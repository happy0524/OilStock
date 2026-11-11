"""Generate narrative outputs only from the current run's actual observations."""
import pandas as pd


def table(frame):
    def fmt(v):
        if pd.isna(v):
            return '미확인'
        if isinstance(v, float):
            return f'{v:.2f}'
        return str(v).replace('|', '/').replace('\n',' ')
    lines = ['| ' + ' | '.join(map(str, frame.columns)) + ' |', '| ' + ' | '.join(['---'] * len(frame.columns)) + ' |']
    return '\n'.join(lines + ['| ' + ' | '.join(fmt(v) for v in row) + ' |' for row in frame.itertuples(index=False, name=None)])


def write_reports(root, cfg, companies, revenue, quality, audit, reactions, frames, run):
    def value(ticker):
        row = reactions.set_index('ticker').loc[ticker]
        return f'{row.return_pct:+.2f}%' if pd.notna(row.return_pct) else '기준일 자료 미확인'

    summaries = []
    for country in ['US','KR']:
        group = reactions[(reactions.country == country) & reactions.include_main]
        valid = group.dropna(subset=['return_pct'])
        summaries.append(f"{country} 주 비교 표본 {len(group)}개 중 {len(valid)}개를 계산했고, 상승 {(valid.return_pct > 0).sum()}개·하락 {(valid.return_pct < 0).sum()}개·보합 {(valid.return_pct == 0).sum()}개를 확인했습니다.")
    summary = ' '.join(summaries)
    periods = audit.groupby('window', sort=False).agg(requested_start=('requested_start','first'),
                 end_exclusive=('end_exclusive','first'), actual_first_date=('actual_first_date','min'),
                 actual_last_date=('actual_last_date','max'), ticker_count=('ticker','size')).reset_index()
    # Range summaries do not replace per-ticker availability in the full manifest.
    snapshots = reactions[reactions.ticker.isin(['XOM','010950.KS','267250.KS','TPL'])][
        ['ticker','company','baseline_date','reaction_date','return_pct','status']]
    oil_results = pd.read_csv(root / 'data/processed/oil_event_reactions.csv')
    services = reactions[reactions.ticker.isin(['SLB','BKR','HAL'])]
    service_note = ('첫 거래일에는 미국 장비·서비스 3개사(SLB·BKR·HAL)가 모두 소폭 하락했습니다.'
                    if len(services) == 3 and services.return_pct.notna().all() and (services.return_pct < 0).all()
                    else '미국 장비·서비스의 첫 거래일 결과는 개별 관측표에 기록했고, 자료가 없는 경우 해석을 보류했습니다.')
    industry_note = ('분석 기간의 통합 석유·가스와 정제·판매에서는 유사한 흐름을 시각적으로 관찰했고, 탐사·생산과 저장·운송에서는 개별 기업의 차이도 확인했습니다.'
                     if run['status'] == 'complete' else '주가 자료가 불완전해 세부 업종 간 경로의 일반적 해석을 보류했습니다.')
    links = {f['file']:f for f in run['figures']}
    def figure(name, alt, prefix=''):
        if links[name]['generated']:
            return f'![{alt}]({prefix}reports/figures/{name})'
        return f"그림 미생성: {alt}. 이유: {links[name]['reason']}."

    readme = f'''# War & Oil Stock Price

**전쟁 전후 한·미 석유 관련 기업의 주가 반응과 사업 구조 탐색**

같은 ‘석유 관련 기업’이라도 주가는 비슷하게 움직였을까요? 이 프로젝트는 원유 선물과 한·미 기업의 주가를 비교하고, 예상과 다른 사례를 계기로 기업의 실제 사업 구성까지 질문을 확장한 탐색적 분석을 재구성했습니다. 제공된 과거 관찰 기록과 이번에 새로 수집·계산한 결과를 구분했습니다.

> **핵심 질문** — 사건 이후 국가·기업·세부 업종별 주가 반응은 어떻게 달랐으며, 사업 구성은 그 차이를 이해하는 데 어떤 단서를 주었을까요?

사건 기준은 **2026-02-28** 미국·이스라엘의 이란 공격 개시로 설정했습니다. [Reuters 보도](https://au.investing.com/news/israel-and-us-launch-strikes-on-iran-targeting-its-leadership-4285236?ampMode=1)와 대조했습니다. 한국은 [삼일절 대체휴일 휴장](https://www.samsungpop.com/common.do?cmd=down&contentType=application%2Fpdf&fileName=4010%2F2026022717364620K_02_01.pdf&inlineYn=Y&saveKey=research.pdf)을 고려해 3/3, 미국은 3/2 종가를 2/27과 비교했습니다.

{figure('oil_windows.png','Brent·WTI 선물 장기·단기 추이')}

{figure('event_reactions.png','2월 27일 종가 대비 국가별 첫 거래일 기업 주가 변동률')}

**이번 실행 결과:** {summary} 엑슨모빌은 **{value('XOM')}**, S-Oil은 **{value('010950.KS')}**, HD현대는 **{value('267250.KS')}**를 기록했습니다. 이는 국가 전체 증시의 수익률이나 전쟁의 인과 효과가 아닌, 정해진 표본의 종가 변화입니다.

### 예상 밖 사례가 바꾼 질문

초기 동기는 “전쟁 뒤 석유 관련 주가가 오를 것”이라는 기대였습니다. 엑슨모빌과 S-Oil에서 출발해 미국 21개·한국 13개 기업으로 범위를 넓혔고, 절대가격 비교에서 기준일 대비 변동률 비교로 발전했습니다. 이 과정은 사용자가 설명한 과거 탐색을 바탕으로 정리했습니다.

사용자는 HD현대의 예상과 다른 하락과 이후 변동을 보고 사업 구성을 조사했다고 설명했습니다. 제공된 매출 입력에서는 **조선해양 41.8%·정유 38.5%**로, 조선해양이 가장 큰 항목이었습니다. 이 사례를 통해 업종 이름과 함께 실제 사업 구성을 살펴볼 필요가 있다는 질문으로 발전했습니다. 조선해양 매출이 하락을 일으켰다는 결론은 내리지 않았습니다.

{figure('hd_hyundai_case.png','HD현대 원래 매출 비중과 주가 사례 비교')}

TPL은 토지·로열티·물 관련 사업 모델의 비교 가능성을 이유로 **EDA 이후 주 비교에서 제외**했습니다. 초기 21개 표와 상세 그림에는 남겼고, 제외 전후 요약도 함께 저장했습니다. [공식 10-K](https://www.sec.gov/Archives/edgar/data/1811074/000181107426000018/tpl-20251231.htm)에서 석유·가스 로열티와 물 관련 수익을 확인했으므로 석유와 무관한 기업으로 분류하지 않았습니다.

{figure('us_industries.png','미국 세부 업종별 기업의 2월 27일 기준 변동률')}

### 데이터와 해석 범위

| 자료 | 범위와 표본 | 출처·주의점 |
|---|---|---|
| 원유 선물 | Brent BZ=F, WTI CL=F; 장기 2/1–4/1 미포함, 단기 2/24–3/16 미포함 | Yahoo Finance, 현물 아님 |
| 미국 주가 | 초기 21개, TPL 제외 주 비교 20개; 일별 2/1–4/2 미포함 | 제공된 고정 목록; 당시 S&P 500 구성 검증 아님 |
| 한국 주가 | 제공된 13개: KOSPI 8개·KOSDAQ 5개; 미국 일별과 같은 요청 기간 | KIND 현재 코드·시장 대조; 수집 코드는 이번 추가 |
| 매출 구성 | 미국 18개·한국 13개, 원 입력 104행 | 사용자 전사: FnGuide·IR 기반; 다수 기준일·회계 기준·원문 링크 미제공 |

S-Oil의 제공 매출 합계는 80.1%이고, GS에는 음수 항목이 있으며, 일부 미국 기업은 100%를 초과했습니다. 이를 보존했고 정규화·누락분 추정·다각화 지수 계산을 하지 않았습니다. 한국의 에너지/화학·E&S·유통·휴게소는 검증된 석유 비중으로 간주하지 않았습니다.

{service_note} {industry_note} 단일 사건·제한된 표본의 탐색이며 시장 수익률, 국가별 경과 시간, 기업 특성을 통제하지 않았습니다. 통계 검정·ML·인과 추론은 수행하지 않았습니다. 원 수업 프로젝트의 팀 구성과 개인 기여는 확인이 필요합니다.

### 직접 확인하고 재현하기

```powershell
python -m venv .venv
.\\.venv\\Scripts\\python -m pip install -r requirements.txt
.\\.venv\\Scripts\\python scripts/run_analysis.py
.\\.venv\\Scripts\\python -m pytest -q
```

기존 캐시를 우선 사용하며 `--refresh`로 재수집하고 `--offline`으로 캐시만 사용합니다. 이번 실행 상태는 **{run['status']}**이며, 수집 시각·버전·요청/관측 범위는 [수집 기록](data/processed/acquisition_manifest.csv)에 남겼습니다.

[분석 보고서](reports/analysis.md) · [품질 보고서](reports/data_quality.md) · [순서대로 실행한 노트북](notebooks/01_exploration.ipynb) · [출처](docs/sources.md) · [재현 방법](docs/reproduction.md) · [표본 결정](data/reference/sample_decisions.csv)
'''
    (root / 'README.md').write_text(readme, encoding='utf-8')
    report = f'''# 분석 보고서

## 1. 문제 정의와 질문 발전

“전쟁 이후 석유 관련 기업의 주가가 오를 것”이라는 기대를 출발점으로 정리했습니다. 수요 급증이나 주가 상승의 인과관계가 확인된 명제로 사용하지 않았습니다. 엑슨모빌·S-Oil에서 국가·세부 업종 비교로 확장한 뒤 HD현대·TPL 사례를 통해 사업 구성의 설명 가능성을 살펴보는 흐름을 재구성했습니다. 과거 탐색 순서는 사용자 설명으로, 아래 수치는 이번 재수집으로 구분했습니다.

## 2. 수집·기간·표본 선정

사건일은 2/28로 설정하고 [Reuters](https://au.investing.com/news/israel-and-us-launch-strikes-on-iran-targeting-its-leadership-4285236?ampMode=1)의 미국·이스라엘 공격 개시 보도와 대조했습니다. 3/2 한국 휴장은 [삼성증권 일정](https://www.samsungpop.com/common.do?cmd=down&contentType=application%2Fpdf&fileName=4010%2F2026022717364620K_02_01.pdf&inlineYn=Y&saveKey=research.pdf)으로 확인했으며 KRX 원문 웹 열람은 403으로 제한됐습니다. 미국 3/2·한국 3/3의 정확한 종가를 비교했습니다.

미국 초기 고정 21개, 주 비교 20개, 매출 입력 18개를 구별했습니다. COP·APA의 매출 자료 부재 이유는 미제공으로 남겼습니다. 한국은 초기 KOSPI 키워드 후보 수집과 후속 토스증권 검색 기반 제공 13개 목록을 구별했습니다. 전수조사나 임의 시총 컷오프를 전제하지 않았습니다. 현재 후보·시총 수집은 선택 스크립트로 분리하고 사건 당시 구성이나 규모 분석으로 사용하지 않았습니다.

{table(periods)}

위 표는 기업별 범위의 최소·최대 요약으로 작성했습니다. 세부 관측일·결측·실패 상태는 [수집 기록](../data/processed/acquisition_manifest.csv)에 기업별로 기록했습니다. 3/16은 단기 범위의 배타적 종료일로 처리했습니다.

## 3. 전처리와 새 품질 검증

시장 현지 날짜를 정규화하고 날짜 중복·비양수 종가를 검사했습니다. 유가는 Brent·WTI가 모두 있는 행만 유지하고 제외 행 수를 별도 표에 남겼습니다. 한국 휴장일을 미국 값으로 채우지 않았고 모든 결측은 그대로 유지했습니다. 기준일이 없는 기업에는 수익률 대신 결측 상태를 남겼습니다. 매출은 원문 항목과 수치를 보존하고 명시 항목·복합 항목·확인 필요를 구분했습니다. 이러한 코드·품질 검증은 이번 재현에 추가했으며 과거에 수행한 검증으로 서술하지 않았습니다.

## 4. EDA와 가설 형성

사용자는 HD현대의 하락과 변동을 보고 조선해양·정유 사업 구성을 조사했다고 설명했습니다. 제공값에서 조선해양 41.8%, 정유 38.5%를 확인했습니다. 한화오션에 대한 관심은 과거 문제의식의 맥락으로만 다루고 별도 비교 표본에 추가하지 않았습니다. HD현대 기타 0.38%는 미제공 캡처에 관한 사용자 전사 설명으로만 기록했으며 원 입력 99.6%에 추가하지 않았습니다.

TPL은 EDA 이후 사업 모델 비교 가능성을 기준으로 주 비교에서 제외했습니다. [2025 10-K](https://www.sec.gov/Archives/edgar/data/1811074/000181107426000018/tpl-20251231.htm)에서 토지·자원 관리 및 물 관련 사업, 에너지 로열티 수익원을 확인했습니다. 상이한 주가 흐름 자체를 제외 근거로 삼지 않았으며 지역·항로 원인은 검증하지 않았습니다. 사후 제외의 선택 편향을 한계에 포함했습니다.

## 5. 분석 설계와 피처 생성

변동률은 `(해당일 Close / 기준일 Close - 1) × 100`으로 계산했습니다. 주가는 `auto_adjust=False`의 Close로, 선물은 제공 코드와 같은 `True`로 고정했습니다. 주가 Close도 분할 조정 등 제공처 정책의 영향을 받을 수 있어 총수익률로 해석하지 않았습니다. 과거 주가 코드의 자동 조정 기본값과 버전이 미확정이므로 이전 결과와 완전히 동일하다고 주장하지 않았습니다.

일별 장기 분석은 각 시장 자료의 첫 관측 행을 공통 기준으로 삼았고, 사건 반응은 2/27을 별도 기준으로 사용했습니다. 실제 첫 관측일은 [기준일 표](../data/processed/daily_baselines.csv)에 기록했습니다. 별도 ML 모델과 다각화 지수를 만들지 않았습니다.

## 6. 평가와 검증

기준일·날짜·표본 매칭을 코드 수준에서 검증하고 그래프를 탐색적으로 비교했습니다. 테스트 통과는 공식과 결측 처리의 구현 검증으로 제한했습니다. 통계 가설검정·외부 사건 재검증·시장 대비 초과수익 분석은 수행하지 않았습니다. 산업 요약은 동일 기업 가중의 기술 통계로만 계산했습니다.

## 7. 실제 발견과 해석

{summary}

{table(snapshots)}

엑슨모빌 {value('XOM')}, S-Oil {value('010950.KS')}, HD현대 {value('267250.KS')}를 이번 실행에서 확인했습니다. TPL의 초기 표본 반응 {value('TPL')}도 보존했습니다. 첫 세션 결과만으로 이후 모든 거래일이나 모든 기업에서 초기 기대가 성립했다고 일반화하지 않았습니다. 사업 구성은 주가 차이를 이해하는 탐색적 단서로 제시했으며 업종보다 더 큰 영향력을 입증했다고 결론 내리지 않았습니다.

![유가](figures/oil_windows.png)

아래 표에서 선물의 2/27 대비 3/2 종가 변화를 계산했습니다. 장기·단기 경로에서 상승과 중간 반락을 함께 관찰했으며 지속적인 단조 상승으로 설명하지 않았습니다. 시계열은 연결 선물로 취급했고 개별 고정 월물의 보유 수익으로 해석하지 않았습니다.

{table(oil_results)}

![첫 거래일 반응](figures/event_reactions.png)

![세부 산업](figures/us_industries.png)

세부 업종 그림에서는 동행과 이탈을 함께 비교하도록 동일한 y축을 적용했습니다. {industry_note} 장비·서비스는 SLB·BKR·HAL로 구분했고 첫 세션 변동률은 각각 {value('SLB')}·{value('BKR')}·{value('HAL')}로 계산했습니다. 업종 라벨만으로 전체 기간의 경로 일치를 전제하지 않았으며 색 자체에 산업적 의미를 부여하지 않았습니다. 수치 요약은 [업종별 첫 세션 표](../data/processed/us_industry_first_session_summary.csv)로 제공했습니다.

![HD현대 사례](figures/hd_hyundai_case.png)

사업 구성 그림은 회사별 원 비중을 사용했습니다. 기업별 pct/N을 합산하고 파이가 다시 정규화했던 이전 방식은 국가 전체 매출 비중으로 해석할 수 없어 대표 그림에서 사용하지 않았습니다. 불완전한 S-Oil과 합계 초과 미국 입력을 바탕으로 국가 간 석유 비중 또는 다각화 효과를 수치화하지 않았습니다.

## 8. 한계와 후속 과제

단일 사건·제한된 표본, 국가별 첫 거래일까지의 시간 차이, 시장·기업 특성 미통제, 매출 기준일·정의 차이와 누락을 한계로 기록했습니다. 사후 가설 형성과 TPL 제외에 따른 선택 편향을 인정하고 [제외 전후 표](../data/processed/tpl_sample_sensitivity.csv)를 함께 제공했습니다. 규모와 지역은 설명 후보였으나 현재 자료로 검증을 완료하지 않았습니다. 이후 시장 대비 초과수익률, 다른 사건과 기간, 사전 가설, 회귀 및 불확실성 검토를 후속 과제로 제안했습니다. 팀 구성과 개인 기여는 확인이 필요한 항목으로 남겼습니다.

## 부록: 초기 21개 보존

첫 관측일 기준 변동률에서는 모든 패널에 같은 y축을 적용했습니다. 세 시점 절대가격 그림에서는 회사별 y축 범위가 달라 직접적인 가격 수준 비교를 제한했습니다. 실제 날짜 간격을 반영했으며 3시점 사이의 선은 관측점 연결로만 사용했습니다.

![초기 21개 일별](figures/us_initial_21_daily.png)

![초기 21개 3시점](figures/us_initial_21_three_dates.png)
'''
    # A partial offline/failed run must not leave broken evidence images in generated reports.
    for f in run['figures']:
        if not f['generated']:
            import re
            report = re.sub(r'!\[[^\]]*\]\(figures/' + re.escape(f['file']) + r'\)',
                            '필수 원자료가 없어 해당 그림을 생성하지 못했습니다.', report)
    (root / 'reports/analysis.md').write_text(report, encoding='utf-8')
    unusual = quality[quality.sum_status == 'review']
    verification_path = root / 'data/processed/company_verification.csv'
    verification = pd.read_csv(verification_path, dtype={'expected_code': str,'provider_code': str}) if verification_path.exists() else pd.DataFrame({'status':['verification_not_run']})
    failure = audit[(audit.status != 'ok') | audit.error.fillna('').ne('')]
    dq = f'''# 데이터 품질 보고서

이번 재현에서 새로 추가한 검증 결과를 정리했습니다. 과거 프로젝트가 이 검사를 수행했다고 가정하지 않았습니다.

## 표본·매칭·분류

미국 21개·한국 13개 고유 티커와 매출 104행을 입력했습니다. 매출 자료는 미국 18개·한국 13개에 연결했고 중복 티커·중복 부문·연결 실패 시 중단하도록 구현했습니다. TPL은 원 표본에 유지했고 COP·APA의 매출 누락 이유는 미확인으로 남겼습니다. 104행의 수치·음수·0을 보존했습니다.

KIND 현재 목록과 코드·시장을 대조했습니다. 세기상사는 현재 002420의 회사명이 우양피앤엘로 표시돼 제공 이름과 현재 이름을 구분했습니다. 2024년 공공기관 보고서의 세기상사 002420 표기와도 대조했습니다. 현재 명칭·시장 검증을 사건 시점의 완전한 상장 이력 검증으로 확대하지 않았습니다. FnGuide 웹 직접 조회는 오류 안내 페이지를 반환해 검증 근거로 사용하지 않았습니다.

{table(verification[[c for c in ['ticker','expected_company','provider_company','expected_code','provider_code','expected_market','status'] if c in verification]])}

분류는 원문 항목에 한정했습니다. `oil_gas_explicit`은 명시된 석유·가스 항목으로만, `other_explicit`은 명시된 다른 사업 항목으로만 표시했습니다. `mixed`와 `needs_review`는 실질 구성 확인을 보류했습니다. 이 분류를 검증된 전체 매출 노출이나 잔여 비석유 비중으로 해석하지 않았습니다.

## 매출 합계 이상

합계 100% 대비 ±0.1%p 이내는 반올림 점검용 범위로만 설정했습니다. 이 범위가 데이터의 정확성이나 완전성을 인증하지 않도록 제한했습니다. 다음 표에는 범위를 벗어난 회사만 표시했고 전체 회사는 [품질 표](../data/processed/revenue_quality.csv)에 보존했습니다.

{table(unusual[['ticker','company','total_pct','delta_from_100','negative_count','missing_count','review_segments']])}

S-Oil 80.1%는 일부 항목만 제공된 입력으로 처리했습니다. GS 기타 -0.94%는 원 입력으로 남겼으며 연결 조정 여부를 추정하지 않았습니다. HD현대 99.6%도 보존했고 사용자 설명의 기타 0.38%를 합산하지 않았습니다. 미국 WMB·OKE 등의 초과 합계도 임의 수정하지 않았습니다. 개별 행 결측이 없더라도 회사 매출 전체가 완전하다고 판정하지 않았습니다. 원문 URL·기준일·회계 기준의 미제공을 별도 한계로 기록했습니다.

## 수집·날짜·결측

실행 상태 `{run['status']}`, 수집 이상 {len(failure)}개 티커/기간, 정확한 사건 비교일 결측 {run['missing_reaction_rows']}개를 기록했습니다. 날짜 중복·비양수 종가는 허용하지 않았고 휴장일·결측을 보간하거나 0으로 대체하지 않았습니다. `missing_on_union_dates`는 수집 묶음에 관측된 날짜 집합의 결측 수로 정의했으며 휴장과 수집 오류를 단독으로 구별하는 값으로 사용하지 않았습니다.

{table(failure[['window','ticker','status','error']]) if len(failure) else '수집 묶음의 모든 요청 티커에서 유효한 관측을 확인했습니다.'}

유가 결측행 제외 수는 [정렬 표](../data/processed/oil_alignment.csv)에, 기업별 기간·시각·해시는 [수집 기록](../data/processed/acquisition_manifest.csv)에 남겼습니다. 요청 범위 바깥의 관측이 반환되면 오류로 중단하도록 구현했습니다. 종목 중간의 개별 공백은 거래소 일별 이력과 별도 대조하지 않았으므로 수집 성공만으로 전체 거래일의 완전성을 보증하지 않았습니다.

## 재현상의 차이와 미확인 사항

유가 `auto_adjust=True`, 주가 `False`를 명시했습니다. 이전 주가 코드의 기본값과 패키지 버전은 미확정이므로 수치 차이 가능성을 남겼습니다. 이전 CSV·그림이 없어 과거 결과와 수치 차이를 직접 대조하지 못했습니다. 한국 주가 수집·KIND 검증·품질 검사·캐시·로그·테스트를 이번 구현에 추가했습니다. 통계 검정·인과 추론·개인 기여 확인은 수행하지 않았습니다.
'''
    (root / 'reports/data_quality.md').write_text(dq, encoding='utf-8')
