---
description: 기존 컨설팅 자료 폴더(PPTX)를 스캔해 색·폰트·슬라이드 규격을 분석하고, 원하면 학습된 테마를 저장한다.
argument-hint: <스캔할 폴더 경로> [--save-theme <이름>] [--limit N]
---

기존 덱에서 스타일을 학습하는 요청이다.

**인자:** $ARGUMENTS

다음을 수행하라:

1. 인자에서 폴더 경로(및 선택적 `--save-theme <이름>`, `--limit N`)를 파싱한다.
2. 아래 명령을 실행한다(경로에 공백이 있으면 따옴표로 감싼다):

   ```bash
   python3 -m deckbuilder.analyze "<폴더>" [--limit N] [--save-theme <이름>]
   ```

   `${CLAUDE_PLUGIN_ROOT}` 가 `sys.path` 에 없으면
   `cd "${CLAUDE_PLUGIN_ROOT}" && python3 -m deckbuilder.analyze ...` 로 실행한다.
3. 리포트(슬라이드 규격 분포, 본문/제목 폰트 빈도, 브랜드 강조색 후보)를 사용자에게 요약한다.
4. `--save-theme` 가 있으면 가장 흔한 강조색으로 `tokens.json` 에 테마가 저장된다.
   이후 `/deck` 에서 `theme="<이름>"` 로 그 스타일을 쓸 수 있음을 안내한다.

폴더가 없거나 PPTX 가 없으면 그 사실을 알리고 올바른 경로를 요청한다.
