"""인라인 SVG 차트. 외부 라이브러리 없이 문자열 SVG 를 생성한다.

모든 함수는 (cfg, ...) 를 받아 SVG 문자열을 반환한다. 색은 테마 series 를 사용.
숫자 라벨은 한국어 덱 관례에 맞춰 그대로 문자열로 넘길 수 있다.
"""

from __future__ import annotations

import html
from .theme import series_color


def _esc(s) -> str:
    return html.escape(str(s), quote=True)


def _fmt(v: float) -> str:
    """1234.0 -> '1,234', 12.5 -> '12.5'."""
    if isinstance(v, (int, float)) and float(v).is_integer():
        return f"{int(v):,}"
    return f"{v:,.1f}"


def bar_chart(cfg, data, *, width=520, height=300, value_labels=True,
              unit="", horizontal=False, color_index=0, highlight=None):
    """data: [(label, value), ...]. highlight: 강조할 label(선택)."""
    ink = cfg["color"]["ink"]
    muted = cfg["color"]["muted"]
    hair = cfg["color"]["hairline"]
    base = series_color(cfg, color_index)
    accent = cfg["color"]["accent"]
    faint = cfg["color"]["faint"]
    vals = [v for _, v in data]
    vmax = max(vals + [0]) or 1
    pad_l, pad_r, pad_t, pad_b = 8, 8, 14, 26
    n = len(data)
    svg = [f'<svg viewBox="0 0 {width} {height}" width="{width}" height="{height}" '
           f'font-family="var(--font-sans)" role="img">']
    if horizontal:
        row_h = (height - pad_t - pad_b) / max(n, 1)
        bar_h = min(row_h * 0.6, 34)
        label_w = 128
        plot_w = width - label_w - 70
        for i, (label, v) in enumerate(data):
            y = pad_t + i * row_h + (row_h - bar_h) / 2
            w = plot_w * (v / vmax)
            fill = accent if (highlight and label == highlight) else base
            svg.append(f'<text x="{label_w-10}" y="{y+bar_h/2+4}" text-anchor="end" '
                       f'font-size="13" fill="{ink}">{_esc(label)}</text>')
            svg.append(f'<rect x="{label_w}" y="{y:.1f}" width="{max(w,1):.1f}" '
                       f'height="{bar_h:.1f}" rx="2" fill="{fill}"/>')
            if value_labels:
                svg.append(f'<text x="{label_w+w+8:.1f}" y="{y+bar_h/2+4:.1f}" '
                           f'font-size="13" font-weight="600" fill="{ink}">'
                           f'{_fmt(v)}{_esc(unit)}</text>')
    else:
        col_w = (width - pad_l - pad_r) / max(n, 1)
        bar_w = min(col_w * 0.56, 64)
        plot_h = height - pad_t - pad_b
        svg.append(f'<line x1="{pad_l}" y1="{pad_t+plot_h}" x2="{width-pad_r}" '
                   f'y2="{pad_t+plot_h}" stroke="{hair}" stroke-width="1"/>')
        for i, (label, v) in enumerate(data):
            cx = pad_l + col_w * (i + 0.5)
            h = plot_h * (v / vmax)
            y = pad_t + plot_h - h
            fill = accent if (highlight and label == highlight) else base
            svg.append(f'<rect x="{cx-bar_w/2:.1f}" y="{y:.1f}" width="{bar_w:.1f}" '
                       f'height="{max(h,1):.1f}" rx="2" fill="{fill}"/>')
            if value_labels:
                svg.append(f'<text x="{cx:.1f}" y="{y-6:.1f}" text-anchor="middle" '
                           f'font-size="13" font-weight="600" fill="{ink}">'
                           f'{_fmt(v)}{_esc(unit)}</text>')
            svg.append(f'<text x="{cx:.1f}" y="{pad_t+plot_h+18:.1f}" text-anchor="middle" '
                       f'font-size="12.5" fill="{muted}">{_esc(label)}</text>')
    svg.append('</svg>')
    return "".join(svg)


def waterfall(cfg, data, *, width=560, height=300, unit=""):
    """TAM→SAM→SOM 등 감소/증가 흐름. data: [(label, value, kind)].
    kind: 'total'(절대막대) | 'down'(감소) | 'up'(증가). 단순 total 시퀀스도 지원."""
    ink = cfg["color"]["ink"]
    muted = cfg["color"]["muted"]
    hair = cfg["color"]["hairline"]
    accent = cfg["color"]["accent"]
    soft = cfg["color"]["accent_soft"]
    vals = [v for _, v, *_ in data]
    vmax = max(vals + [0]) or 1
    pad_t, pad_b = 16, 26
    n = len(data)
    col_w = (width - 16) / max(n, 1)
    bar_w = min(col_w * 0.6, 90)
    plot_h = height - pad_t - pad_b
    svg = [f'<svg viewBox="0 0 {width} {height}" width="{width}" height="{height}" '
           f'font-family="var(--font-sans)" role="img">']
    svg.append(f'<line x1="8" y1="{pad_t+plot_h}" x2="{width-8}" y2="{pad_t+plot_h}" '
               f'stroke="{hair}" stroke-width="1"/>')
    for i, item in enumerate(data):
        label, v = item[0], item[1]
        kind = item[2] if len(item) > 2 else "total"
        cx = 8 + col_w * (i + 0.5)
        h = plot_h * (v / vmax)
        y = pad_t + plot_h - h
        fill = accent if kind in ("total",) else soft
        stroke = "none" if kind == "total" else accent
        svg.append(f'<rect x="{cx-bar_w/2:.1f}" y="{y:.1f}" width="{bar_w:.1f}" '
                   f'height="{max(h,1):.1f}" rx="2" fill="{fill}" stroke="{stroke}" '
                   f'stroke-width="1"/>')
        svg.append(f'<text x="{cx:.1f}" y="{y-6:.1f}" text-anchor="middle" '
                   f'font-size="14" font-weight="700" fill="{ink}">{_fmt(v)}{_esc(unit)}</text>')
        svg.append(f'<text x="{cx:.1f}" y="{pad_t+plot_h+18:.1f}" text-anchor="middle" '
                   f'font-size="12.5" fill="{muted}">{_esc(label)}</text>')
        if i < n - 1:
            nxt = pad_t + plot_h - plot_h * (data[i+1][1] / vmax)
            x2 = 8 + col_w * (i + 1.5) - bar_w / 2
            svg.append(f'<line x1="{cx+bar_w/2:.1f}" y1="{y:.1f}" x2="{x2:.1f}" '
                       f'y2="{y:.1f}" stroke="{hair}" stroke-dasharray="3 3"/>')
    svg.append('</svg>')
    return "".join(svg)


