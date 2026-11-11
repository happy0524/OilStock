# 실행과 재현

Windows PowerShell, Python 3.10에서 실행했습니다. 저장소 루트에서 아래 순서로 실행합니다. Linux/macOS에서는 `.venv/Scripts/python` 대신 `.venv/bin/python`을 사용합니다.

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python scripts/verify_companies.py
.\.venv\Scripts\python scripts/run_analysis.py
.\.venv\Scripts\python -m pytest -q
.\.venv\Scripts\python scripts/execute_notebook.py
```

`verify_companies.py`는 현재 KIND 목록을 대조하며 제공 표본을 새 목록으로 교체하지 않습니다. 세기상사는 제공 이름을 보존하고 현재 코드·시장·이름 차이를 별도로 기록합니다. 유성티엔에스는 공식 목록에서 확인한 024800.KQ를 사용합니다.

시세 수집은 기존 캐시를 우선 사용합니다. 캐시는 티커·기간·자동조정 정책을 포함한 키와 SHA-256으로 검증합니다. 실패·빈 티커도 상태로 저장되므로 재시도할 때는 `--refresh`를 사용합니다. `--offline`은 네트워크 없이 원자료 캐시만 사용합니다. 두 옵션은 동시에 사용할 수 없습니다.

```powershell
.\.venv\Scripts\python scripts/run_analysis.py --refresh
.\.venv\Scripts\python scripts/run_analysis.py --offline
```

실행 상태가 `partial`이면 가능한 표와 그림·미생성 사유를 보고서에 남기고 종료 코드 2를 반환합니다. 없는 자료를 샘플 가격으로 대체하지 않습니다. 정확한 비교일 결측은 `missing_exact_date`로 남깁니다. `--offline`에서 캐시가 없는 경우에도 같은 방식으로 명시합니다. 배포 시 원자료는 포함하지 않으므로 새 환경의 최초 실행에는 네트워크가 필요합니다.

일별 표의 빈 칸은 해당 티커의 관측 부재를 의미합니다. 휴장일을 다른 시장의 값으로 채우지 않습니다. 선물은 두 티커 모두 존재하는 날짜만 그래프에 사용합니다. 실제 거래소 달력의 모든 중간 거래일을 일괄 인증하는 파이프라인은 아닙니다.

`configs/analysis.json`에 제공된 네 기간 버전을 분리했습니다. 유가 장기는 3/31, 단기는 3/13, 일별 주가는 4/1이 이번 실제 마지막 관측일이었습니다. 세 시점 수집의 마지막 관측일은 3/13이지만 표·그림은 2/27·3/2·3/10만 선택했습니다. 기업별 범위는 수집 기록에서 확인합니다. 일별 첫 관측일 기준은 이번 실행에서 2/2이며, 사건 반응의 2/27과 다릅니다.

주가는 `auto_adjust=False`의 Close, 유가는 `True`로 고정했습니다. 과거 주가 코드에서 지정하지 않은 자동조정 옵션·버전과 달라질 수 있습니다. 배당 재투자 총수익률로 해석하지 않습니다. 선물 티커는 제공처의 연결·롤 정책에 영향을 받으며 현물이나 고정 월물 투자수익률로 해석하지 않습니다.

폰트는 Malgun Gothic → AppleGothic → NanumGothic → Noto Sans CJK KR 순서로 선택합니다. 없으면 경고 후 영문 라벨을 사용합니다. 운영체제 폰트를 별도로 설치하는 명령은 실행하지 않습니다.

노트북은 `run_analysis.py`로 생성한 CSV와 그림을 위에서 아래로 읽습니다. 노트북 실행 스크립트는 현재 Python 환경을 커널로 사용하며 전 셀의 실행 번호·오류 부재를 검사합니다. 원자료 재수집이 필요한 분석 로직은 공통 모듈에 두고 중복하지 않았습니다.

선택적인 초기 후보 스냅샷은 다음 명령으로 수집합니다. 현재 후보를 사건 당시 구성이나 21개 고정 표본으로 덮어쓰지 않습니다. 시총은 요청 시점 값으로만 기록하고 분석 표본 컷오프에 사용하지 않습니다. 한국 KIND 목록에는 시총이 없어 미제공으로 남깁니다.

```powershell
.\.venv\Scripts\python scripts/collect_candidates.py
.\.venv\Scripts\python scripts/collect_candidates.py --refresh --market-caps
```

GitHub 업로드는 수행하지 않았습니다. 사용자가 저장소를 만든 뒤 루트에서 실행할 최소 명령은 다음과 같습니다. `<본인 저장소 URL>`은 실제 주소로 바꿉니다.

```powershell
git init
git add README.md requirements.txt .gitignore configs src scripts tests notebooks docs reports data/reference data/processed
git commit -m "Add war and oil exploratory analysis portfolio"
git branch -M main
git remote add origin <본인 저장소 URL>
git push -u origin main
```

매출 원문 출처·이용 조건, 원 수업 프로젝트의 팀 구성과 개인 기여 범위는 공개 전 확인할 항목입니다. 코드 테스트 통과는 경제적 가설의 통계 검증과 구별합니다.
