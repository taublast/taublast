"""Draws a pin card (SVG) for every GitHub repo linked from README.md into cards/<owner>-<repo>.svg and points
the README's card images at them. No outside card service: the repo data comes from the GitHub API."""
import json, os, re, urllib.request
from xml.sax.saxutils import escape

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
README = os.path.join(ROOT, 'README.md')
OUT = os.path.join(ROOT, 'cards')
TOKEN = os.environ.get('GITHUB_TOKEN') or os.environ.get('GH_TOKEN')

FONT = "'Segoe UI',Ubuntu,'Helvetica Neue',Sans-Serif"
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


def card(d):
    # title and description only: no language, stars or forks row
    title = escape(d['name'])
    desc = [escape(x) for x in wrap(d.get('description') or '')]
    desc_svg = ''.join(f'<tspan x="25" dy="{0 if i == 0 else 18}">{t}</tspan>' for i, t in enumerate(desc))
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="400" height="104" viewBox="0 0 400 104" role="img" aria-label="{title}">\n'
            f'<style>.t{{font:600 18px {FONT};fill:#58a6ff}}.d{{font:400 13px {FONT};fill:#c9d1d9}}</style>\n'
            f'<rect x="0.5" y="0.5" rx="10" width="399" height="103" fill="#0d1117" stroke="#30363d"/>\n'
            f'<svg x="25" y="21" width="16" height="16" viewBox="0 0 16 16"><path fill="#8b949e" d="{BOOK}"/></svg>\n'
            f'<text x="49" y="35" class="t">{title}</text>\n'
            f'<text x="25" y="63" class="d">{desc_svg}</text>\n</svg>\n')


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