def line_chart(cfg, series, *, width=560, height=300, unit="", labels=None):
    """series: [(name, [v0, v1, ...]), ...]. labels: x축 라벨 리스트."""
    ink = cfg["color"]["ink"]
    muted = cfg["color"]["muted"]
    hair = cfg["color"]["hairline"]
    allv = [v for _, ys in series for v in ys]
    vmax = max(allv + [0]) or 1
    vmin = min(allv + [0])
    span = (vmax - vmin) or 1
    pad_l, pad_r, pad_t, pad_b = 12, 60, 16, 26
    m = max((len(ys) for _, ys in series), default=1)
    plot_w = width - pad_l - pad_r
    plot_h = height - pad_t - pad_b
    def X(i): return pad_l + plot_w * (i / max(m - 1, 1))
    def Y(v): return pad_t + plot_h * (1 - (v - vmin) / span)
    svg = [f'<svg viewBox="0 0 {width} {height}" width="{width}" height="{height}" '
           f'font-family="var(--font-sans)" role="img">']
    svg.append(f'<line x1="{pad_l}" y1="{pad_t+plot_h}" x2="{pad_l+plot_w}" '
               f'y2="{pad_t+plot_h}" stroke="{hair}"/>')
    for si, (name, ys) in enumerate(series):
        col = series_color(cfg, si)
        pts = " ".join(f"{X(i):.1f},{Y(v):.1f}" for i, v in enumerate(ys))
        svg.append(f'<polyline points="{pts}" fill="none" stroke="{col}" '
                   f'stroke-width="2.5" stroke-linejoin="round"/>')
        for i, v in enumerate(ys):
            svg.append(f'<circle cx="{X(i):.1f}" cy="{Y(v):.1f}" r="3" fill="{col}"/>')
        lv = ys[-1]
        svg.append(f'<text x="{X(len(ys)-1)+8:.1f}" y="{Y(lv)+4:.1f}" font-size="12.5" '
                   f'font-weight="600" fill="{col}">{_esc(name)}</text>')
    if labels:
        for i, lab in enumerate(labels):
            svg.append(f'<text x="{X(i):.1f}" y="{pad_t+plot_h+18:.1f}" text-anchor="middle" '
                       f'font-size="12" fill="{muted}">{_esc(lab)}</text>')
    svg.append('</svg>')
    return "".join(svg)


def donut(cfg, data, *, width=260, height=260, unit="%", center_label=None):
    """data: [(label, value), ...]. 도넛 + 범례 없이 조각 라벨."""
    import math
    ink = cfg["color"]["ink"]
    muted = cfg["color"]["muted"]
    total = sum(v for _, v in data) or 1
    cx, cy = width / 2, height / 2
    r, rin = min(cx, cy) - 6, (min(cx, cy) - 6) * 0.62
    svg = [f'<svg viewBox="0 0 {width} {height}" width="{width}" height="{height}" '
           f'font-family="var(--font-sans)" role="img">']
    ang = -math.pi / 2
    for i, (label, v) in enumerate(data):
        frac = v / total
        a2 = ang + frac * 2 * math.pi
        large = 1 if frac > 0.5 else 0
        x1, y1 = cx + r * math.cos(ang), cy + r * math.sin(ang)
        x2, y2 = cx + r * math.cos(a2), cy + r * math.sin(a2)
        xi1, yi1 = cx + rin * math.cos(a2), cy + rin * math.sin(a2)
        xi2, yi2 = cx + rin * math.cos(ang), cy + rin * math.sin(ang)
        col = series_color(cfg, i)
        svg.append(f'<path d="M{x1:.1f},{y1:.1f} A{r:.1f},{r:.1f} 0 {large} 1 '
                   f'{x2:.1f},{y2:.1f} L{xi1:.1f},{yi1:.1f} A{rin:.1f},{rin:.1f} 0 '
                   f'{large} 0 {xi2:.1f},{yi2:.1f} Z" fill="{col}"/>')
        mid = (ang + a2) / 2
        lx, ly = cx + (r + 14) * math.cos(mid), cy + (r + 14) * math.sin(mid)
        anchor = "start" if math.cos(mid) >= 0 else "end"
        svg.append(f'<text x="{lx:.1f}" y="{ly:.1f}" text-anchor="{anchor}" '
                   f'font-size="12" fill="{muted}">{_esc(label)} '
                   f'<tspan font-weight="700" fill="{ink}">{_fmt(v)}{_esc(unit)}</tspan></text>')
        ang = a2
    if center_label:
        svg.append(f'<text x="{cx}" y="{cy+6}" text-anchor="middle" font-size="20" '
                   f'font-weight="700" fill="{ink}">{_esc(center_label)}</text>')
    svg.append('</svg>')
    return "".join(svg)
