# 출처와 자료 계보

2026-11-12에 확인한 출처입니다. 제공된 과거 설명과 이번에 직접 수집한 자료를 구분했습니다.

| 자료 | 직접 출처 | 이번 사용 범위 |
|---|---|---|
| 사건 기준일 | [Reuters, 2026-02-28 공격 개시 보도](https://au.investing.com/news/israel-and-us-launch-strikes-on-iran-targeting-its-leadership-4285236?ampMode=1) | 미국·이스라엘의 이란 공격 개시를 2/28 사건 기준으로 설정 |
| 한국 휴장 | [삼성증권 2026년 3월 일정, 16쪽](https://www.samsungpop.com/common.do?cmd=down&contentType=application%2Fpdf&fileName=4010%2F2026022717364620K_02_01.pdf&inlineYn=Y&saveKey=research.pdf) | 3/2 삼일절 대체휴일 한국 증시 휴장 확인 |
| 공식 휴장 안내 경로 | [KRX 연간 일정](https://www.krx.co.kr/contents/MKD/01/0110/01100303/MKD01100303.jsp) | 웹 도구 403으로 본문 확인 실패; 증권사 일정과 실제 시세 날짜로 보완 |
| 주가·선물 | [Yahoo Finance](https://finance.yahoo.com/), [yfinance 문서](https://ranaroussi.github.io/yfinance/reference/api/yfinance.download.html) | 실제 Close 수집; end 배타적, 자동조정 정책 명시 |
| 한국 코드·시장 | [KIND KOSPI 목록](https://kind.krx.co.kr/corpgeneral/corpList.do?method=download&marketType=stockMkt), [KIND KOSDAQ 목록](https://kind.krx.co.kr/corpgeneral/corpList.do?method=download&marketType=kosdaqMkt) | 현재 목록을 직접 다운로드해 13개 코드·시장 대조; 8개 KOSPI·5개 KOSDAQ |
| 세기상사 과거 코드 | [한국콘텐츠진흥원 2024년 1분기 콘텐츠산업 동향 보고서](https://welcon.kocca.kr/cmm/fms/crawling/%5B%EC%B5%9C%EC%A2%85%5D2024%EB%85%84%201%EB%B6%84%EA%B8%B0%20%EC%BD%98%ED%85%90%EC%B8%A0%EC%82%B0%EC%97%85%20%EB%8F%99%ED%96%A5%EB%B6%84%EC%84%9D%20%EB%B3%B4%EA%B3%A0%EC%84%9C_241115%EC%88%98%EC%A0%95%EB%B3%B8_%EB%AF%B8%EB%A6%AC%EB%B3%B4%EA%B8%B0?atchFileId=FILE_f5f7b9d0-cdd8-41d4-8b99-f5854dbb7efd&fileSn=1) | 표 9-6의 세기상사 002420과 현재 KIND의 우양피앤엘 002420을 구분; 정확한 명칭 변경일은 미검증 |
| TPL 사업 | [2025 Form 10-K, SEC](https://www.sec.gov/Archives/edgar/data/1811074/000181107426000018/tpl-20251231.htm) | 토지·자원 관리와 물 사업, 석유·가스 로열티 수익원을 확인; 비석유 부동산 기업으로 단정하지 않음 |
| 미국 초기 후보 탐색 | [Wikipedia S&P 500 목록](https://en.wikipedia.org/wiki/List_of_S%26P_500_companies) | 선택 스크립트에서 실행 시점 GICS Energy만 수집; 고정 21개와 별개 |
| 매출 입력 | 사용자 제공 문서의 한국 50행·미국 54행 | FnGuide·기업 IR 기반의 사용자 전사. 수치 원형 보존. 회사별 원문 링크·회계 기준·대부분 기준일은 미제공 |

FnGuide 회사 페이지를 직접 요청했으나 오류 안내 HTML이 반환돼 독립 검증 근거로 사용하지 않았습니다. 매출 입력의 FnGuide·IR 출처 표기는 사용자 설명이며 해당 원문들을 직접 확인했다는 의미가 아닙니다. HD현대 2025.12 기준 및 기타 0.38%도 사용자 전사 설명으로만 기록했고, 캡처 이미지는 제공되지 않았습니다.

미국 고정 21개의 세부 업종은 제공된 당시 라벨입니다. 현재 GICS 또는 사건일 GICS로 새로 인증하지 않았습니다. TPL의 제공 분류도 초기 기록에 보존했으며 주 비교 제외는 별도 결정 파일에 기록했습니다.

## 이용 조건과 공개 범위

[yfinance README](https://github.com/ranaroussi/yfinance#readme)는 연구·교육 목적의 도구라는 점과 Yahoo 데이터 이용 권리가 별개임을 안내합니다. Yahoo API의 개인 이용 안내도 확인했습니다. [Yahoo 이용약관](https://legal.yahoo.com/us/en/yahoo/terms/otos/index.html)은 직접 조회 시 999 응답으로 본문 전체를 확인하지 못했습니다. 따라서 외부 원자료의 공개 재배포 권리를 확보했다고 주장하지 않았습니다.

다운로드한 시세·KIND 목록·페이지 캐시는 `data/raw/`에 보관하고 기본 Git 추적에서 제외했습니다. 산출물은 분석 그림·변동률·선택일 요약을 중심으로 구성했습니다. 이것이 파생 산출물의 모든 공개 권리를 인증하지는 않으며 공개 전 적용 조건을 확인할 항목으로 남겼습니다. 라이브러리 라이선스를 원자료나 프로젝트 전체에 확대 적용하지 않았고 프로젝트 라이선스를 임의로 추가하지 않았습니다.

수집 시각·패키지 버전·요청 범위·실제 관측 범위·캐시 해시는 `data/processed/acquisition_manifest.csv`, 실행 버전과 입력 해시는 `data/processed/run_manifest.json`에 기록했습니다.
