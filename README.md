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

\---

## 레포지토리 구조

```
.
├── README.md                              # 본 문서
├── requirements.txt                       # Python 패키지 의존성
├── .gitignore
│
├── data/
│   └── survey\\\_responses.csv               # 설문조사 raw 데이터 (n=34)
│
├── notebooks/
│   └── elevator\\\_balking\\\_analysis.ipynb    # 팀원 B (채윤) - 설문 분석 노트북
│
└── outputs/
    ├── survey\\\_params.json                 # 후속 분석용 파라미터 (자동 생성)
    ├── balking\\\_curve\\\_analysis.png         # Balking 모델 적합 그래프
    └── survey\\\_distributions.png           # T, X 분포 시각화
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

