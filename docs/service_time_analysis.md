# 서비스 타임 전처리 및 분포 피팅

피크 시간대 엘리베이터 출발 타임스탬프를 가공해 큐잉 모델 입력값(도착률 λ, 서비스율 μ, 대기 상한 K)을 산출하고, 서비스 시간 분포가 결정론적(D)인지 일반분포(G)인지 검정한 결과를 정리

관련 파일: 코드 `src/service_time_analysis.py`, 노트북 `notebooks/elevator_service_time_analysis.ipynb`, 결과 `outputs/service_time_params.json`.

---

## 1. 데이터

| 파일 | 내용 | 비고 |
|---|---|---|
| `data/raw/elevator_service_timestamps.csv` | 호기별 출발(문 열림) 시각 | 3세션, 호기 1~3, 총 51개 시각 |
| `data/raw/peak_arrival_counts.csv` | 세션별 도착 인원·관측시간·최대 대기 K | 3세션 |
| `data/processed/cycle_times.csv` | 사이클 타임 N=42 (자동 생성) | 분포 피팅 입력 |

측정 세션은 S1 05/20 오후(13:15~13:30), S2 05/21 오전(08:45~09:00), S3 05/21 오후(14:45~15:00)다.
피크 시간대 1층 상행 수요는 요일·교시와 무관하게 동일한 구조적 조건에서 반복되므로, 세 세션을 단일 프로세스의 독립 관측치로 통합한다.

---

## 2. 분석 방법

서비스 사이클 타임은 같은 호기의 연속 출발 시각 차이로 정의한다 (예: 14:42:20~14:48:45 → 6.41분).

- 도착률 λ = 총 도착 인원 / 총 관측 시간 (세션 통합)
- 서비스율 μ = 1 / E[S] (호기 1대 기준)
- 대기 상한 K = 세션별 최대 대기 인원의 평균
- 분포 판정: 변동계수 제곱 Cs² = Var(S)/E[S]² 로 1차 분류(D≈0, M≈1, G=그 외) 후 `fitter` + KS 검정으로 최적 분포 확정

---

## 3. 결과 — 모델 입력값

| 기호 | 값 | 의미 |
|---|---|---|
| λ | 4.356 명/분 (261.3/h) | 피크 1층 상행 도착률 |
| μ | 0.239 cycles/분 | 호기 1대 1사이클 처리율 (= 1/E[S]) |
| E[S] | 4.184 분 | 평균 왕복 사이클 시간 |
| K | 14 | 1층 대기 공간 상한 (세션 최대 10·12·21의 평균) |
| B | 17 | 엘리베이터 정원 (1150kg, Full-batch 가정) |
| 서비스 분포 | G (gamma) | Cs²=0.166, KS p≈0.99 |
| ρ | 0.357 | 시스템 이용률 λ/(sBμ), s=3 |

```python
import json
svc = json.load(open("outputs/service_time_params.json"))
lam = svc["lambda_per_min"]      # 4.3556
mu  = svc["mu_per_min_per_car"]  # 0.239
K   = svc["K_capacity"]          # 14
B   = svc["batch_size_B"]        # 17
```

---

## 4. 데이터에서 얻은 인사이트

1. 서비스 시간은 결정론적(D)이 아니라 일반분포(G)다. 사이클 타임이 1.87~9.33분으로 약 5배 퍼져 있고 Cs²=0.166이라 상수로 볼 수 없다. `fitter`+KS에서 gamma(p=0.988)·weibull_min(0.986)이 최적, uniform만 기각. 따라서 M/D가 아닌 M/G/s/K(batch)로 모델링해야 대기시간 과소추정을 피한다.
2. 도착률은 시간대가 늦을수록 증가한다(세션별 3.40 → 4.67 → 5.00명/분). 통합 λ=4.356, 처리능력 s·B·μ=12.19명/분으로 평균 이용률 ρ=0.357이지만, 배치 출발과 도착 burst 때문에 순간 대기열은 K=21까지 치솟는다.
3. 대기열 혼잡은 오후 피크에서 폭발한다. 세션별 최대 대기 10/12/21명으로 S3가 오전의 약 2배. K=14를 기본값으로 두되 최악값(21)에 대한 민감도 분석을 함께 둔다.

(그래프: `outputs/service_time_distribution_fit.png`, `outputs/cycle_time_spread.png`)

---

## 5. 재현 방법

```bash
pip install -r requirements.txt
python src/service_time_analysis.py
# 또는: jupyter notebook notebooks/elevator_service_time_analysis.ipynb
```

실행하면 `data/processed/cycle_times.csv`, `outputs/service_time_params.json`, 그래프 2장이 생성된다.

---

## 6. 다음 단계 (큐잉 모델 풀이)

위 λ·μ·K·B와 설문 분석의 이탈 상수 bk(`outputs/survey_params.json`)를 입력으로 M/G/s/K in batch units 균형방정식을 세워, 정상상태 확률과 평균 대기시간 Wq를 구하고 현행 s=3과 직원용 추가 개방 s=4를 비교한다. 상태의존 도착률은 λ_i = λ · bk^(i-c) 형태로 반영한다.
