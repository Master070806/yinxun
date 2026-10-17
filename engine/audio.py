"""Anonymous, bounded playback proxy for Every Noise's track previews."""
from collections import OrderedDict
import json
import re
import threading
import time
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, HTTPRedirectHandler, build_opener
from urllib.error import HTTPError, URLError

MAX_AUDIO_BYTES = 8 * 1024 * 1024
AUDIO_HOSTS = {'p.scdn.co'}


class AudioError(Exception):
    def __init__(self, message='This sample is currently unavailable. Try playing it again.', status=502):
        super().__init__(message)
        self.status = status
        self.payload = {'error': message, 'code': 'audio_unavailable'}


def allowed_preview(url):
    if not isinstance(url, str):
        return False
    try:
        parts = urlsplit(url)
        return (parts.scheme == 'https' and parts.hostname in AUDIO_HOSTS and
                parts.username is None and parts.password is None and parts.port in (None, 443))
    except ValueError:
        return False


class SafeRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not allowed_preview(newurl):
            raise AudioError()
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def strip_mp3_metadata(data):
    """Keep MPEG audio frames while dropping the usual title/artist ID3 tags."""
    if data.startswith(b'ID3') and len(data) >= 10:
        if all(b < 128 for b in data[6:10]):
            size = sum(b << shift for b, shift in zip(data[6:10], (21, 14, 7, 0)))
            end = 10 + size + (10 if data[3] == 4 and data[5] & 0x10 else 0)
            if end < len(data):
                data = data[end:]
    if len(data) >= 128 and data[-128:-125] == b'TAG':
        data = data[:-128]
    return data


class AudioStore:
    def __init__(self, capacity=24):
        self.capacity = capacity
        self.cache = OrderedDict()
        self.lock = threading.Lock()
        self.opener = build_opener(SafeRedirect())

    def _resolve(self, track):
        url = track.get('preview_url')
        if url:
            if not allowed_preview(url):
                raise AudioError()
            return url
        track_id = track.get('track_id') or ''
        if not re.fullmatch(r'[A-Za-z0-9]{22}', track_id):
            raise AudioError()
        request = Request('https://everynoise.com/spotproxy.cgi?' + urlencode({'track': track_id}),
                          headers={'User-Agent': 'Genreguessr/1.0'})
        try:
            with self.opener.open(request, timeout=12) as response:
                data = response.read(262145)
            if len(data) > 262144:
                raise AudioError()
            url = json.loads(data).get('preview_url')
            if not url or not allowed_preview(url):
                raise AudioError()
            return url
        except (HTTPError, URLError, TimeoutError, ValueError, OSError) as exc:
            raise AudioError() from exc

    def get(self, track):
        # The cache contains only audio bytes, not files exposed by the web server.
        with self.lock:
            url = self._resolve(track)
            cached = self.cache.get(url)
            if cached and time.monotonic() - cached[0] < 7200:
                self.cache.move_to_end(url)
                return cached[1]
            request = Request(url, headers={'User-Agent': 'Mozilla/5.0', 'Referer': 'https://everynoise.com/'})
            try:
                with self.opener.open(request, timeout=20) as response:
                    if not allowed_preview(response.geturl()):
                        raise AudioError()
                    mime = response.headers.get('Content-Type', '').split(';')[0]
                    if mime not in ('audio/mpeg', 'audio/mp3', 'application/octet-stream'):
                        raise AudioError()
                    data = response.read(MAX_AUDIO_BYTES + 1)
                if not data or len(data) > MAX_AUDIO_BYTES:
                    raise AudioError()
                data = strip_mp3_metadata(data)
            except (HTTPError, URLError, TimeoutError, OSError) as exc:
                raise AudioError() from exc
            self.cache[url] = (time.monotonic(), data)
            self.cache.move_to_end(url)
            while len(self.cache) > self.capacity:
                self.cache.popitem(last=False)
            return data
