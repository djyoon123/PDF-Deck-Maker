---
name: build-deck
description: 브리프를 전략컨설팅 품질의 읽기용 PDF 덱으로 만든다. 슬라이드/PPT/덱/보고서/제안서를 "그려줘/만들어줘"라고 하거나, 시장분석·전략·CDD·PMI·사업계획 같은 컨설팅형 산출물을 요청할 때 사용. 한국어 우선, 중립 미니멀 기본 테마(pwc/kpmg/bcg/kearney/house 리테마 가능). deckbuilder(파이썬 stdlib) + Chrome 헤드리스로 실제 .pdf 파일을 출력한다.
---

# build-deck — 컨설팅 덱 빌더

브리프 → **스토리라인 → deck-spec(파이썬 dict) → HTML → PDF**. python-pptx 없이 HTML/CSS를
Chrome 헤드리스로 렌더링해 픽셀 정밀한 컨설팅 슬라이드를 만든다. 전제: Google Chrome 설치.

플러그인 루트는 런타임에 `${CLAUDE_PLUGIN_ROOT}` 로 참조한다. 코드는 그 아래 `deckbuilder/`.

## 워크플로 (반드시 이 순서)

1. **브리프 해석 & 질문**: 목적·청중·핵심 메시지·페이지 수를 파악. 불명확하면 1~2개만 질문.
2. **스토리라인 먼저 (텍스트로)**: 슬라이드를 그리기 전에 아웃라인을 **액션 타이틀 리스트**로 먼저 쓴다.
   - SCQA(상황-복잡성-질문-답)로 도입, **피라미드 구조**(결론 먼저 → 근거).
   - **슬라이드 1장 = 메시지 1개**. 타이틀은 명사구가 아니라 **결론 문장**.
     - ✗ "유럽 시장 개요"  → ✓ "유럽은 현지 생산 없이는 대형 수주가 구조적으로 어렵다"
3. **아키타입 매핑**: 각 메시지에 가장 맞는 슬라이드 타입 1개를 배정(아래 표).
4. **deck-spec 작성**: 파이썬 스크립트로 `build(...)` 호출. `output/<이름>.pdf` 로 출력.
5. **렌더 & 검증**: 실행 → PDF 생성 확인. 사용자에게 경로 안내(원하면 슬라이드별 근거 요약).

## 실행 방법

작업 폴더(사용자 CWD)에 빌드 스크립트를 쓰고 실행한다. 예:

```python
import sys; sys.path.insert(0, "${CLAUDE_PLUGIN_ROOT}")
from deckbuilder.render import build

build(
    title="신규 시장 진출 전략 (샘플 덱)",
    meta={"project": "Project Sample", "date": "2026.07",
          "source_default": "자료: 팀 분석"},   # 데이터 슬라이드 기본 출처
    theme="neutral",        # neutral(기본) | pwc | kpmg | bcg | kearney | house
    slides=[ ... ],         # 아래 아키타입 스펙 리스트
    out="output/sample.pdf",
)
```

실행: `python3 build_deck.py` (또는 `python3 -m deckbuilder.render spec.json`). Chrome 경로가
비표준이면 `CHROME_BIN` 환경변수로 지정.

## 12개 아키타입 스펙 레퍼런스

모든 슬라이드는 dict, 필수 키 `type`. 공통 선택 키: `kicker`(상단 라벨), `source`(푸터 출처, 미지정 시
meta.source_default), `takeaway`(하단 시사점 배너). 텍스트에 `**굵게**` 마크업 가능.

| type | 용도 | 핵심 키 |
|------|------|--------|
| `cover` | 표지 | subtitle, client, date, author, confidential |
| `agenda` | 목차 | items(문자열 또는 {label,sub}), active(강조 번호/라벨) |
| `section` | 섹션 구분(다크) | num, title, subtitle |
| `executive_summary` | 핵심 요약 | title, points([{lead,body}]), kpi([{value,label,delta}]) |
| `content` | 액션타이틀+불릿(+비주얼) | title, bullets([{label,body,subs}]), visual, visual_span |
| `matrix_2x2` | 2×2 매트릭스 | title, x, y, x_axis, y_axis, quadrants[4], items([{label,q,note}]) |
| `mece` | MECE 컬럼 | title, columns([{title,badge,items[]}]) |
| `roadmap` | 로드맵/타임라인 | title, phases([{name,period,items[]}]) |
| `kpi` | KPI 카드(최대 4) | title, cards([{label,value,trend,delta,note}]) |
| `market_sizing` | TAM-SAM-SOM/퍼널 | title, unit, data([(label,value,note)]) |
| `comparison` | 비교/벤치마킹 표 | title, columns[], rows([{label,cells[],highlight}]), highlight_col |
| `process` | 프로세스 플로우 | title, steps([{name,desc}]) |

### 세부 규칙
- **matrix_2x2 `q`**: 1=좌상, 2=우상, 3=좌하, 4=우하. q2(우상단)가 자동 강조됨 → 결론 사분면을 q2에 두라.
- **comparison `cells`**: 평점은 `"high"|"mid"|"low"|"none"`(●●●~○○○) 또는 `"yes"|"no"`(✔/—) 또는 임의 문자열.
  `highlight_col`(0-base)로 추천 열 강조.
- **kpi `trend`**: `"up"|"down"|"flat"` (▲녹색/▼적색/▬). `delta`는 증감 라벨.
- **content `visual`** (우측 도표): dict, `kind`:
  - `"bar"|"hbar"`: `data=[(label,value)]`, `unit`, `highlight`
  - `"line"`: `series=[(name,[values])]`, `labels=[x축]`, `unit`
  - `"waterfall"`: `data=[(label,value)]`, `unit`
  - `"donut"`: `data=[(label,value)]`, `unit`, `center`
  - `"stat"`: `data=[{value,label}]` (큰 숫자 나열)
  - `"note"`: `text` (사이드 노트 박스)
  - 텍스트+도표 배치 시 `visual_span`(기본 "44%")으로 도표 폭 조절.

## 품질 체크리스트 (렌더 전 자문)
- [ ] 모든 타이틀이 **결론 문장**인가? (명사구 금지)
- [ ] 슬라이드당 메시지 1개인가?
- [ ] 프레임워크/표가 **MECE**인가? (중복·누락 없음)
- [ ] 데이터 슬라이드에 **출처**가 있는가?
- [ ] 표지→목차→(섹션→내용)*→핵심요약 흐름이 피라미드인가?
- [ ] 숫자에 단위와 기준연도가 붙어 있는가?

## 스타일 학습 / 리테마
- 기존 덱 폴더에서 색·폰트·규격을 학습해 새 테마 저장:
  `python3 -m deckbuilder.analyze "<폴더>" --save-theme <이름>` → 이후 `theme="<이름>"`.
- 색만 바꾸려면 `build(..., overrides={"color":{"accent":"#0B5"}})`.

## 참고
- 각 아키타입의 인자 형태는 위 표와 `deckbuilder/components.py` 의 빌더 함수 시그니처를 참고.
- 새 아키타입/디자인 토큰은 `deckbuilder/components.py`, `templates/base.css`, `deckbuilder/tokens.json`.
