"""Draws a pin card (SVG) for every GitHub repo linked from README.md into cards/<owner>-<repo>.svg and points
the README's card images at them. No outside card service: the repo data comes from the GitHub API."""
import json, os, re, urllib.request
from xml.sax.saxutils import escape

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
README = os.path.join(ROOT, 'README.md')
OUT = os.path.join(ROOT, 'cards')
TOKEN = os.environ.get('GITHUB_TOKEN') or os.environ.get('GH_TOKEN')

LANG_COLORS = {'C#': '#178600', 'Rust': '#dea584', 'TypeScript': '#3178c6', 'JavaScript': '#f1e05a',
               'Python': '#3572A5', 'HTML': '#e34c26', 'Kotlin': '#A97BFF', 'Swift': '#F05138', 'C++': '#f34b7d',
               'Batchfile': '#C1F12E', 'PowerShell': '#012456'}

FONT = "'Segoe UI',Ubuntu,'Helvetica Neue',Sans-Serif"
STAR = ('M8 .25a.75.75 0 01.673.418l1.882 3.815 4.21.612a.75.75 0 01.416 1.279l-3.046 2.97.719 4.192a.75.75 0 '
        '01-1.088.791L8 12.347l-3.766 1.98a.75.75 0 01-1.088-.79l.72-4.194L.818 6.374a.75.75 0 01.416-1.28l4.21-.611'
        'L7.327.668A.75.75 0 018 .25z')
FORK = ('M5 3.25a.75.75 0 11-1.5 0 .75.75 0 011.5 0zm0 2.122a2.25 2.25 0 10-1.5 0v.878A2.25 2.25 0 005.75 8.5h1.5v2.128'
        'a2.251 2.251 0 101.5 0V8.5h1.5a2.25 2.25 0 002.25-2.25v-.878a2.25 2.25 0 10-1.5 0v.878a.75.75 0 01-.75.75h-4.5'
        'A.75.75 0 015 6.25v-.878zm3.75 7.378a.75.75 0 11-1.5 0 .75.75 0 011.5 0zm3-8.75a.75.75 0 100-1.5.75.75 0 000 1.5z')
BOOK = ('M2 2.5A2.5 2.5 0 014.5 0h8.75a.75.75 0 01.75.75v12.5a.75.75 0 01-.75.75h-2.5a.75.75 0 110-1.5h1.75v-2h-8a1 1 0 '
        '00-.714 1.7.75.75 0 01-1.072 1.05A2.495 2.495 0 012 11.5v-9zm10.5-1V9h-8c-.356 0-.694.074-1 .208V2.5a1 1 0 '
        '011-1h8zM5 12.25v3.25a.25.25 0 00.4.2l1.45-1.087a.25.25 0 01.3 0L8.6 15.7a.25.25 0 00.4-.2v-3.25a.25.25 0 '
        '00-.25-.25h-3.5a.25.25 0 00-.25.25z')


def repo(full):
    req = urllib.request.Request('https://api.github.com/repos/' + full,
                                 headers={'Accept': 'application/vnd.github+json', 'User-Agent': 'profile-cards'})
    if TOKEN:
        req.add_header('Authorization', 'Bearer ' + TOKEN)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def wrap(text, width=54, lines=2):
    words, out, cur = (text or '').split(), [], ''
    used = 0
    for w in words:
        if cur and len(cur) + 1 + len(w) > width:
            out.append(cur)
            cur = ''
            if len(out) == lines:
                break
        cur = (cur + ' ' + w).strip()
        used += 1
    if len(out) < lines and cur:
        out.append(cur)
    if used < len(words) or (len(out) == lines and cur and cur not in out):
        out[-1] = out[-1].rstrip('.,;: ') + '…'
    return out[:lines]


def kfmt(n):
    return f'{n / 1000:.1f}k' if n >= 1000 else str(n)


def card(d):
    title = escape(d['name'])
    desc = [escape(x) for x in wrap(d.get('description') or '')]
    lang = d.get('language') or ''
    desc_svg = ''.join(f'<tspan x="25" dy="{0 if i == 0 else 18}">{t}</tspan>' for i, t in enumerate(desc))
    x, meta = 25, ''
    if lang:
        meta += (f'<circle cx="{x + 6}" cy="-4" r="6" fill="{LANG_COLORS.get(lang, "#8b949e")}"/>'
                 f'<text x="{x + 17}" y="0" class="m">{escape(lang)}</text>')
        x += 17 + 7 * len(lang) + 18
    for icon, value in ((STAR, d['stargazers_count']), (FORK, d['forks_count'])):
        meta += (f'<svg x="{x}" y="-12" width="16" height="16" viewBox="0 0 16 16"><path fill="#8b949e" d="{icon}"/></svg>'
                 f'<text x="{x + 21}" y="0" class="m">{kfmt(value)}</text>')
        x += 21 + 7 * len(kfmt(value)) + 18
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="400" height="120" viewBox="0 0 400 120" role="img" aria-label="{title}">\n'
            f'<style>.t{{font:600 18px {FONT};fill:#58a6ff}}.d{{font:400 13px {FONT};fill:#c9d1d9}}.m{{font:400 12px {FONT};fill:#c9d1d9}}</style>\n'
            f'<rect x="0.5" y="0.5" rx="10" width="399" height="119" fill="#0d1117" stroke="#30363d"/>\n'
            f'<svg x="25" y="21" width="16" height="16" viewBox="0 0 16 16"><path fill="#8b949e" d="{BOOK}"/></svg>\n'
            f'<text x="49" y="35" class="t">{title}</text>\n'
            f'<text x="25" y="63" class="d">{desc_svg}</text>\n'
            f'<g transform="translate(0,103)">{meta}</g>\n</svg>\n')


def main():
    os.makedirs(OUT, exist_ok=True)
    text = open(README, encoding='utf-8', newline='').read()
    repos = sorted(set(re.findall(r'<a href="https://github\.com/([\w.-]+/[\w.-]+)"', text)))
    for full in repos:
        owner, name = full.split('/')
        path = f'cards/{owner}-{name}.svg'
        open(os.path.join(ROOT, path), 'w', encoding='utf-8', newline='\n').write(card(repo(full)))
        # the card image right after this repo's link shows the local card
        text = re.sub(r'(<a href="https://github\.com/' + re.escape(full) + r'"[^>]*>\s*<img src=")[^"]*(")',
                      lambda m: m.group(1) + path + m.group(2), text)
        print('card', path)
    open(README, 'w', encoding='utf-8', newline='').write(text)


if __name__ == '__main__':
    main()
