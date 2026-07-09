"""디자인 토큰 로드 · 병합 · CSS 변수 생성.

tokens.json 의 base 위에 선택한 theme 를, 그 위에 사용자 overrides 를 깊은 병합한다.
결과 config(dict) 로부터 :root CSS 변수 블록과 전역 base CSS 를 만든다.
"""

from __future__ import annotations

import copy
import json
import os

_HERE = os.path.dirname(os.path.abspath(__file__))
_TOKENS_PATH = os.path.join(_HERE, "tokens.json")


def _deep_merge(a: dict, b: dict) -> dict:
    """b 를 a 위에 깊은 병합한 새 dict 반환."""
    out = copy.deepcopy(a)
    for k, v in (b or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = copy.deepcopy(v)
    return out


def load_tokens(path: str | None = None) -> dict:
    with open(path or _TOKENS_PATH, encoding="utf-8") as fh:
        return json.load(fh)


def resolve(theme: str = "neutral", overrides: dict | None = None,
            tokens_path: str | None = None) -> dict:
    """base + theme + overrides 병합된 최종 config 반환."""
    tokens = load_tokens(tokens_path)
    cfg = copy.deepcopy(tokens["base"])
    theme_patch = tokens.get("themes", {}).get(theme)
    if theme_patch is None:
        available = ", ".join(tokens.get("themes", {}))
        raise ValueError(f"알 수 없는 테마 '{theme}'. 사용 가능: {available}")
    cfg = _deep_merge(cfg, theme_patch)
    if overrides:
        cfg = _deep_merge(cfg, overrides)
    cfg["_theme"] = theme
    return cfg


def css_variables(cfg: dict) -> str:
    """config → :root { --c-ink: ...; } 문자열."""
    color = cfg["color"]
    font = cfg["font"]
    page = cfg["page"]
    lines = []
    for key, val in color.items():
        if key == "series":
            for i, s in enumerate(val):
                lines.append(f"  --series-{i}: {s};")
        else:
            lines.append(f"  --c-{key.replace('_', '-')}: {val};")
    lines.append(f"  --font-sans: {font['sans']};")
    lines.append(f"  --font-num: {font['num']};")
    for key in ("title_px", "kicker_px", "body_px", "small_px", "footer_px",
                "cover_title_px", "section_num_px", "section_title_px", "data_px"):
        lines.append(f"  --fs-{key.replace('_px', '').replace('_', '-')}: {font[key]}px;")
    lines.append(f"  --page-w: {page['width_px']}px;")
    lines.append(f"  --page-h: {page['height_px']}px;")
    lines.append(f"  --mx: {page['margin_x_px']}px;")
    lines.append(f"  --mt: {page['margin_top_px']}px;")
    lines.append(f"  --mb: {page['margin_bottom_px']}px;")
    return ":root {\n" + "\n".join(lines) + "\n}"


def series_color(cfg: dict, i: int) -> str:
    series = cfg["color"]["series"]
    return series[i % len(series)]
