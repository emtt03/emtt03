#!/usr/bin/env python3
"""Build a GitHub profile README illustration using genuine ASCII and public GitHub stats."""
from __future__ import annotations

import argparse
import calendar
from datetime import date
import json
import os
from pathlib import Path
import re
from urllib.request import Request, urlopen
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[1]
USERNAME = 'emtt03'
BIRTH_DATE = date(2009, 4, 3)

PALETTES = {
    'dark': {
        'bg':'#0d1117', 'panel':'#10161f', 'edge':'#30363d',
        'fg':'#bdc9d7', 'bright':'#cfe6f8', 'muted':'#8296aa',
        'label':'#1793d1', 'accent':'#1793d1', 'lead':'#617181',
        'ascii':'#bac5d2', 'ghost':'#56687a'
    },
    'light': {
        'bg':'#ffffff', 'panel':'#f4f7fb', 'edge':'#ced6df',
        'fg':'#3c5368', 'bright':'#165477', 'muted':'#687b8b',
        'label':'#087fb9', 'accent':'#087fb9', 'lead':'#b1bfcb',
        'ascii':'#3b5267', 'ghost':'#8293a1'
    }
}


def user_stats():
    headers = {'Accept':'application/vnd.github+json', 'User-Agent':'emtt03-profile-readme'}
    token = os.environ.get('GITHUB_TOKEN')
    if token:
        headers['Authorization'] = f'Bearer {token}'
    req = Request(f'https://api.github.com/users/{USERNAME}', headers=headers)
    with urlopen(req, timeout=25) as res:
        user = json.load(res)
    if user.get('login', '').lower() != USERNAME:
        raise ValueError('Unexpected profile received from GitHub API')
    return {field: int(user[field]) for field in ('public_repos', 'followers', 'following')}


def personal_uptime(today=None):
    """Elapsed calendar time from a birth date; NOT device uptime."""
    today = today or date.today()
    years, months, days = today.year - BIRTH_DATE.year, today.month - BIRTH_DATE.month, today.day - BIRTH_DATE.day
    if days < 0:
        prev_year, prev_month = (today.year - 1, 12) if today.month == 1 else (today.year, today.month - 1)
        days += calendar.monthrange(prev_year, prev_month)[1]
        months -= 1
    if months < 0:
        years -= 1
        months += 12
    return f'{years}y {months}m {days}d'


def txt(x, y, value, cls='fg', size=14, extra=''):
    return f'<text x="{x}" y="{y}" class="{cls}" font-size="{size}" {extra}>{escape(str(value))}</text>'


