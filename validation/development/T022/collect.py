import argparse
from collections import deque
from html.parser import HTMLParser
import json
from pathlib import Path
import subprocess
import sys
from urllib.parse import urljoin, urlsplit
from urllib.request import urlopen


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hrefs = []

    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        if tag == 'a' and 'href' in attrs:
            self.hrefs.append(attrs['href'])


parser = argparse.ArgumentParser(description='Collect pages discoverable from the supplied process entry URLs.')
parser.add_argument('--cli', type=Path, required=True)
parser.add_argument('--out', type=Path, required=True)
parser.add_argument('urls', nargs='+')
args = parser.parse_args()
args.out.mkdir(parents=True, exist_ok=False)
pending = deque(enumerate(args.urls, 1))
seen = {}
while pending:
    index, url = pending.popleft()
    if url in seen:
        continue
    with urlopen(url, timeout=10) as response:
        links = Links()
        links.feed(response.read().decode())
    destination = args.out / f'{index}-{len(seen)+1:02}'
    destination.mkdir()
    seen[url] = destination.name
    for href in links.hrefs:
        link = urljoin(url, href)
        if link.startswith(args.urls[index-1]) and not urlsplit(link).fragment:
            pending.append((index, link))
    command = [sys.executable, str(args.cli), 'page-audit', '--url', url, '--out', str(destination / 'page')]
    for phase, flags in (
        ('initial', ['--level', 'AA', '--mode', 'machine', '--screenshots', 'initial', '--initial-only']),
        ('explore', ['--resume', '--quick-explore']),
    ):
        with (destination / (phase + '.log')).open('w') as log:
            result = subprocess.run(command + flags, stdout=log, stderr=subprocess.STDOUT, timeout=240)
        if result.returncode:
            break
    print(url, result.returncode, flush=True)
    (args.out / 'urls.json').write_text(json.dumps(seen, indent=2))
