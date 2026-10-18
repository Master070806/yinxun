"""Offline checks: data integrity, required assets, HTTP access boundaries."""
import ast
import json
import math
from pathlib import Path
import re
import sys
import threading
from urllib.request import build_opener, ProxyHandler, Request
from urllib.error import HTTPError

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from serve import Handler, ThreadingHTTPServer


def main():
    for name in ['serve.py']:
        ast.parse((ROOT / name).read_text(encoding='utf-8-sig'))
    data = json.loads((ROOT / 'web/map-data.json').read_text(encoding='utf-8-sig'))
    points = data['points']
    assert len(points) == 5453, 'Update data version and checks deliberately if replacing the snapshot'
    assert len({p['name'] for p in points}) == len(points)
    for p in points:
        assert all(isinstance(p[k], (float, int)) and math.isfinite(p[k]) for k in ['x', 'y'])
        assert re.fullmatch(r'#[0-9a-fA-F]{6}', p['color'])
    assert data['license'] == 'CC BY-SA 4.0'
    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    client = build_opener(ProxyHandler({}))
    base = f'http://127.0.0.1:{server.server_port}'
    try:
        for path in ['/', '/home.css', '/map.html', '/map.js', '/map.css', '/map-data.json', '/style.css', '/index.html',
                     '/genreguessr', '/genreguessr/', '/genreguessr.html', '/genreguessr.css', '/genreguessr.js',
                     '/genre-cluster.js', '/genre-cluster.css', '/about', '/about/', '/about.html', '/about.css',
                     '/genrerace', '/genrerace/', '/genrerace.html', '/genrerace.css', '/genrerace.js',
                     '/multiplayer-genreguessr', '/multiplayer-genreguessr/', '/multiplayer-genreguessr.html',
                     '/multiplayer-genrerace', '/multiplayer-genrerace/', '/multiplayer-genrerace.html',
                     '/multiplayer.js', '/multiplayer.css', '/i18n.js', '/i18n.css', '/i18n-messages.js', '/genre-names.js', '/genre-ui.js']:
            with client.open(base + path) as r:
                body = r.read()
                assert r.status == 200 and len(body) > 0, path
                if path in ['/', '/index.html']:
                    assert body == (ROOT / 'web/index.html').read_bytes()
                if path in ['/genreguessr', '/genreguessr/', '/genreguessr.html']:
                    assert body == (ROOT / 'web/genreguessr.html').read_bytes()
                if path in ['/about', '/about/', '/about.html']:
                    assert body == (ROOT / 'web/about.html').read_bytes()
                if path in ['/genrerace', '/genrerace/', '/genrerace.html']:
                    assert body == (ROOT / 'web/genrerace.html').read_bytes()
                for mode in ('genreguessr', 'genrerace'):
                    if path in [f'/multiplayer-{mode}', f'/multiplayer-{mode}/', f'/multiplayer-{mode}.html']:
                        assert body == (ROOT / f'web/multiplayer-{mode}.html').read_bytes()
        for path in ['/README.md', '/.env', '/.git/config', '/web/../serve.py', '/catalog.json', '/app.js', '/audio/example.mp3', '/genreguessr-demo.json', '/.cache/genreguessr/catalog.json', '/engine/game.py']:
            try:
                client.open(base + path)
            except HTTPError as e:
                assert e.code == 404, path
            else:
                raise AssertionError(f'Unexpected public path: {path}')
        with client.open(Request(base + '/map-data.json', headers={'Range': 'bytes=0-9'})) as r:
            assert r.status == 206 and len(r.read()) == 10
        try:
            client.open(Request(base + '/map-data.json', headers={'Range': 'bytes=999999999-'}))
        except HTTPError as e:
            assert e.code == 416
        else:
            raise AssertionError('Out-of-range request should fail')
    finally:
        server.shutdown()
        server.server_close()
        thread.join()
    print('PASS: Python syntax, map integrity, HTTP assets and access boundaries')


if __name__ == '__main__':
    main()
