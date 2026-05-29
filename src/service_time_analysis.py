# -*- coding: utf-8 -*-
"""
서비스(사이클) 타임 전처리 및 분포 피팅 — 팀원 A (김민섭)
미디어관 엘리베이터 대기 시스템 분석 / OR-2 Term Project

역할
  엘리베이터 출발 타임스탬프 raw 데이터를 가공하여
  큐잉 모델에 투입할 도착률(lambda)·서비스율(mu)·대기상한(K) 상숫값을 산출하고,
  서비스 시간 분포가 Deterministic(D)인지 General(G)인지 검정한다.

파이프라인
  data/raw/elevator_service_timestamps.csv   (호기별 출발 시각)
  data/raw/peak_arrival_counts.csv           (세션별 도착 인원/관측시간/K)
        |
        v 전처리 (호기별 연속 차이 = 사이클 타임)
  data/processed/cycle_times.csv
        |
        v fitter + KS 검정 + 변동계수(Cs^2) 판정
  outputs/service_time_distribution_fit.png
  outputs/cycle_time_spread.png
  outputs/service_time_params.json           (lambda, mu, K, 분포 판정 등)

사용법
  $ python src/service_time_analysis.py            # 저장소 루트에서 실행
  또는 모듈로 import 하여 함수 단위 호출 가능.
"""
from __future__ import annotations
import os
import json
import numpy as np
import pandas as pd
from scipy import stats
from fitter import Fitter

# ---- Batch / 서버 상수 (현장 측정) ----
BATCH_SIZE_B = 17   # 엘리베이터 정원 (1150kg)
SERVERS_S = 3       # 현행 학생용 엘리베이터 대수 (개선안 4)

# ---- 경로: 저장소 루트 기준 자동 탐색 ----
_THIS = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(_THIS)
RAW_DIR = os.path.join(REPO_ROOT, "data", "raw")
PROC_DIR = os.path.join(REPO_ROOT, "data", "processed")
OUT_DIR = os.path.join(REPO_ROOT, "outputs")


# ----------------------------------------------------------------------
# 전처리
# ----------------------------------------------------------------------
def _to_seconds(t: str) -> int:
    h, m, s = (int(x) for x in t.split(":"))
    return h * 3600 + m * 60 + s


def build_cycle_times(timestamps_csv: str | None = None) -> pd.DataFrame:
    """호기별 연속 출발 시각 차이 = 1회 서비스 사이클 타임(분) 데이터셋 생성."""
    path = timestamps_csv or os.path.join(RAW_DIR, "elevator_service_timestamps.csv")
    raw = pd.read_csv(path)
    rows = []
    for (sess, car), g in raw.sort_values(["session", "car", "seq"]).groupby(["session", "car"]):
        secs = [_to_seconds(t) for t in g["door_open_time"]]
        stamps = list(g["door_open_time"])
        for i in range(1, len(secs)):
            d = secs[i] - secs[i - 1]
            rows.append({
                "session": sess, "car": car,
                "from": stamps[i - 1], "to": stamps[i],
                "cycle_sec": d, "cycle_min": round(d / 60.0, 4),
            })
    return pd.DataFrame(rows)


def compute_lambda(counts_csv: str | None = None):
    """세션 통합 도착률 lambda (명/분)."""
    path = counts_csv or os.path.join(RAW_DIR, "peak_arrival_counts.csv")
    c = pd.read_csv(path)
    per_session = {r["session"]: round(r["n_arrivals"] / r["obs_min"], 4)
                   for _, r in c.iterrows()}
    tot_arr = int(c["n_arrivals"].sum())
    tot_min = int(c["obs_min"].sum())
    return tot_arr, tot_min, tot_arr / tot_min, per_session


def compute_K(counts_csv: str | None = None):
    """대기 공간 상한 K = 세션별 최대 대기 인원의 평균 (기획서 정의)."""
    path = counts_csv or os.path.join(RAW_DIR, "peak_arrival_counts.csv")
    c = pd.read_csv(path)
    k_each = {r["session"]: int(r["K_max"]) for _, r in c.iterrows()}
    k_mean = float(c["K_max"].mean())
    return int(round(k_mean)), k_mean, k_each


# ----------------------------------------------------------------------
# 분포 판정
# ----------------------------------------------------------------------
def describe_and_classify(x: np.ndarray):
    """변동계수 제곱(Cs^2)으로 D / M / G 1차 판정."""
    mean = float(np.mean(x))
    std = float(np.std(x, ddof=1))
    cv = std / mean
    cv2 = cv ** 2
    if cv2 < 0.10:
        verdict = "D (Deterministic) 근사 적합 - 분산이 매우 작음"
    elif cv2 < 0.50:
        verdict = "변동이 약한 G - D 가정은 변동 과소추정, M/G 권장"
    else:
        verdict = "G (General) - D 부적합, M/G 모델 사용"
    return {"mean": mean, "std": std, "cv": cv, "cv2": cv2, "verdict": verdict}


def fit_distributions(x: np.ndarray):
    """fitter 적합 + 적합 파라미터에 대한 KS 검정(p-value)."""
    candidates = ["norm", "expon", "gamma", "lognorm", "uniform", "rayleigh", "weibull_min"]
    f = Fitter(x, distributions=candidates, timeout=60)
    f.fit()
    summary = f.summary(Nbest=len(candidates), plot=False)
    rows = []
    for name in candidates:
        params = f.fitted_param[name]
        ks_stat, p = stats.kstest(x, name, args=params)
        rows.append({
            "distribution": name,
            "ks_stat": round(float(ks_stat), 4),
            "p_value": round(float(p), 4),
            "fit_ok": bool(p > 0.05),
            "sse": round(float(summary.loc[name, "sumsquare_error"]), 4),
        })
    ks_df = pd.DataFrame(rows).sort_values("p_value", ascending=False).reset_index(drop=True)
    return f, summary, ks_df


