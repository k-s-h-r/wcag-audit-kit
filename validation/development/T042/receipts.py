"""Bind follow-up evidence to the case and viewport in which it was captured."""

from struct import unpack

from collect import digest


EVIDENCE = ('observation.json', 'source-case.json', 'input-events.json', 'browser-requests.json',
            'main-frame-documents.json', 'http-receipts.json', 'before.html', 'after.html',
            'before.png', 'after.png')
ORIGINALS = (*EVIDENCE, 'before.json', 'after.json', 'before.ax.json', 'after.ax.json')
SOURCE_FIELDS = ('case_id', 'state', 'environment', 'page_url', 'graph_digest', 'viewport')


def source_identity(source):
    return {key: source[key] for key in SOURCE_FIELDS}


def original_hashes(area):
    return {name: digest(area / name) for name in ORIGINALS}


def require_image_dimensions(area, viewport):
    expected = (viewport['width'], viewport['height'])
    for name in ('before.png', 'after.png'):
        with (area / name).open('rb') as image:
            header = image.read(24)
        if (len(header) != 24 or header[:16] != b'\x89PNG\r\n\x1a\n\x00\x00\x00\x0dIHDR'
                or unpack('>II', header[16:]) != expected):
            raise ValueError(f'{name}: 画像の寸法と検査票の画面幅が一致しない')
