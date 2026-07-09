"""슬라이드 아키타입 → HTML 빌더 + 전역 base CSS.

각 아키타입 함수 시그니처: fn(cfg, spec, ctx) -> str  (완결된 <section class="slide">).
ctx = {"page": int, "meta": dict}. 레지스트리 SLIDES 로 render.py 가 디스패치.
"""

from __future__ import annotations

import html
from . import charts

# --------------------------------------------------------------------------- #
# 공통 유틸
# --------------------------------------------------------------------------- #

def esc(s) -> str:
    return html.escape(str(s), quote=True)


def _rich(s) -> str:
    """**굵게** 만 가벼운 마크업으로 허용. 나머지는 이스케이프."""
    import re
    out = esc(s)
    out = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", out)
    return out


def _footer(cfg, ctx, source=None):
    meta = ctx.get("meta", {})
    src = source if source is not None else meta.get("source_default", "")
    mid_bits = [b for b in (meta.get("project", ""), meta.get("date", "")) if b]
    mid = "  ·  ".join(mid_bits)
    conf = meta.get("confidential", "")
    left = f'<span class="src">{esc(src)}</span>' if src else "<span></span>"
    return (
        '<div class="foot">'
        f'{left}'
        f'<span class="foot-mid">{esc(mid)}{("  ·  " + esc(conf)) if (mid and conf) else esc(conf)}</span>'
        f'<span class="foot-pg">{ctx["page"]}</span>'
        '</div>'
    )


def _head(cfg, kicker, title):
    k = f'<div class="kicker">{esc(kicker)}</div>' if kicker else ""
    return f'<div class="head">{k}<h1>{_rich(title)}</h1><div class="rule"></div></div>'


def _slide(inner, klass=""):
    return f'<section class="slide {klass}">{inner}</section>'


def _takeaway(text):
    if not text:
        return ""
    return f'<div class="takeaway"><span class="ta-tag">시사점</span>{_rich(text)}</div>'


# --------------------------------------------------------------------------- #
# 1. 표지
# --------------------------------------------------------------------------- #

def cover(cfg, spec, ctx):
    meta = ctx.get("meta", {})
    title = spec.get("title") or ctx.get("deck_title", "제목")
    subtitle = spec.get("subtitle", "")
    client = spec.get("client", meta.get("project", ""))
    date = spec.get("date", meta.get("date", ""))
    author = spec.get("author", "")
    conf = spec.get("confidential", meta.get("confidential", ""))
    tag = f'<div class="cover-tag">{esc(subtitle)}</div>' if subtitle else ""
    rows = []
    if client:
        rows.append(f'<div><span>CLIENT</span>{esc(client)}</div>')
    if date:
        rows.append(f'<div><span>DATE</span>{esc(date)}</div>')
    if author:
        rows.append(f'<div><span>PREPARED BY</span>{esc(author)}</div>')
    meta_html = f'<div class="cover-meta">{"".join(rows)}</div>' if rows else ""
    conf_html = f'<div class="cover-conf">{esc(conf)}</div>' if conf else ""
    inner = (
        '<div class="cover-body">'
        f'{tag}'
        f'<h1 class="cover-title">{_rich(title)}</h1>'
        f'{meta_html}'
        '</div>'
        f'{conf_html}'
    )
    return _slide(inner, "cover")


# --------------------------------------------------------------------------- #
# 2. 목차
# --------------------------------------------------------------------------- #

def agenda(cfg, spec, ctx):
    items = spec.get("items", [])
    title = spec.get("title", "목차")
    active = spec.get("active")  # 강조할 항목 인덱스(1-base) 또는 라벨
    rows = []
    for i, it in enumerate(items, 1):
        label = it if isinstance(it, str) else it.get("label", "")
        sub = "" if isinstance(it, str) else it.get("sub", "")
        is_active = (active == i or active == label)
        cls = "ag-item active" if is_active else "ag-item"
        sub_html = f'<div class="ag-sub">{esc(sub)}</div>' if sub else ""
        rows.append(
            f'<div class="{cls}"><div class="ag-no">{i:02d}</div>'
            f'<div class="ag-txt"><div class="ag-label">{esc(label)}</div>{sub_html}</div></div>'
        )
    inner = _head(cfg, spec.get("kicker", "AGENDA"), title) + \
        f'<div class="body"><div class="ag-list">{"".join(rows)}</div></div>' + \
        _footer(cfg, ctx, spec.get("source", ""))
    return _slide(inner)


