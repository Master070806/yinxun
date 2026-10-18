"""Music game APIs and explicitly allowlisted website assets."""
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from threading import Lock
from time import monotonic
from urllib.parse import parse_qs, urlsplit
import json
import mimetypes
import re

ROOT = Path(__file__).resolve().parent
ASSETS = {'/', '/index.html', '/home.css', '/style.css', '/map.html', '/map.css', '/i18n.js', '/i18n.css', '/i18n-messages.js',
          '/map.js', '/map-data.json', '/genreguessr', '/genreguessr/',
          '/genreguessr.html', '/genreguessr.css', '/genreguessr.js',
          '/genre-cluster.js', '/genre-cluster.css',
          '/genrerace', '/genrerace/', '/genrerace.html', '/genrerace.css', '/genrerace.js',
          '/multiplayer-genreguessr', '/multiplayer-genreguessr/', '/multiplayer-genreguessr.html',
          '/multiplayer-genrerace', '/multiplayer-genrerace/', '/multiplayer-genrerace.html',
          '/multiplayer.js', '/multiplayer.css',
          '/about', '/about/', '/about.html', '/about.css'}
ALIASES = {'/': 'index.html', '/genreguessr': 'genreguessr.html',
           '/genreguessr/': 'genreguessr.html',
           '/genrerace': 'genrerace.html', '/genrerace/': 'genrerace.html',
           '/multiplayer-genreguessr': 'multiplayer-genreguessr.html',
           '/multiplayer-genreguessr/': 'multiplayer-genreguessr.html',
           '/multiplayer-genrerace': 'multiplayer-genrerace.html',
           '/multiplayer-genrerace/': 'multiplayer-genrerace.html',
           '/about': 'about.html', '/about/': 'about.html'}


class Handler(BaseHTTPRequestHandler):
    game_service = None
    race_service = None
    multiplayer_service = None
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

    def rooms(self):
        service, _ = self.services()
        races = self.races()
        cls = type(self)
        with cls.initialization_lock:
            if (cls.multiplayer_service is None or
                    cls.multiplayer_service.catalog is not service.catalog or
                    cls.multiplayer_service.provider is not service.provider):
                from engine.multiplayer import MultiplayerService
                cls.multiplayer_service = MultiplayerService(service, races)
            return cls.multiplayer_service

    def player_token(self, *, audio=False):
        authorization = self.headers.get('Authorization', '')
        if authorization.startswith('Bearer '):
            return authorization[7:]
        if authorization:
            return 'invalid-authorization'
        if audio:
            return parse_qs(urlsplit(self.path).query).get('token', [None])[0]
        return None

    def log_request(self, code='-', size='-'):
        # Audio elements need a query credential; never write it to access logs.
        self.log_message('"%s %s %s" %s %s', self.command,
                         urlsplit(self.path).path, self.request_version, str(code), str(size))

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
        # Allow same-host HTTP or HTTPS (including a TLS reverse proxy).
        origin = self.headers.get('Origin')
        host = self.headers.get('Host', '')
        if (self.headers.get('Sec-Fetch-Site') == 'cross-site' or
                (origin and origin not in ('http://' + host, 'https://' + host))):
            self.discard_request_body()
            self.json_response(403, {'error': 'This request must come from the game.', 'code': 'invalid_origin'})
            return
        path = urlsplit(self.path).path
        match = re.fullmatch(r'/api/games/([A-Za-z0-9_-]{1,64})/(cluster|genre)', path)
        race_move = re.fullmatch(r'/api/races/([A-Za-z0-9_-]{1,64})/move', path)
        room_action = re.fullmatch(
            r'/api/rooms/([A-Za-z0-9_-]{1,64})/(join|configure|start|cluster|genre|ready|move|leave|remove)', path)
        if path not in ('/api/games', '/api/races', '/api/rooms') and not match and not race_move and not room_action:
            self.discard_request_body()
            self.send_error(404)
            return
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if self.headers.get_content_type() != 'application/json' or not 0 < length <= 16384:
                self.discard_request_body()
                raise ValueError()
            request = json.loads(self.rfile.read(length), parse_constant=lambda _: None)
            if not isinstance(request, dict):
                raise ValueError()
        except (ValueError, UnicodeError):
            self.json_response(400, {'error': 'Send a valid game request.', 'code': 'invalid_request'})
            return
        try:
            if path == '/api/rooms':
                result = self.rooms().create(request)
            elif room_action:
                if room_action[2] == 'join':
                    result = self.rooms().join(room_action[1], request)
                else:
                    result = self.rooms().action(room_action[1], self.player_token(),
                                                room_action[2], request)
            elif path == '/api/races':
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

    def discard_request_body(self):
        # Closing over unread input can reset the connection on Windows before
        # the client receives our error. Bound both the bytes and waiting time.
        try:
            length = min(max(int(self.headers.get('Content-Length', '0')), 0), 65536)
        except ValueError:
            return
        previous_timeout = self.connection.gettimeout()
        deadline = monotonic() + 0.5
        try:
            while length and (remaining := deadline - monotonic()) > 0:
                self.connection.settimeout(remaining)
                chunk = self.rfile.read1(min(length, 8192))
                if not chunk:
                    break
                length -= len(chunk)
        except OSError:
            pass
        finally:
            self.connection.settimeout(previous_timeout)

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
        self.send_header('Referrer-Policy', 'no-referrer')
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
            game = re.fullmatch(r'/api/games/([A-Za-z0-9_-]{1,64})', path)
            if game:
                service, _ = self.services()
                self.json_response(200, service.get(game[1]), body)
                return
            room = re.fullmatch(r'/api/rooms/([A-Za-z0-9_-]{1,64})', path)
            if room:
                self.json_response(200, self.rooms().get(room[1], self.player_token()), body)
                return
            room_audio = re.fullmatch(
                r'/api/rooms/([A-Za-z0-9_-]{1,64})/audio/(\d{1,2})/(clue|candidate)/(\d{1,10})', path)
            if room_audio:
                kind = ('clue' + room_audio[4]) if room_audio[3] == 'clue' else 'candidate'
                track = self.rooms().audio_source(room_audio[1], self.player_token(audio=True),
                                                 int(room_audio[2]), kind,
                                                 int(room_audio[4]) if kind == 'candidate' else None)
                _, media = self.services()
                self.send_bytes(media.get(track), 'audio/mpeg', body, anonymous=True)
                return
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
    parser.add_argument('--host', default='127.0.0.1',
                        help='Bind address; use 0.0.0.0 to allow multiplayer on your network.')
    args = parser.parse_args()
    print(f'Yinxun: http://{args.host}:{args.port}', flush=True)
    if args.host == '0.0.0.0':
        print('Invite friends using this computer\'s LAN IP in the browser URL.', flush=True)
    ThreadingHTTPServer((args.host, args.port), Handler).serve_forever()
