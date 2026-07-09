# consulting-deck

브리프만 주면 **전략컨설팅 품질의 읽기용 PDF 덱**을 그려주는 Claude Code 플러그인.

PwC·McKinsey·BCG·EY·Kearney·KPMG의 실제 산출물 코퍼스에서 학습한 **레이아웃 그리드·타이포·12개
슬라이드 아키타입**을 HTML/CSS로 조립하고 **Chrome 헤드리스**로 PDF 렌더링한다.
python-pptx 없이 동작하며, 파이썬 표준 라이브러리만 사용한다(오프라인·무설치).

- **출력**: 편집 불필요한 읽기용 `.pdf`
- **기본 테마**: 중립 미니멀 (클라이언트별 리테마 지원: `pwc`/`kpmg`/`bcg`/`kearney`/`house`)
- **언어**: 한국어 우선(영문 혼용)

## 요구사항
- Python 3.9+
- Google Chrome (`--headless --print-to-pdf` 용). 비표준 경로면 `CHROME_BIN` 환경변수로 지정.

## 설치 (로컬 마켓플레이스)
인터랙티브 `claude` 세션에서:
```
/plugin marketplace add /Users/steve/Desktop/consulting-deck
/plugin install consulting-deck
```

## 사용
- **덱 만들기**: `/deck <한 문단 브리프>`
  → `deck-builder` 에이전트가 스토리라인을 잡고 `output/*.pdf` 를 렌더링.
- **스타일 학습**: `/deck-analyze "<덱 폴더>" --save-theme <이름>`
  → 색·폰트·규격을 분석하고 학습 테마를 저장. 이후 `theme="<이름>"` 로 사용.

### 코드로 직접
```python
import sys; sys.path.insert(0, "/Users/steve/Desktop/consulting-deck")
from deckbuilder.render import build

build(
    title="신규 시장 진출 전략 (샘플 덱)",
    meta={"project": "Project Sample", "date": "2026.07", "source_default": "자료: 팀 분석"},
    theme="neutral",
    slides=[
        {"type": "cover", "subtitle": "최종 보고", "client": "샘플기업 (Sample Co.)"},
        {"type": "executive_summary", "title": "...", "points": [...], "kpi": [...]},
        # ... 12개 아키타입
    ],
    out="output/sample.pdf",
)
```
각 아키타입의 상세 인자는 [`skills/build-deck/SKILL.md`](skills/build-deck/SKILL.md) 참고.

## 12개 슬라이드 아키타입
`cover` · `agenda` · `section` · `executive_summary` · `content`(불릿+차트) ·
`matrix_2x2` · `mece` · `roadmap` · `kpi` · `market_sizing`(TAM-SAM-SOM) ·
`comparison`(벤치마킹 표) · `process`

각 타입의 상세 스펙과 작성 규칙은 [`skills/build-deck/SKILL.md`](skills/build-deck/SKILL.md) 참고.

## 구조
```
deckbuilder/     파이썬 패키지 (tokens.json, theme, components, charts, render, analyze)
templates/       base.css (디자인 시스템)
commands/        /deck, /deck-analyze
agents/          deck-builder
skills/          build-deck (방법론 + API 레퍼런스)
```

## 커스터마이즈
- **색만 변경**: `build(..., overrides={"color": {"accent": "#0B5"}})`
- **테마 추가**: `deckbuilder/tokens.json` 의 `themes` 에 항목 추가
- **새 아키타입**: `deckbuilder/components.py` 에 빌더 함수 + `SLIDES` 레지스트리 등록, `templates/base.css` 에 스타일 추가
- **규격 변경(A4 등)**: `tokens.json` 의 `base.page`(기본 16:9 1280×720)
