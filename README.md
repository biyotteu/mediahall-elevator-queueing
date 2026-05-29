# 미디어관 엘리베이터 대기 시스템 분석

> OR-2 Term Project | Analysis of M/D/1/K Queueing System with Batch Service
> Batch Service 모델링과 Balking 분석을 통한 최적 운영 대수 산정 및 경제성 검토

\---

### 핵심 인사이트

|항목|값|의미|
|-|-|-|
|이탈 감쇠 상수 `bk`|**0.9807**|대기열이 1명 증가 시 잔류 확률 약 1.93% 감소|
|마지노선 시간 `T`|**5.49분**|학생 평균 인내 대기 시간|
|불만족도 `X`|**4.06점** (5점 만점)|피크 타임 시간 압박|
|고층 이용자 이탈안함 비율|**87.5%**|6층 이하 (20%) 대비 압도적|
|도착률 `λ`|**4.356명/분**|피크 1층 상행 도착률 (세션 통합, 사이클 N=42)|
|서비스율 `μ`|**0.239 cycles/분**|호기 1대 처리율 (E[S]=4.18분), 서비스 분포 G(감마)|
|대기 상한 `K`|**14명**|세션별 최대 대기(10·12·21) 평균|

\---

## 레포지토리 구조

```
.
├── README.md                                  # 본 문서
├── requirements.txt                           # Python 패키지 의존성
├── .gitignore
│
├── data/
│   ├── raw/
│   │   ├── elevator_service_timestamps.csv    # 팀원 A - 호기별 출발 시각
│   │   └── peak_arrival_counts.csv            # 팀원 A - 세션별 도착인원/관측/K
│   ├── processed/
│   │   └── cycle_times.csv                     # 팀원 A - 사이클 타임 N=42 (자동 생성)
│   └── survey_responses.csv                    # 팀원 B - 설문 raw (n=34)
│
├── notebooks/
│   ├── elevator_service_time_analysis.ipynb   # 팀원 A (민섭) - 서비스타임 전처리·분포 피팅
│   └── elevator_balking_analysis.ipynb        # 팀원 B (채윤) - 설문 분석
│
├── src/
│   └── service_time_analysis.py               # 팀원 A - 전처리+피팅 모듈 (CLI)
│
├── docs/
│   └── service_time_analysis.md               # 팀원 A - 서비스타임 분석 문서
│
└── outputs/
    ├── service_time_params.json               # 팀원 A - λ,μ,K,분포 (자동 생성)
    ├── service_time_distribution_fit.png      # 팀원 A
    ├── cycle_time_spread.png                  # 팀원 A
    ├── survey_params.json                     # 팀원 B - bk,T,X (자동 생성)
    ├── balking_curve_analysis.png             # 팀원 B
    └── survey_distributions.png               # 팀원 B
```

\---



## 시작하기

### 1\. 환경 설정

```bash
git clone https://github.com/<your-id>/elevator-queueing-analysis.git
cd elevator-queueing-analysis
pip install -r requirements.txt
```

### 2\. 노트북 실행

```bash
jupyter notebook notebooks/elevator\\\_balking\\\_analysis.ipynb
```

또는 Google Colab 에서 바로 열기 - `notebooks/elevator\\\_balking\\\_analysis.ipynb` 를 Colab 에 업로드한 뒤, `data/survey\\\_responses.csv` 도 같이 업로드해서 실행하면 됩니다.

### 3\. 결과 확인

노트북을 끝까지 실행하면 `outputs/` 폴더에 다음 파일들이 자동 생성됩니다:

* `survey\\\_params.json` — 분석을 통해 도출한 파라미터 값으로, 코드에 직접 import 가능
* `balking\\\_curve\\\_analysis.png` — 발표자료 첨부용
* `survey\\\_distributions.png` — 발표자료 첨부용

\---

## 주요 분석 결과 (요약)

### Balking Model 적합도

지수 감쇠 모델 P(stay) = bk^n 을 사용하여 설문 응답에 적합한 결과:

```
bk = 0.9807 (±0.0043)
R² = 0.8053
RMSE = 0.0563
```

### 학생 특성별 차이

|그룹|n|T 평균|X 평균|이탈 안함 비율|
|-|-|-|-|-|
|6층 이하 이용자|10|3.60분|3.90점|20.0%|
|7층 이상 이용자|24|6.27분|4.13점|87.5%|

→ 고층 이용자는 계단 대체 비용이 높아 balking 확률이 낮음. 후속 시뮬레이션에서 이질적 고객 모델 적용 검토 가능.

### T-X 상관관계

Pearson 상관계수 `r = 0.347` (p = 0.045) → 인내 대기 시간이 긴 학생일수록 불만족도가 높음. 직관과 반대되는 결과로, "긴 시간 기다릴 의향" = "수업 중요도 높음" → 압박감 증가라는 해석 가능.

\---

## 서비스 타임 분석 (팀원 A · 민섭)

피크 시간대 엘리베이터 출발 타임스탬프(3세션 통합, 사이클 N=42)를 전처리·분포 피팅하여 도착률·서비스율을 도출했다. 상세 문서는 `docs/service_time_analysis.md`, 노트북은 `notebooks/elevator_service_time_analysis.ipynb`.

### 모델 입력값

|기호|값|의미|
|-|-|-|
|λ|4.356 명/분 (261.3/h)|피크 1층 상행 도착률|
|μ|0.239 cycles/분|호기 1대 처리율 (= 1/E[S])|
|E[S]|4.184 분|평균 왕복 사이클 시간|
|K|14|1층 대기 공간 상한 (세션 최대 10·12·21 평균)|
|B|17|엘리베이터 정원 (1150kg)|
|서비스 분포|G (gamma)|Cs²=0.166, KS p≈0.99|
|ρ|0.357|이용률 λ/(sBμ), s=3|

### 분포 판정 (D vs G)

사이클 타임이 1.87~9.33분으로 약 5배 퍼져 있고 Cs²=0.166이라 결정론적(D)으로 볼 수 없다. fitter + KS 검정에서 gamma(p=0.988)·weibull_min(0.986)이 최적이고 uniform만 기각되었다. 따라서 M/D가 아닌 **M/G/s/K (batch)** 로 모델링해야 대기시간(Wq) 과소추정을 피한다.

### 데이터 인사이트

도착률은 시간대가 늦을수록 증가한다(세션별 3.40 → 4.67 → 5.00명/분). 평균 이용률 ρ=0.357로 낮지만, 배치 출발과 도착 burst 때문에 순간 대기열은 K=21까지 치솟으며 오후 피크(S3)가 오전의 약 2배로 가장 혼잡하다.

```python
import json
svc = json.load(open("outputs/service_time_params.json"))
lam = svc["lambda_per_min"]      # 4.3556
mu  = svc["mu_per_min_per_car"]  # 0.239
K   = svc["K_capacity"]          # 14
```

(그래프: `outputs/service_time_distribution_fit.png`, `outputs/cycle_time_spread.png`)

\---

## 후속 단계

큐잉 모델 코드에서 본 노트북 결과를 다음과 같이 사용하시면 됩니다:

```python
import json

with open("outputs/survey\\\_params.json", "r") as f:
    params = json.load(f)

bk = params\\\["bk"]                  # 0.9807
T\\\_threshold = params\\\["T\\\_avg\\\_min"]  # 5.49 → P{Wq <= 5.49분} 계산
X\\\_dissatisfaction = params\\\["X\\\_avg\\\_score"]  # 4.06 → Loss of Goodwill 환산
```

\---