# --------------------------------------------------------------------------- #
# 3. 섹션 구분
# --------------------------------------------------------------------------- #

def section(cfg, spec, ctx):
    num = spec.get("num", "")
    title = spec.get("title", "")
    sub = spec.get("subtitle", "")
    num_html = f'<div class="sec-num">{esc(num)}</div>' if num else ""
    sub_html = f'<div class="sec-sub">{esc(sub)}</div>' if sub else ""
    inner = (
        '<div class="sec-body">'
        f'{num_html}<h1 class="sec-title">{_rich(title)}</h1>{sub_html}'
        '</div>'
        f'<div class="foot"><span></span><span class="foot-pg">{ctx["page"]}</span></div>'
    )
    return _slide(inner, "section")


# --------------------------------------------------------------------------- #
# 4. 핵심 요약 (Executive Summary)
# --------------------------------------------------------------------------- #

def executive_summary(cfg, spec, ctx):
    title = spec.get("title", "핵심 요약")
    points = spec.get("points", [])
    kpis = spec.get("kpi", [])
    pt_html = []
    for p in points:
        if isinstance(p, dict):
            lead = p.get("lead", "")
            body = p.get("body", "")
            lead_html = f'<b>{_rich(lead)}</b> ' if lead else ""
            pt_html.append(f'<li>{lead_html}{_rich(body)}</li>')
        else:
            pt_html.append(f'<li>{_rich(p)}</li>')
    left = f'<ol class="es-points">{"".join(pt_html)}</ol>'
    right = ""
    if kpis:
        cards = []
        for k in kpis:
            cards.append(
                f'<div class="es-kpi"><div class="es-kpi-v">{esc(k.get("value",""))}</div>'
                f'<div class="es-kpi-l">{esc(k.get("label",""))}</div>'
                + (f'<div class="es-kpi-d">{esc(k.get("delta",""))}</div>' if k.get("delta") else "")
                + '</div>'
            )
        right = f'<div class="es-kpis">{"".join(cards)}</div>'
    grid = f'<div class="es-grid {"has-kpi" if kpis else ""}">{left}{right}</div>'
    inner = _head(cfg, spec.get("kicker", "EXECUTIVE SUMMARY"), title) + \
        f'<div class="body">{grid}</div>' + _footer(cfg, ctx, spec.get("source", ""))
    return _slide(inner)


# --------------------------------------------------------------------------- #
# 5. 일반 콘텐츠 (액션타이틀 + 불릿 + 선택 비주얼)
# --------------------------------------------------------------------------- #

def _bullets(items):
    out = []
    for it in items:
        if isinstance(it, dict):
            label = it.get("label") or it.get("lead") or ""
            body = it.get("body", "")
            subs = it.get("subs", [])
            lead = f'<b>{_rich(label)}</b>' if label else ""
            sep = " — " if (label and body) else ""
            sub_html = ""
            if subs:
                sub_html = '<ul class="sub">' + "".join(f'<li>{_rich(s)}</li>' for s in subs) + '</ul>'
            out.append(f'<li>{lead}{sep}{_rich(body)}{sub_html}</li>')
        else:
            out.append(f'<li>{_rich(it)}</li>')
    return f'<ul class="bullets">{"".join(out)}</ul>'


