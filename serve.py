"""Loopback-only music game APIs and explicitly allowlisted website assets."""
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from threading import Lock
from urllib.parse import urlsplit
import json
import mimetypes
import re

ROOT = Path(__file__).resolve().parent
ASSETS = {'/', '/index.html', '/home.css', '/style.css', '/map.html', '/map.css',
          '/map.js', '/map-data.json', '/genreguessr', '/genreguessr/',
          '/genreguessr.html', '/genreguessr.css', '/genreguessr.js',
          '/genre-cluster.js', '/genre-cluster.css',
          '/genrerace', '/genrerace/', '/genrerace.html', '/genrerace.css', '/genrerace.js',
          '/about', '/about/', '/about.html', '/about.css'}
ALIASES = {'/': 'index.html', '/genreguessr': 'genreguessr.html',
           '/genreguessr/': 'genreguessr.html',
           '/genrerace': 'genrerace.html', '/genrerace/': 'genrerace.html',
           '/about': 'about.html', '/about/': 'about.html'}


class Handler(BaseHTTPRequestHandler):
    game_service = None
    race_service = None
    audio_store = None
    initialization_lock = Lock()

    def services(self):
        cls = type(self)
        with cls.initialization_lock:
            if cls.game_service is None:
                from engine.catalog import Catalog
                from engine.game import GameService
                cls.game_service = GameService(Catalog())
            if cls.audio_store is None:
                from engine.audio import AudioStore
                cls.audio_store = AudioStore()
        return cls.game_service, cls.audio_store

    def races(self):
        service, _ = self.services()
        cls = type(self)
        with cls.initialization_lock:
            if (cls.race_service is None or cls.race_service.catalog is not service.catalog
                    or cls.race_service.provider is not service.provider):
                from engine.race import RaceService
                cls.race_service = RaceService(service.catalog, service.provider)
            return cls.race_service

    def json_response(self, status, payload, body=True):
        data = json.dumps(payload, ensure_ascii=False, allow_nan=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.end_headers()
        if body:
            self.wfile.write(data)

    def api_error(self, error, body=True):
        # Only deliberately public exceptions may cross the HTTP boundary.
        from engine.audio import AudioError
        from engine.game import GameError
        if isinstance(error, (GameError, AudioError)):
            self.json_response(error.status, error.payload, body)
        else:
            self.log_error('Game service failed: %s', type(error).__name__)
            self.json_response(503, {'error': 'The game service is unavailable. Please try again.',
                                     'code': 'service_unavailable'}, body)

    def do_POST(self):
        # The local browser is the only writer; reject cross-site submissions.
        origin = self.headers.get('Origin')
        if (self.headers.get('Sec-Fetch-Site') == 'cross-site' or
                (origin and origin != 'http://' + self.headers.get('Host', ''))):
            self.json_response(403, {'error': 'This request must come from the game.', 'code': 'invalid_origin'})
            return
        path = urlsplit(self.path).path
        match = re.fullmatch(r'/api/games/([A-Za-z0-9_-]{1,64})/(cluster|genre)', path)
        race_move = re.fullmatch(r'/api/races/([A-Za-z0-9_-]{1,64})/move', path)
        if path not in ('/api/games', '/api/races') and not match and not race_move:
            self.send_error(404)
            return
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if self.headers.get_content_type() != 'application/json' or not 0 < length <= 16384:
                raise ValueError()
            request = json.loads(self.rfile.read(length), parse_constant=lambda _: None)
            if not isinstance(request, dict):
                raise ValueError()
        except (ValueError, UnicodeError):
            self.json_response(400, {'error': 'Send a valid game request.', 'code': 'invalid_request'})
            return
        try:
            if path == '/api/races':
                result = self.races().start(request.get('start_id'), request.get('goal_id'),
                                           request.get('settings'))
            elif race_move:
                result = self.races().move(race_move[1], request.get('genre_id'), request.get('revision'))
            else:
                service, _ = self.services()
                if path == '/api/games':
                    result = service.start(request.get('settings'), retry_id=request.get('retry_id'))
                elif match[2] == 'cluster':
                    result = service.choose_cluster(match[1], request.get('cluster_id'))
                else:
                    result = service.choose_genre(match[1], request.get('genre_id'))
            self.json_response(200, result)
        except (BrokenPipeError, ConnectionResetError):
            pass
        except Exception as error:
            self.api_error(error)

    def do_HEAD(self):
        self.serve(False)

    def do_GET(self):
        self.serve(True)

    def send_bytes(self, data, content_type, body, *, anonymous=False):
        size = len(data)
        start, end, status = 0, size - 1, 200
        value = self.headers.get('Range')
        if value:
            match = re.fullmatch(r'bytes=(\d*)-(\d*)', value)
            valid = match and any(match.groups())
            if valid:
                if match[1]:
                    start = int(match[1])
                    end = min(int(match[2]) if match[2] else end, end)
                else:
                    start = max(0, size - int(match[2]))
                valid = start <= end and start < size
            if not valid:
                self.send_response(416)
                self.send_header('Content-Range', f'bytes */{size}')
                self.send_header('Content-Length', '0')
                self.end_headers()
                return
            status = 206
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(end - start + 1))
        self.send_header('Accept-Ranges', 'bytes')
        self.send_header('Cache-Control', 'no-store' if anonymous else 'no-cache')
        self.send_header('X-Content-Type-Options', 'nosniff')
        if anonymous:
            self.send_header('Content-Disposition', 'inline; filename="sample.mp3"')
        if status == 206:
            self.send_header('Content-Range', f'bytes {start}-{end}/{size}')
        self.end_headers()
        if body:
            self.wfile.write(data[start:end + 1])

    def serve(self, body):
        path = urlsplit(self.path).path
        try:
            race = re.fullmatch(r'/api/races/([A-Za-z0-9_-]{1,64})', path)
            if race:
                self.json_response(200, self.races().get(race[1]), body)
                return
            if path == '/api/status':
                service, _ = self.services()
                self.json_response(200, {'ready': True, 'genres': len(service.catalog.genres)}, body)
                return
            if path == '/api/genres':
                service, _ = self.services()
                self.json_response(200, {'genres': [
                    {key: genre[key] for key in ('id', 'name', 'color')}
                    for genre in service.catalog.genres
                ]}, body)
                return
            genre_audio = re.fullmatch(r'/api/genres/([^/]+)/audio', path)
            if genre_audio:
                from engine.audio import AudioError
                from engine.game import GameError
                if not re.fullmatch(r'[0-9]{1,10}', genre_audio[1]):
                    raise GameError('Genre not found.', status=404, code='genre_not_found')
                service, media = self.services()
                genre_id = int(genre_audio[1])
                if not any(genre['id'] == genre_id for genre in service.catalog.genres):
                    raise GameError('Genre not found.', status=404, code='genre_not_found')
                track = next((sample for sample in service.catalog.samples(genre_id)
                              if sample.get('preview_url') or sample.get('track_id')), None)
                if track is None:
                    raise AudioError()
                self.send_bytes(media.get(track), 'audio/mpeg', body, anonymous=True)
                return
            audio = re.fullmatch(r'/api/games/([A-Za-z0-9_-]{1,64})/audio/([12])', path)
            if audio:
                service, media = self.services()
                track = service.audio_source(audio[1], int(audio[2]))
                self.send_bytes(media.get(track), 'audio/mpeg', body, anonymous=True)
                return
            candidate = re.fullmatch(
                r'/api/games/([A-Za-z0-9_-]{1,64})/candidate/(\d{1,10})/audio', path)
            if candidate:
                service, media = self.services()
                track = service.candidate_audio_source(candidate[1], int(candidate[2]))
                self.send_bytes(media.get(track), 'audio/mpeg', body, anonymous=True)
                return
            if path not in ASSETS:
                self.send_error(404)
                return
            asset = ROOT / 'web' / ALIASES.get(path, path[1:])
            if not asset.is_file():
                self.send_error(404)
                return
            self.send_bytes(asset.read_bytes(), mimetypes.guess_type(asset)[0] or 'application/octet-stream', body)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            pass
        except Exception as error:
            self.api_error(error, body)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8780)
    port = parser.parse_args().port
    print(f'Yinxun: http://127.0.0.1:{port}', flush=True)
    ThreadingHTTPServer(('127.0.0.1', port), Handler).serve_forever()