# ----------------------------------------------------------------------
# 시각화
# ----------------------------------------------------------------------
def make_plots(x, f, mean, out_dir=OUT_DIR):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    os.makedirs(out_dir, exist_ok=True)

    plt.figure(figsize=(8, 5))
    try:
        f.plot_pdf(Nbest=3, lw=2)
    except Exception:
        pass
    plt.hist(x, bins=8, density=True, alpha=0.35, color="steelblue", edgecolor="white")
    plt.axvline(mean, color="red", ls="--", lw=1.5, label="Mean E[S]={:.2f} min".format(mean))
    plt.title("Elevator Cycle Time - Histogram & Fitted Distributions")
    plt.xlabel("Cycle time (min)")
    plt.ylabel("Density")
    plt.legend(fontsize=8)
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "service_time_distribution_fit.png"), dpi=130)
    plt.close()

    plt.figure(figsize=(7, 4))
    plt.boxplot(x, vert=False, widths=0.5)
    plt.scatter(x, np.ones_like(x), alpha=0.6, color="darkorange", zorder=3)
    plt.axvline(mean, color="red", ls="--", lw=1.5, label="Mean={:.2f} min (D assumption)".format(mean))
    plt.title("Cycle Time Spread vs Deterministic Mean")
    plt.xlabel("Cycle time (min)")
    plt.yticks([])
    plt.legend(fontsize=8)
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "cycle_time_spread.png"), dpi=130)
    plt.close()


# ----------------------------------------------------------------------
# 엔드투엔드 실행
# ----------------------------------------------------------------------
def run(save: bool = True) -> dict:
    df = build_cycle_times()
    x = df["cycle_min"].to_numpy(dtype=float)
    tot_arr, tot_min, lam, lam_each = compute_lambda()
    K, K_mean, K_each = compute_K()
    desc = describe_and_classify(x)
    mu = 1.0 / desc["mean"]
    f, summary, ks_df = fit_distributions(x)
    best = ks_df.iloc[0]

    params = {
        "N_cycles": int(len(x)),
        "lambda_per_min": round(lam, 4),
        "lambda_per_hour": round(lam * 60, 2),
        "lambda_per_session": lam_each,
        "E_S_min": round(desc["mean"], 4),
        "std_min": round(desc["std"], 4),
        "CV": round(desc["cv"], 4),
        "CV2": round(desc["cv2"], 4),
        "service_dist_verdict": desc["verdict"],
        "mu_per_min_per_car": round(mu, 4),
        "best_fit_distribution": str(best["distribution"]),
        "best_fit_p_value": float(best["p_value"]),
        "K_capacity": K,
        "K_mean_raw": round(K_mean, 2),
        "K_per_session": K_each,
        "batch_size_B": BATCH_SIZE_B,
        "servers_s": SERVERS_S,
        "system_capacity_per_min": round(SERVERS_S * BATCH_SIZE_B * mu, 4),
        "rho": round(lam / (SERVERS_S * BATCH_SIZE_B * mu), 4),
        "ks_table": ks_df.to_dict(orient="records"),
    }

    if save:
        os.makedirs(PROC_DIR, exist_ok=True)
        os.makedirs(OUT_DIR, exist_ok=True)
        df.to_csv(os.path.join(PROC_DIR, "cycle_times.csv"), index=False, encoding="utf-8-sig")
        make_plots(x, f, desc["mean"])
        with open(os.path.join(OUT_DIR, "service_time_params.json"), "w", encoding="utf-8") as fp:
            json.dump(params, fp, ensure_ascii=False, indent=2)

    return params


def _print_report(p: dict):
    print("=" * 60)
    print("  서비스 타임 분석 - 최종 모델 입력 상숫값")
    print("=" * 60)
    print("  사이클 관측치 N      = {}".format(p["N_cycles"]))
    print("  도착률 lambda        = {} 명/분 ({} 명/시간)".format(p["lambda_per_min"], p["lambda_per_hour"]))
    print("  평균 사이클 E[S]     = {} 분".format(p["E_S_min"]))
    print("  서비스율 mu = 1/E[S] = {} cycles/분 (호기 1대)".format(p["mu_per_min_per_car"]))
    print("  변동계수 CV^2        = {}".format(p["CV2"]))
    print("  분포 판정            = {}".format(p["service_dist_verdict"]))
    print("  최적 적합 분포       = {} (KS p={})".format(p["best_fit_distribution"], p["best_fit_p_value"]))
    print("  대기 공간 상한 K     = {} (세션별 {} 평균={})".format(p["K_capacity"], p["K_per_session"], p["K_mean_raw"]))
    print("  처리능력 s*B*mu      = {} 명/분 (s={}, B={})".format(p["system_capacity_per_min"], p["servers_s"], p["batch_size_B"]))
    print("  이용률 rho           = {}".format(p["rho"]))
    print("=" * 60)


if __name__ == "__main__":
    _print_report(run(save=True))
    print("저장: data/processed/cycle_times.csv, outputs/service_time_params.json,")
    print("       outputs/service_time_distribution_fit.png, outputs/cycle_time_spread.png")
