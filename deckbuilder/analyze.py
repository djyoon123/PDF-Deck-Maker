"""컨설팅 자료 폴더 스캔 → 스타일 토큰 추출.

각 .pptx 의 OpenXML(theme1.xml, presentation.xml)만 열어(미디어 미추출) 색·폰트·슬라이드
규격을 집계한다. 결과를 요약 출력하고, 선택적으로 학습된 테마를 tokens.json 에 병합 저장한다.

사용:
    python -m deckbuilder.analyze "<폴더경로>" [--save-theme <이름>]
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import zipfile
from collections import Counter

_HERE = os.path.dirname(os.path.abspath(__file__))
_TOKENS_PATH = os.path.join(_HERE, "tokens.json")

_CLR_KEYS = ["dk1", "lt1", "dk2", "lt2", "accent1", "accent2", "accent3",
             "accent4", "accent5", "accent6", "hlink"]


def _color_from_block(block: str):
    m = re.search(r'srgbClr val="([0-9A-Fa-f]{6})"', block)
    if m:
        return "#" + m.group(1).upper()
    m = re.search(r'sysClr val="\w+" lastClr="([0-9A-Fa-f]{6})"', block)
    if m:
        return "#" + m.group(1).upper()
    return None


def _parse_theme(xml: str) -> dict:
    out = {"colors": {}, "major": None, "minor": None}
    cs = re.search(r"<a:clrScheme.*?</a:clrScheme>", xml, re.S)
    if cs:
        for key in _CLR_KEYS:
            m = re.search(rf"<a:{key}>(.*?)</a:{key}>", cs.group(), re.S)
            if m:
                c = _color_from_block(m.group(1))
                if c:
                    out["colors"][key] = c
    mj = re.search(r"<a:majorFont>.*?typeface=\"([^\"]+)\"", xml, re.S)
    mn = re.search(r"<a:minorFont>.*?typeface=\"([^\"]+)\"", xml, re.S)
    out["major"] = mj.group(1) if mj else None
    out["minor"] = mn.group(1) if mn else None
    return out


def _parse_size(xml: str):
    m = re.search(r'sldSz cx="(\d+)" cy="(\d+)"(?:\s+type="(\w+)")?', xml)
    if m:
        return int(m.group(1)), int(m.group(2)), (m.group(3) or "custom")
    return None


def analyze_pptx(path: str) -> dict | None:
    try:
        with zipfile.ZipFile(path) as z:
            names = set(z.namelist())
            theme = {}
            for cand in ("ppt/theme/theme1.xml", "ppt/theme/theme2.xml"):
                if cand in names:
                    theme = _parse_theme(z.read(cand).decode("utf-8", "ignore"))
                    break
            size = None
            if "ppt/presentation.xml" in names:
                size = _parse_size(z.read("ppt/presentation.xml").decode("utf-8", "ignore"))
            n_slides = sum(1 for n in names if re.match(r"ppt/slides/slide\d+\.xml$", n))
        return {"file": os.path.basename(path), "theme": theme, "size": size,
                "slides": n_slides}
    except (zipfile.BadZipFile, KeyError, OSError):
        return None


def _is_grey(hexc: str) -> bool:
    h = hexc.lstrip("#")
    if len(h) != 6:
        return False
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return max(r, g, b) - min(r, g, b) < 18


def scan(folder: str, limit: int | None = None) -> dict:
    pptx = []
    for root, _dirs, files in os.walk(folder):
        for f in files:
            if f.lower().endswith((".pptx", ".ppt")) and not f.startswith("~$"):
                pptx.append(os.path.join(root, f))
    pptx.sort()
    if limit:
        pptx = pptx[:limit]

    results, sizes, majors, minors = [], Counter(), Counter(), Counter()
    accent_colors = Counter()
    ok = 0
    for p in pptx:
        r = analyze_pptx(p)
        if not r:
            continue
        ok += 1
        results.append(r)
        if r["size"]:
            sizes[(r["size"][0], r["size"][1], r["size"][2])] += 1
        if r["theme"].get("major"):
            majors[r["theme"]["major"]] += 1
        if r["theme"].get("minor"):
            minors[r["theme"]["minor"]] += 1
        # accent1/accent2/dk2 중 무채색이 아닌 것 = 브랜드 강조색 후보
        for k in ("accent1", "accent2", "dk2", "accent5"):
            c = r["theme"]["colors"].get(k)
            if c and not _is_grey(c) and c not in ("#FFFFFF", "#000000"):
                accent_colors[c] += 1

    return {
        "folder": folder,
        "total_found": len(pptx),
        "parsed_ok": ok,
        "top_sizes": sizes.most_common(5),
        "top_major_fonts": majors.most_common(6),
        "top_minor_fonts": minors.most_common(6),
        "top_accents": accent_colors.most_common(10),
        "files": results,
    }


def _print_report(rep: dict):
    print(f"\n== 스캔: {rep['folder']}")
    print(f"   PPTX {rep['total_found']}개 발견 / {rep['parsed_ok']}개 분석 성공\n")
    print("● 슬라이드 규격 (cx, cy, type) — 빈도")
    for (cx, cy, ty), n in rep["top_sizes"]:
        ratio = round(cx / cy, 3) if cy else 0
        print(f"    {cx} x {cy}  [{ty}]  비율 {ratio}   ×{n}")
    print("\n● 본문 폰트 (minor) — 빈도")
    for name, n in rep["top_minor_fonts"]:
        print(f"    {name:28} ×{n}")
    print("\n● 제목 폰트 (major) — 빈도")
    for name, n in rep["top_major_fonts"]:
        print(f"    {name:28} ×{n}")
    print("\n● 브랜드 강조색 후보 — 빈도")
    for c, n in rep["top_accents"]:
        print(f"    {c}   ×{n}")
    print()


def _save_theme(name: str, rep: dict):
    """가장 흔한 강조색으로 학습 테마를 tokens.json 에 추가/갱신."""
    if not rep["top_accents"]:
        print("강조색을 찾지 못해 테마를 저장하지 않았습니다.")
        return
    accent = rep["top_accents"][0][0]
    with open(_TOKENS_PATH, encoding="utf-8") as fh:
        tokens = json.load(fh)
    tokens.setdefault("themes", {})[name] = {
        "color": {"accent": accent, "accent_soft": _tint(accent, 0.86)}
    }
    with open(_TOKENS_PATH, "w", encoding="utf-8") as fh:
        json.dump(tokens, fh, ensure_ascii=False, indent=2)
    print(f"✓ 테마 '{name}' 저장 (accent={accent}) → {_TOKENS_PATH}")
    print(f"  사용: build(..., theme=\"{name}\")")


def _tint(hexc: str, amount: float) -> str:
    """색을 흰색 쪽으로 amount(0~1)만큼 밝게."""
    h = hexc.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    r = round(r + (255 - r) * amount)
    g = round(g + (255 - g) * amount)
    b = round(b + (255 - b) * amount)
    return f"#{r:02X}{g:02X}{b:02X}"


def _main(argv):
    ap = argparse.ArgumentParser(description="컨설팅 자료 폴더 스타일 분석")
    ap.add_argument("folder", help="스캔할 폴더 경로")
    ap.add_argument("--limit", type=int, default=None, help="분석할 최대 파일 수")
    ap.add_argument("--save-theme", metavar="NAME", default=None,
                    help="가장 흔한 강조색으로 테마를 tokens.json 에 저장")
    ap.add_argument("--json", action="store_true", help="원시 결과를 JSON 으로 출력")
    args = ap.parse_args(argv)

    if not os.path.isdir(args.folder):
        print(f"폴더를 찾을 수 없습니다: {args.folder}")
        return 1
    rep = scan(args.folder, limit=args.limit)
    if args.json:
        print(json.dumps({k: v for k, v in rep.items() if k != "files"},
                         ensure_ascii=False, indent=2))
    else:
        _print_report(rep)
    if args.save_theme:
        _save_theme(args.save_theme, rep)
    return 0


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
