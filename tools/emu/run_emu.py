#!/usr/bin/env python3
"""Run a harness script in headless Edge against ZX-M8XXX and save the result.

    python tools/emu/run_emu.py smoke machine=pentagon trd=/media/ufo.trd name=boot1 [png=build/emu/boot1.png]

Everything after the script name is passed to the script as URL query parameters.
Results land in build/emu/<name>.json (and a PNG if png= is given and the result has `scr`).
"""
import json, os, shutil, subprocess, sys, tempfile, time, urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
EDGE = os.environ.get('EDGE') or next((p for p in (
    r'C:\Program Files\Google\Chrome\Application\chrome.exe',   # Edge prints nothing here: it hands the job to the running Edge
    r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe') if os.path.exists(p)), 'msedge')
PORT = int(os.environ.get('EMU_PORT', '8791'))


def main(argv):
    script = argv[0]
    params = dict(a.split('=', 1) for a in argv[1:])
    png = params.pop('png', None)
    budget = int(params.pop('budget', '120000'))
    params['script'] = script
    params.setdefault('name', script)
    out = os.path.join(ROOT, 'build', 'emu')
    os.makedirs(out, exist_ok=True)
    res = os.path.join(out, params['name'] + '.json')
    if os.path.exists(res):
        os.remove(res)
    srv = subprocess.Popen([sys.executable, os.path.join(ROOT, 'tools', 'emu', 'serve_emu.py'), str(PORT)])
    prof = tempfile.mkdtemp(prefix='zxrun')
    try:
        time.sleep(0.8)
        url = f'http://127.0.0.1:{PORT}/ufo/harness.html?' + urllib.parse.urlencode(params)
        cmd = [EDGE, '--headless=new', '--disable-gpu', f'--user-data-dir={prof}', '--no-first-run',
               f'--virtual-time-budget={budget}', '--dump-dom', url]
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        dom = p.stdout
        i = dom.find('id="out">')
        print(dom[i + 9:i + 900].split('</pre>')[0] if i >= 0 else 'no DOM output: ' + dom[:300] + p.stderr[-200:])
    except subprocess.TimeoutExpired:
        print('TIMEOUT')
    finally:
        srv.terminate()
        shutil.rmtree(prof, ignore_errors=True)
    if not os.path.exists(res):
        print('no result file')
        return 1
    data = json.load(open(res, encoding='utf-8'))
    payload = data.get('data', data)
    scr = payload.pop('scr', None)
    if png and scr:
        import zxtool
        raw = os.path.join(out, 'scr.bin')
        open(raw, 'wb').write(bytes(scr))
        zxtool.main(['scr', raw, png])
        print('screen ->', png)
    print(json.dumps(payload))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))