def build(theme, stats):
    c = PALETTES[theme]
    s = [f"""<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630" viewBox="0 0 1200 630" role="img" aria-label="emtt03 GitHub profile. ASCII portrait, system, programming stack, UADY student, and public GitHub stats. English.">
<title>emtt03 / README.md — {theme} mode</title>
<desc>Developer profile inspired by terminal system info layout. Portrait is made of text characters, not an embedded photo. Counters come from the public GitHub API.</desc>
<style>
  .fg {{ fill:{c['fg']}; }}
  .bright {{ fill:{c['bright']}; }}
  .muted {{ fill:{c['muted']}; }}
  .label {{ fill:{c['label']}; }}
  .glyph {{ fill:{c['ascii']}; }}
  text {{ font-family:'DejaVu Sans Mono','Liberation Mono',Consolas,monospace; font-weight:400; }}
</style>
<rect x="0.75" y="0.75" width="1198.5" height="628.5" rx="9" fill="{c['bg']}" stroke="{c['edge']}" stroke-width="1.5"/>
{txt(25, 36, 'emtt03 / README.md', 'muted', 14)}
<rect x="22" y="57" width="1156" height="549" rx="10" fill="{c['panel']}"/>
"""]

    # The original screenshot has only a tall, uninterrupted ASCII portrait in the left column.
    portrait_lines = (ROOT/'assets'/'portrait_ascii.txt').read_text(encoding='utf-8').splitlines()
    if len(portrait_lines) > 27 or any(len(line)>52 for line in portrait_lines):
        raise ValueError('ASCII portrait does not fit designated panel')
    # Keep ASCII exactly, but make X background characters almost invisible for a cleaner face.
    # Center the ASCII portrait block within the left column so it feels symmetric with the interface.
    font_size = 11.8
    line_height = 18.2
    char_step = 6.95
    left_col_x = 34
    left_col_w = 395
    panel_y = 57
    panel_h = 549
    max_chars = max(len(line) for line in portrait_lines)
    content_w = max_chars * char_step
    content_h = (len(portrait_lines) - 1) * line_height
    start_x = left_col_x + max(0, (left_col_w - content_w) / 2)
    start_y = panel_y + max(0, (panel_h - content_h) / 2) + 3

    s.append(f'<g xml:space="preserve" font-family="DejaVu Sans Mono, Liberation Mono, monospace" font-size="{font_size}" font-weight="400" letter-spacing="0.1">')
    for i, line in enumerate(portrait_lines):
        segments = []
        for m in re.finditer(r'X+|[^X]+', line):
            substring = m.group()
            if substring.startswith('X'):
                segments.append(f'<tspan fill="{c["ghost"]}" opacity="0.07">{escape(substring)}</tspan>')
            else:
                segments.append(f'<tspan fill="{c["ascii"]}" opacity="0.97">{escape(substring)}</tspan>')
        y = start_y + i * line_height
        s.append(f'<text x="{start_x:.1f}" y="{y:.1f}" xml:space="preserve">{"".join(segments)}</text>')
    s.append('</g>')

    # Terminal right column: small colored labels, dotted leaders and aligned values.
    s.append(txt(475, 101, 'emtt03@github', 'bright', 16))
    s.append(txt(1155, 101, 'Building, learning, and experimenting.', 'muted', 11, 'text-anchor="end"'))
    s.append(f'<path d="M474 110H1157" stroke="{c["edge"]}" stroke-width="1"/>')

    def row(y, name, value):
        s.append(txt(482, y, name + ':', 'label', 13))
        # Dot leaders are a line pattern, not manually entered character counts.
        s.append(f'<path d="M685 {y-5}H813" stroke="{c["lead"]}" stroke-width="1.15" stroke-dasharray="1.5 5.6"/>')
        s.append(txt(830, y, value, 'bright', 12.6))

    for y, title, value in [
        (141, 'OS', 'Arch Linux, Windows 11, iOS, Android 14'),
        (164, 'Uptime', personal_uptime()),
        (187, 'Host', 'Lenovo ThinkPad L14 Gen 2'),
        (210, 'CPU', 'Intel Core i7-1165G7'),
        (233, 'WM', 'Hyprland'),
        (256, 'Editor', 'VSCodium')
    ]:
        row(y, title, value)
    s.append(f'<path d="M475 272H1157" stroke="{c["edge"]}"/>')
    for y, title, value in [
        (294, 'Languages.Programming', 'Python, JavaScript'),
        (317, 'Languages.Web', 'HTML, CSS'),
        (340, 'Tools.AI', 'Codex, Claude Code'),
        (363, 'Tools.Hardware', 'Arduino, Raspberry Pi, Git'),
        (386, 'Web.Hosting', 'Cloudflare Pages')
    ]:
        row(y, title, value)
    s.append(f'<path d="M475 402H1157" stroke="{c["edge"]}"/>')
    for y, title, value in [
        (424, 'Role', 'UADY Student, Linux Enthusiast'),
        (447, 'Focus', 'Frontend Developer in Progress'),
        (470, 'Location', 'Merida, Yucatan, Mexico'),
        (493, 'Hobbies.Software', 'Linux, Web development, Gaming'),
        (516, 'Hobbies.Other', 'Electronics, Music')
    ]:
        row(y, title, value)
    s.append(f'<path d="M475 534H1157" stroke="{c["edge"]}"/>')
    s.append(txt(480, 556, 'GitHub Stats', 'label', 14))
    s.append(f'<path d="M601 551H1157" stroke="{c["edge"]}"/>')
    if stats is None:
        s.append(txt(482, 585, 'Awaiting first GitHub Actions sync — no sample numbers', 'muted', 13))
    else:
        s.append(txt(482, 584, 'Repos:', 'label', 12.8))
        s.append(txt(568, 584, stats['public_repos'], 'bright', 12.8))
        s.append(txt(693, 584, 'Followers:', 'label', 12.8))
        s.append(txt(806, 584, stats['followers'], 'bright', 12.8))
        s.append(txt(939, 584, 'Following:', 'label', 12.8))
        s.append(txt(1060, 584, stats['following'], 'bright', 12.8))
    s.append('</svg>')
    return '\n'.join(s)+'\n'


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument('--offline', action='store_true', help='skip API, leave counters pending')
    args = cli.parse_args()
    stats = None if args.offline else user_stats()
    (ROOT/'assets').mkdir(exist_ok=True)
    for theme in PALETTES:
        (ROOT/'assets'/f'{theme}_mode.svg').write_text(build(theme, stats), encoding='utf-8')
    print('Generated SVG profile in both themes; ' + ('stats pending' if stats is None else 'real GitHub counters'))

if __name__ == '__main__':
    main()
