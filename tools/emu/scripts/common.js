// Shared by the test scripts: boot build/ufo2.trd and get into the game (the world map).
export async function bootGame(zx, opts = {}) {
  const machine = opts.machine || 'pentagon';
  await zx.ready({ machine });
  await zx.start({ machine });
  const sp = zx.spectrum;
  const F = n => { for (let i = 0; i < n; i++) sp.runFrame(); };
  await zx.loadUrl('/media/ufo2.trd?' + Date.now(), { name: 'ufo2.trd' });
  zx.pause();
  sp.bootTrdos();
  const log = [];
  // the title program runs in IM 2; hold "2" until the game has set its own interrupt table (I = #8E)
  let n = 0, held = false;
  for (; n < 6000; n++) {
    F(1);
    const r = zx.captureRegisters();
    if (r.i === 0x8E) break;
    if (!held && r.im === 2 && r.pc >= 0x7000) { zx.keyDown('2'); held = true; }
  }
  zx.keyUp('2');
  log.push('game after ' + n + ' frames');
  const tr = [];
  for (let k = 0; k < 15; k++) { F(10); const r = zx.captureRegisters(); tr.push(r.pc.toString(16) + '/' + r.sp.toString(16) + '/' + r.i.toString(16)); }
  log.push('start: ' + tr.join(' '));
  if (opts.cheat) zx.keyDown('j');          // J + ENTER: no 3D fight
  F(5); zx.keyDown('Enter');
  const t2 = [];
  for (let k = 0; k < 40; k++) { F(1); const r = zx.captureRegisters(); t2.push(r.pc.toString(16) + '/' + r.sp.toString(16)); if (k === 10) { zx.keyUp('Enter'); if (opts.cheat) zx.keyUp('j'); } }
  log.push('enter: ' + t2.join(' '));
  const t3 = [];
  for (let k = 0; k < 30; k++) { F(10); const r = zx.captureRegisters(); t3.push(r.pc.toString(16) + '/' + r.sp.toString(16) + '/' + r.im); }
  log.push('idle: ' + t3.join(' '));
  const sym = {};
  for (const m of (await (await fetch('/media/game/main.sym?' + Date.now())).text()).matchAll(/^(\w+): EQU 0x([0-9A-Fa-f]+)/gm)) sym[m[1]] = parseInt(m[2], 16);
  log.push('map pc=' + zx.captureRegisters().pc.toString(16));
  return { sp, F, sym, log };
}