def _visual(cfg, v):
    """spec['visual'] dict → SVG/HTML. kind: bar|hbar|line|waterfall|donut|stat|note."""
    if not v:
        return ""
    kind = v.get("kind")
    if kind in ("bar", "hbar"):
        return charts.bar_chart(cfg, v["data"], unit=v.get("unit", ""),
                                horizontal=(kind == "hbar"),
                                highlight=v.get("highlight"),
                                width=v.get("width", 520), height=v.get("height", 300))
    if kind == "line":
        return charts.line_chart(cfg, v["series"], labels=v.get("labels"),
                                 unit=v.get("unit", ""),
                                 width=v.get("width", 520), height=v.get("height", 300))
    if kind == "waterfall":
        return charts.waterfall(cfg, v["data"], unit=v.get("unit", ""),
                                width=v.get("width", 520), height=v.get("height", 300))
    if kind == "donut":
        return charts.donut(cfg, v["data"], unit=v.get("unit", "%"),
                            center_label=v.get("center"),
                            width=v.get("width", 260), height=v.get("height", 260))
    if kind == "stat":
        cards = []
        for s in v["data"]:
            cards.append(
                f'<div class="stat"><div class="stat-v">{esc(s.get("value",""))}</div>'
                f'<div class="stat-l">{esc(s.get("label",""))}</div></div>'
            )
        return f'<div class="stat-col">{"".join(cards)}</div>'
    if kind == "note":
        return f'<div class="side-note">{_rich(v.get("text",""))}</div>'
    return ""


def content(cfg, spec, ctx):
    title = spec.get("title", "")
    body_items = spec.get("bullets", spec.get("points", []))
    visual = spec.get("visual")
    body_col = _bullets(body_items) if body_items else ""
    if body_items and visual:
        vis_w = spec.get("visual_span", "44%")
        body = (f'<div class="split" style="--vis:{vis_w}">'
                f'<div class="split-l">{body_col}</div>'
                f'<div class="split-r">{_visual(cfg, visual)}</div></div>')
    elif visual:
        body = f'<div class="center-vis">{_visual(cfg, visual)}</div>'
    else:
        body = body_col
    body += _takeaway(spec.get("takeaway"))
    inner = _head(cfg, spec.get("kicker", ""), title) + \
        f'<div class="body">{body}</div>' + _footer(cfg, ctx, spec.get("source", ""))
    return _slide(inner)


# --------------------------------------------------------------------------- #
# 6. 2x2 매트릭스
# --------------------------------------------------------------------------- #

def matrix_2x2(cfg, spec, ctx):
    title = spec.get("title", "")
    xlab = spec.get("x", ("낮음", "높음"))
    ylab = spec.get("y", ("낮음", "높음"))
    xaxis = spec.get("x_axis", "")
    yaxis = spec.get("y_axis", "")
    items = spec.get("items", [])  # {label, q:1..4, note}  q: 1=좌상,2=우상,3=좌하,4=우하
    quad_titles = spec.get("quadrants", ["", "", "", ""])
    quads = {1: [], 2: [], 3: [], 4: []}
    for it in items:
        quads.get(it.get("q", 1), quads[1]).append(it)
    def cell(qi):
        qt = quad_titles[qi-1] if qi-1 < len(quad_titles) else ""
        qt_html = f'<div class="q-title">{esc(qt)}</div>' if qt else ""
        chips = "".join(
            f'<div class="q-chip">{_rich(it.get("label",""))}'
            + (f'<span class="q-note">{esc(it.get("note",""))}</span>' if it.get("note") else "")
            + '</div>'
            for it in quads[qi]
        )
        return f'<div class="quad q{qi}">{qt_html}<div class="q-chips">{chips}</div></div>'
    grid = (
        '<div class="matrix">'
        f'<div class="y-axis"><span>{esc(yaxis)}</span></div>'
        '<div class="matrix-inner">'
        f'<div class="y-hi">{esc(ylab[1])}</div>'
        f'{cell(1)}{cell(2)}{cell(3)}{cell(4)}'
        f'<div class="y-lo">{esc(ylab[0])}</div>'
        f'<div class="x-lo">{esc(xlab[0])}</div>'
        f'<div class="x-hi">{esc(xlab[1])}</div>'
        '</div>'
        f'<div class="x-axis"><span>{esc(xaxis)}</span></div>'
        '</div>'
    )
    inner = _head(cfg, spec.get("kicker", ""), title) + \
        f'<div class="body">{grid}{_takeaway(spec.get("takeaway"))}</div>' + \
        _footer(cfg, ctx, spec.get("source", ""))
    return _slide(inner)


# --------------------------------------------------------------------------- #
# 7. MECE 컬럼
# --------------------------------------------------------------------------- #

