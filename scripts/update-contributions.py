"""Render the verified contribution snapshot into the profile banner.

Run after updating assets/contributions.json with a new verified snapshot:
    python3 scripts/update-contributions.py
The public unauthenticated GitHub calendar omits private contributions; do not
replace this snapshot with public-only counts or add account credentials here.
"""
from datetime import date, timedelta
from pathlib import Path
from html import escape
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / 'assets/contributions.json'
BANNER = ROOT / 'assets/revive-wordmark.svg'
README = ROOT / 'README.md'
PALETTE = ['#111C2B', '#193A59', '#296893', '#4C9CCA', '#A1D9F2']
START_MARKER = '    <!-- Contribution snapshot: start -->'
END_MARKER = '    <!-- Contribution snapshot: end -->'


def render(data):
    days = data['days']
    assert days and sum(d['count'] for d in days) == data['total']
    dates = [date.fromisoformat(d['date']) for d in days]
    assert dates == sorted(set(dates))
    assert all(isinstance(d['count'], int) and d['count'] >= 0 for d in days)
    assert all(b - a == timedelta(days=1) for a, b in zip(dates, dates[1:]))
    assert dates[-1] == date.fromisoformat(data['captured'])
    start = dates[0] - timedelta(days=(dates[0].weekday() + 1) % 7)
    weeks = (dates[-1] - start).days // 7 + 1
    assert 52 <= weeks <= 54
    step = 1272 / weeks
    size = step - 6
    x0, y0 = 192, 524
    font = 'Arial, Helvetica, sans-serif'
    lines = [
        START_MARKER,
        '    <g id="contributions" font-family="' + font + '">',
        '      <title>GitHub activity: ' + str(data['total']) + ' contributions</title>',
        '      <rect x="80" y="422" width="1440" height="336" rx="18" fill="#060C19" fill-opacity=".9" stroke="#9CBBEF" stroke-opacity=".12"/>',
        f'      <text x="112" y="468" fill="#EAF2FF" font-size="25" font-weight="600">{data["total"]} contributions in the last year</text>',
        f'      <text x="1488" y="468" text-anchor="end" fill="#8FA5C6" font-size="18">{date.fromisoformat(data["captured"]).strftime("%d.%m.%Y")}</text>',
    ]
    previous = None
    for week in range(weeks):
        day = start + timedelta(days=week * 7)
        month = (day.year, day.month)
        if month != previous:
            label = day.strftime('%b')
            lines.append(f'      <text x="{x0 + week * step:.2f}" y="507" fill="#9BAEC9" font-size="19">{label}</text>')
            previous = month
    for row, label in [(1, 'Mon'), (3, 'Wed'), (5, 'Fri')]:
        lines.append(f'      <text x="171" y="{y0 + row * 24 + 15}" text-anchor="end" fill="#8FA5C6" font-size="18">{label}</text>')
    for item, day in zip(days, dates):
        offset = (day - start).days
        week, row = divmod(offset, 7)
        count = item['count']
        level = 0 if count == 0 else min(4, (count - 1) // 3 + 1)
        label = escape(f'{item["date"]}: {count} contributions')
        lines.append(f'      <rect x="{x0 + week * step:.2f}" y="{y0 + row * 24}" width="{size:.2f}" height="18" rx="3" fill="{PALETTE[level]}" data-date="{item["date"]}" data-count="{count}"><title>{label}</title></rect>')
    lines.append('      <text x="112" y="727" fill="#7D94B6" font-size="17">GitHub · revivea0</text>')
    lines.append('      <text x="1272" y="727" text-anchor="end" fill="#8FA5C6" font-size="17">Less</text>')
    for i, color in enumerate(PALETTE):
        lines.append(f'      <rect x="{1284 + i * 25}" y="712" width="18" height="18" rx="3" fill="{color}"/>')
    lines.append('      <text x="1413" y="727" fill="#8FA5C6" font-size="17">More</text>')
    lines.extend(['    </g>', END_MARKER])
    return '\n'.join(lines)


def main():
    data = json.loads(DATA.read_text())
    svg = BANNER.read_text()
    graph = render(data)
    if START_MARKER in svg:
        start = svg.index(START_MARKER)
        end = svg.index(END_MARKER) + len(END_MARKER)
        svg = svg[:start] + graph + svg[end:]
    else:
        svg = svg.replace('viewBox="0 0 1600 480"', 'viewBox="0 0 1600 790"')
        svg = svg.replace('<rect width="1600" height="480"', '<rect width="1600" height="790"')
        svg = svg.replace('width="1599" height="479"', 'width="1599" height="789"')
        marker = '    <rect x=".5" y=".5"'
        assert marker in svg
        svg = svg.replace(marker, graph + '\n' + marker)
    description = ('revivea — frontend, full stack, web systems. Звёздное небо и календарь GitHub: '
                   + str(data['total']) + ' contributions. Снимок на ' + data['captured'] + '.')
    svg = re.sub(r'<desc id="desc">.*?</desc>', '<desc id="desc">' + escape(description) + '</desc>', svg)
    BANNER.write_text(svg)
    version = hashlib.sha256(svg.encode()).hexdigest()[:10]
    readme, count = re.subn(r'revive-wordmark\.svg\?v=[a-z0-9]+', 'revive-wordmark.svg?v=' + version, README.read_text())
    assert count == 1
    readme = readme.replace('alt="revivea — звёздное небо, frontend, full stack и веб-системы"', 'alt="revivea — звёздное небо, календарь активности GitHub, frontend и full stack"')
    README.write_text(readme)
    print(f'Rendered {len(data["days"])} days, {data["total"]} contributions; banner version {version}')


if __name__ == '__main__':
    main()
