import html


def _split_lines(text: str, max_line_len: int, max_lines: int) -> list[str]:
    words = [word for word in text.strip().split() if word]
    if not words:
        return []

    lines: list[str] = []
    current: list[str] = []
    current_len = 0

    for word in words:
        extra = len(word) if not current else len(word) + 1
        if current and current_len + extra > max_line_len:
            lines.append(" ".join(current))
            if len(lines) >= max_lines:
                return lines
            current = [word]
            current_len = len(word)
        else:
            current.append(word)
            current_len += extra

    if current and len(lines) < max_lines:
        lines.append(" ".join(current))

    return lines


def build_fallback_cover_svg(title: str | None, author: str | None) -> bytes:
    safe_title = html.escape((title or "Untitled").strip() or "Untitled")
    safe_author = html.escape((author or "Unknown Author").strip() or "Unknown Author")

    title_lines = _split_lines(safe_title, max_line_len=20, max_lines=4)
    if not title_lines:
        title_lines = ["Untitled"]

    title_y = 165
    line_height = 26
    title_svg = "\n".join(
        f'<text x="60" y="{title_y + i * line_height}" '
        'font-family="Segoe UI, Arial, sans-serif" font-size="22" font-weight="700" '
        'fill="#111827">'
        f"{line}</text>"
        for i, line in enumerate(title_lines)
    )

    author_line = _split_lines(safe_author, max_line_len=28, max_lines=1)
    author_value = author_line[0] if author_line else "Unknown Author"

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="600" height="900" viewBox="0 0 600 900">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#e2e8f0"/>
      <stop offset="100%" stop-color="#cbd5e1"/>
    </linearGradient>
  </defs>
  <rect width="600" height="900" fill="url(#bg)"/>
  <rect x="40" y="40" width="520" height="820" rx="28" fill="#f8fafc" stroke="#cbd5e1" stroke-width="4"/>
  <rect x="60" y="80" width="480" height="54" rx="12" fill="#0f172a"/>
  <text x="80" y="115" font-family="Segoe UI, Arial, sans-serif" font-size="24" font-weight="700" fill="#f8fafc">Book</text>
  {title_svg}
  <line x1="60" y1="740" x2="540" y2="740" stroke="#cbd5e1" stroke-width="2"/>
  <text x="60" y="786" font-family="Segoe UI, Arial, sans-serif" font-size="28" fill="#475569">{author_value}</text>
</svg>"""
    return svg.encode("utf-8")