def mece(cfg, spec, ctx):
    title = spec.get("title", "")
    cols = spec.get("columns", [])
    n = len(cols) or 1
    col_html = []
    for i, c in enumerate(cols):
        head = c.get("title", "")
        items = c.get("items", [])
        lis = "".join(f'<li>{_rich(it)}</li>' for it in items)
        badge = f'<div class="mece-badge">{esc(c.get("badge",""))}</div>' if c.get("badge") else ""
        col_html.append(
            f'<div class="mece-col"><div class="mece-h">{badge}<span>{_rich(head)}</span></div>'
            f'<ul class="mece-items">{lis}</ul></div>'
        )
    grid = f'<div class="mece" style="--cols:{n}">{"".join(col_html)}</div>'
    inner = _head(cfg, spec.get("kicker", ""), title) + \
        f'<div class="body">{grid}{_takeaway(spec.get("takeaway"))}</div>' + \
        _footer(cfg, ctx, spec.get("source", ""))
    return _slide(inner)


# --------------------------------------------------------------------------- #
# 8. 로드맵 / 타임라인
# --------------------------------------------------------------------------- #

def roadmap(cfg, spec, ctx):
    title = spec.get("title", "")
    phases = spec.get("phases", [])
    n = len(phases) or 1
    ph_html = []
    for i, p in enumerate(phases):
        name = p.get("name", f"Phase {i+1}")
        period = p.get("period", "")
        items = p.get("items", [])
        lis = "".join(f'<li>{_rich(it)}</li>' for it in items)
        period_html = f'<div class="ph-period">{esc(period)}</div>' if period else ""
        ph_html.append(
            f'<div class="phase"><div class="ph-marker"><span class="ph-dot"></span></div>'
            f'<div class="ph-card"><div class="ph-name">{esc(name)}</div>{period_html}'
            f'<ul class="ph-items">{lis}</ul></div></div>'
        )
    grid = f'<div class="roadmap" style="--cols:{n}"><div class="rm-line"></div>{"".join(ph_html)}</div>'
    inner = _head(cfg, spec.get("kicker", "ROADMAP"), title) + \
        f'<div class="body">{grid}{_takeaway(spec.get("takeaway"))}</div>' + \
        _footer(cfg, ctx, spec.get("source", ""))
    return _slide(inner)


# --------------------------------------------------------------------------- #
# 9. KPI 대시보드
# --------------------------------------------------------------------------- #

def kpi(cfg, spec, ctx):
    title = spec.get("title", "")
    cards = spec.get("cards", [])
    n = min(max(len(cards), 1), 4)
    cd = []
    for c in cards:
        trend = c.get("trend", "")  # up|down|flat
        tclass = {"up": "up", "down": "down"}.get(trend, "flat")
        arrow = {"up": "▲", "down": "▼", "flat": "▬"}.get(trend, "")
        delta = f'<span class="kpi-delta {tclass}">{arrow} {esc(c.get("delta",""))}</span>' if c.get("delta") else ""
        note = f'<div class="kpi-note">{esc(c.get("note",""))}</div>' if c.get("note") else ""
        cd.append(
            f'<div class="kpi-card"><div class="kpi-l">{esc(c.get("label",""))}</div>'
            f'<div class="kpi-v">{esc(c.get("value",""))}{delta}</div>{note}</div>'
        )
    grid = f'<div class="kpi-grid" style="--cols:{n}">{"".join(cd)}</div>'
    inner = _head(cfg, spec.get("kicker", "KEY METRICS"), title) + \
        f'<div class="body">{grid}{_takeaway(spec.get("takeaway"))}</div>' + \
        _footer(cfg, ctx, spec.get("source", ""))
    return _slide(inner)


# --------------------------------------------------------------------------- #
# 10. 시장규모 (TAM-SAM-SOM / 퍼널)
# --------------------------------------------------------------------------- #

