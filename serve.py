"""Local-only map preview server; exposes only explicitly allowed app assets."""
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from pathlib import Path
import re,mimetypes
ROOT=Path(__file__).resolve().parent
class Handler(BaseHTTPRequestHandler):
    def do_HEAD(self):self.serve(False)
    def do_GET(self):self.serve(True)
    def serve(self,body):
        url=self.path.split('?')[0]
        if url in ['/','/index.html','/style.css','/map.html','/map.css','/map.js','/map-data.json']:
            path=ROOT/'web'/('map.html' if url in ['/', '/index.html'] else url[1:])
        else:self.send_error(404);return
        if not path.is_file():self.send_error(404);return
        size=path.stat().st_size;start=0;end=size-1;status=200
        value=self.headers.get('Range')
        if value:
            m=re.fullmatch(r'bytes=(\d*)-(\d*)',value)
            if not m or not any(m.groups()):self.send_error(416);return
            if m[1]:start=int(m[1]);end=min(int(m[2]) if m[2] else end,end)
            else:start=max(0,size-int(m[2]))
            if start>end or start>=size:self.send_response(416);self.send_header('Content-Range',f'bytes */{size}');self.end_headers();return
            status=206
        self.send_response(status)
        self.send_header('Content-Type',mimetypes.guess_type(path)[0] or 'application/octet-stream')
        self.send_header('Content-Length',str(end-start+1));self.send_header('Accept-Ranges','bytes')
        self.send_header('Cache-Control','no-cache');self.send_header('X-Content-Type-Options','nosniff')
        if status==206:self.send_header('Content-Range',f'bytes {start}-{end}/{size}')
        self.end_headers()
        if body:
            try:
                with path.open('rb') as f:
                    f.seek(start);remaining=end-start+1
                    while remaining:
                        chunk=f.read(min(65536,remaining))
                        if not chunk:break
                        self.wfile.write(chunk);remaining-=len(chunk)
            except (BrokenPipeError,ConnectionResetError,ConnectionAbortedError):pass
if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument('--port',type=int,default=8765)
    port=parser.parse_args().port
    print(f'Yinxun: http://127.0.0.1:{port}',flush=True)
    ThreadingHTTPServer(('127.0.0.1',port),Handler).serve_forever()
