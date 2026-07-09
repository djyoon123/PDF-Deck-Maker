"""deck-spec → HTML 조립 → Chrome 헤드리스 → PDF.

사용:
    from deckbuilder.render import build
    build(title="...", slides=[{...}], out="output/deck.pdf", theme="neutral",
          meta={"project":"...", "date":"2026-07"})

CLI:
    python -m deckbuilder.render spec.json          # JSON 스펙에서 렌더
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time

from . import theme as _theme
from .components import SLIDES

_HERE = os.path.dirname(os.path.abspath(__file__))
_CSS_PATH = os.path.join(os.path.dirname(_HERE), "templates", "base.css")

# 페이지 번호를 매기지 않는(그리고 카운터도 올리지 않는) 슬라이드 타입
_UNNUMBERED = {"cover"}


def _find_chrome() -> str:
    env = os.environ.get("CHROME_BIN")
    if env and os.path.exists(env):
        return env
    candidates = [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Google Chrome Canary.app/Contents/MacOS/Google Chrome Canary",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
        shutil.which("google-chrome"),
        shutil.which("chromium"),
        shutil.which("chromium-browser"),
    ]
    for c in candidates:
        if c and os.path.exists(c):
            return c
    raise RuntimeError(
        "Chrome 실행 파일을 찾지 못했습니다. 환경변수 CHROME_BIN 에 경로를 지정하세요.\n"
        "예: export CHROME_BIN='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'"
    )


def render_html(title, slides, *, theme="neutral", meta=None, overrides=None,
                tokens_path=None) -> str:
    """deck-spec → 완결된 HTML 문서 문자열."""
    cfg = _theme.resolve(theme=theme, overrides=overrides, tokens_path=tokens_path)
    base_meta = dict(cfg.get("meta", {}))
    if meta:
        base_meta.update({k: v for k, v in meta.items() if v is not None})

    with open(_CSS_PATH, encoding="utf-8") as fh:
        base_css = fh.read()
    var_css = _theme.css_variables(cfg)

    page = 0
    out = []
    for i, spec in enumerate(slides):
        stype = spec.get("type")
        fn = SLIDES.get(stype)
        if fn is None:
            raise ValueError(
                f"슬라이드 #{i+1}: 알 수 없는 type '{stype}'. "
                f"사용 가능: {', '.join(sorted(SLIDES))}"
            )
        if stype not in _UNNUMBERED:
            page += 1
        ctx = {"page": page, "meta": base_meta, "deck_title": title}
        out.append(fn(cfg, spec, ctx))

    body = "\n".join(out)
    html = (
        "<!doctype html><html lang=\"ko\"><head><meta charset=\"utf-8\">"
        f"<title>{_esc(title)}</title><style>\n{var_css}\n{base_css}\n</style>"
        f"</head><body>\n{body}\n</body></html>"
    )
    return html


def _esc(s):
    import html as _h
    return _h.escape(str(s), quote=True)


def to_pdf(html: str, out: str, *, keep_html=False) -> str:
    """HTML 문자열을 Chrome 헤드리스로 PDF 렌더링."""
    out = os.path.abspath(out)
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    chrome = _find_chrome()

    tmp_dir = tempfile.mkdtemp(prefix="deckbuilder_")
    html_path = os.path.join(tmp_dir, "deck.html")
    with open(html_path, "w", encoding="utf-8") as fh:
        fh.write(html)

    user_data = os.path.join(tmp_dir, "profile")
    if os.path.exists(out):
        os.remove(out)
    cmd = [
        chrome,
        "--headless=new",
        "--disable-gpu",
        "--no-sandbox",
        "--no-first-run",
        "--no-pdf-header-footer",
        "--font-render-hinting=none",
        "--force-color-profile=srgb",
        "--hide-scrollbars",
        f"--user-data-dir={user_data}",
        f"--print-to-pdf={out}",
        f"file://{html_path}",
    ]
    # 일부 Chrome 빌드는 --print-to-pdf 후에도 프로세스가 종료되지 않는다.
    # 결과 파일이 생성되면 즉시 종료시키는 poll-and-kill 방식으로 처리한다.
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    deadline = time.time() + 60
    stable_since = None
    last_size = -1
    while time.time() < deadline:
        if proc.poll() is not None:
            break
        if os.path.exists(out):
            size = os.path.getsize(out)
            if size > 0 and size == last_size:
                if stable_since is None:
                    stable_since = time.time()
                elif time.time() - stable_since > 0.8:
                    break  # 파일 크기가 안정화됨 → 완료
            else:
                stable_since = None
                last_size = size
        time.sleep(0.25)
    if proc.poll() is None:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
    if not os.path.exists(out) or os.path.getsize(out) == 0:
        err = b""
        try:
            err = proc.stderr.read() or b""
        except Exception:
            pass
        raise RuntimeError(
            "Chrome 렌더링 실패: PDF 가 생성되지 않았습니다.\n"
            f"STDERR:\n{err.decode('utf-8', 'ignore')[-2000:]}"
        )
    if keep_html:
        saved = out.rsplit(".", 1)[0] + ".html"
        shutil.copyfile(html_path, saved)
    shutil.rmtree(tmp_dir, ignore_errors=True)
    return out


def build(title, slides, out="output/deck.pdf", *, theme="neutral", meta=None,
          overrides=None, tokens_path=None, keep_html=False) -> str:
    """엔드투엔드: deck-spec → PDF. 산출 경로 반환."""
    html = render_html(title, slides, theme=theme, meta=meta, overrides=overrides,
                       tokens_path=tokens_path)
    path = to_pdf(html, out, keep_html=keep_html)
    print(f"✓ PDF 생성: {path}  ({len(slides)} 슬라이드, 테마={theme})")
    return path


def build_from_spec(spec: dict, out=None) -> str:
    """dict 스펙(딕셔너리 하나) → PDF. spec 키: title, slides, theme, meta, out."""
    return build(
        title=spec.get("title", "제목 없음"),
        slides=spec.get("slides", []),
        out=out or spec.get("out", "output/deck.pdf"),
        theme=spec.get("theme", "neutral"),
        meta=spec.get("meta"),
        overrides=spec.get("overrides"),
        keep_html=spec.get("keep_html", False),
    )


def _main(argv):
    if not argv:
        print("사용법: python -m deckbuilder.render <spec.json> [out.pdf]")
        return 1
    with open(argv[0], encoding="utf-8") as fh:
        spec = json.load(fh)
    out = argv[1] if len(argv) > 1 else None
    build_from_spec(spec, out=out)
    return 0


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