def market_sizing(cfg, spec, ctx):
    title = spec.get("title", "")
    data = spec.get("data", [])  # [(label, value, note)]
    unit = spec.get("unit", "")
    chart = charts.waterfall(cfg, [(d[0], d[1]) for d in data], unit=unit,
                             width=560, height=320)
    notes = []
    for d in data:
        note = d[2] if len(d) > 2 else ""
        notes.append(
            f'<div class="ms-row"><div class="ms-label">{esc(d[0])}</div>'
            f'<div class="ms-val">{charts._fmt(d[1])}{esc(unit)}</div>'
            f'<div class="ms-note">{esc(note)}</div></div>'
        )
    body = (f'<div class="split" style="--vis:50%">'
            f'<div class="split-l"><div class="ms-list">{"".join(notes)}</div></div>'
            f'<div class="split-r">{chart}</div></div>')
    inner = _head(cfg, spec.get("kicker", "MARKET SIZING"), title) + \
        f'<div class="body">{body}{_takeaway(spec.get("takeaway"))}</div>' + \
        _footer(cfg, ctx, spec.get("source", ""))
    return _slide(inner)


# --------------------------------------------------------------------------- #
# 11. 비교 / 벤치마킹 표
# --------------------------------------------------------------------------- #

_RATING = {"high": "●●●", "mid": "●●○", "low": "●○○", "none": "○○○",
           "yes": "✔", "no": "—", "y": "✔", "n": "—"}


def comparison(cfg, spec, ctx):
    title = spec.get("title", "")
    cols = spec.get("columns", [])           # 헤더 라벨(첫 칸 제외)
    rows = spec.get("rows", [])              # {label, cells:[...], highlight?}
    highlight_col = spec.get("highlight_col")  # 강조 열 인덱스(0-base, cells 기준)
    thead = '<th class="rowhead"></th>' + "".join(
        f'<th class="{"hl" if highlight_col==i else ""}">{esc(c)}</th>' for i, c in enumerate(cols)
    )
    trs = []
    for r in rows:
        cells = []
        for i, cell in enumerate(r.get("cells", [])):
            val = cell
            cls = "hl" if highlight_col == i else ""
            if isinstance(cell, str) and cell.lower() in _RATING:
                val = f'<span class="dots">{_RATING[cell.lower()]}</span>'
            cells.append(f'<td class="{cls}">{val if isinstance(val,str) else esc(val)}</td>')
        rowcls = "hl-row" if r.get("highlight") else ""
        trs.append(f'<tr class="{rowcls}"><td class="rowhead">{_rich(r.get("label",""))}</td>{"".join(cells)}</tr>')
    table = f'<table class="cmp"><thead><tr>{thead}</tr></thead><tbody>{"".join(trs)}</tbody></table>'
    inner = _head(cfg, spec.get("kicker", ""), title) + \
        f'<div class="body">{table}{_takeaway(spec.get("takeaway"))}</div>' + \
        _footer(cfg, ctx, spec.get("source", ""))
    return _slide(inner)


# --------------------------------------------------------------------------- #
# 12. 프로세스 플로우
# --------------------------------------------------------------------------- #

def process(cfg, spec, ctx):
    title = spec.get("title", "")
    steps = spec.get("steps", [])
    n = len(steps) or 1
    st = []
    for i, s in enumerate(steps):
        name = s.get("name", "")
        desc = s.get("desc", "")
        desc_html = f'<div class="st-desc">{_rich(desc)}</div>' if desc else ""
        arrow = '<div class="st-arrow">→</div>' if i < n - 1 else ""
        st.append(
            f'<div class="pstep"><div class="st-no">{i+1}</div>'
            f'<div class="st-name">{_rich(name)}</div>{desc_html}</div>{arrow}'
        )
    grid = f'<div class="process">{"".join(st)}</div>'
    inner = _head(cfg, spec.get("kicker", "PROCESS"), title) + \
        f'<div class="body">{grid}{_takeaway(spec.get("takeaway"))}</div>' + \
        _footer(cfg, ctx, spec.get("source", ""))
    return _slide(inner)


# --------------------------------------------------------------------------- #
# 레지스트리
# --------------------------------------------------------------------------- #

SLIDES = {
    "cover": cover,
    "agenda": agenda,
    "section": section,
    "executive_summary": executive_summary,
    "content": content,
    "matrix_2x2": matrix_2x2,
    "mece": mece,
    "roadmap": roadmap,
    "kpi": kpi,
    "market_sizing": market_sizing,
    "comparison": comparison,
    "process": process,
}
