"""Static server for headless emulator runs.

  /                 -> the ZX-M8XXX folder (EMU_DIR)
  /ufo/...          -> tools/emu/   (harness page and scripts)
  /media/...        -> build/       (images built by this project)
  POST /result?name=x -> build/emu/x.json   (written atomically)
"""
import http.server, json, mimetypes, os, re, sys
from urllib.parse import urlparse, parse_qs

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
EMU_DIR = os.environ.get('M8XXX_DIR', r'D:\Emulators\ZX\ZX-M8XXX')
OUT = os.path.join(ROOT, 'build', 'emu')
for ext, t in (('.js', 'text/javascript'), ('.mjs', 'text/javascript'), ('.css', 'text/css'),
               ('.json', 'application/json'), ('.wasm', 'application/wasm')):
    mimetypes.add_type(t, ext)
SAFE = re.compile(r'^[A-Za-z0-9._-]{1,64}$')


class H(http.server.SimpleHTTPRequestHandler):
    def translate_path(self, path):
        p = urlparse(path).path
        for prefix, base in (('/ufo/', os.path.join(ROOT, 'tools', 'emu')), ('/media/', os.path.join(ROOT, 'build'))):
            if p.startswith(prefix):
                return os.path.join(base, *[x for x in p[len(prefix):].split('/') if x and x != '..'])
        return os.path.join(EMU_DIR, *[x for x in p.split('/') if x and x != '..'])

    def end_headers(self):
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        super().end_headers()

    def do_POST(self):
        u = urlparse(self.path)
        if u.path.rstrip('/') not in ('/result', '/progress'):
            self.send_error(404)
            return
        body = self.rfile.read(int(self.headers.get('Content-Length') or 0))
        name = (parse_qs(u.query).get('name') or [u.path.strip('/')])[0]
        if not SAFE.match(name):
            self.send_error(400)
            return
        os.makedirs(OUT, exist_ok=True)
        p = os.path.join(OUT, name if name.endswith('.json') else name + '.json')
        open(p + '.tmp', 'wb').write(body)
        os.replace(p + '.tmp', p)
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(b'{"ok":true}')

    def log_message(self, *a):
        pass


if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
    http.server.ThreadingHTTPServer(('127.0.0.1', port), H).serve_forever()
