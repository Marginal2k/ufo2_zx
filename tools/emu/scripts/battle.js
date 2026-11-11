// Test: start with the J+ENTER cheat (no 3D fight), hire a crew, force an interception, answer Y, watch the tactical battle start.
//   python tools/emu/run_emu.py battle name=battle pc=<address of "LD A,(xHAC2)" in build/game/main.lst>
import { bootGame } from './common.js';
export async function run(zx, q) {
  const { sp, F, sym, log } = await bootGame(zx, { cheat: true });
  const res = { log, shots: {} };
  const h = v => v.toString(16);
  const shot = n => { res.shots[n] = Array.from(zx.peekBank(sp.memory.screenBank || 5).slice(0, 6912)); };
  res.log.push('xHAC2=' + h(zx.peek(sym.xHAC2)) + ' pc=' + h(zx.captureRegisters().pc));
  zx.pause(); zx.runToInterrupt(200000); zx.step(9);
  res.log.push('after int pc=' + h(zx.captureRegisters().pc));
  const S = 0x9100, w = v => [v & 255, v >> 8];
  // LD A,4 / LD (NRECR),A / LD (AQU),A / CALL RECRUT / XOR A / LD (T_INTR),A / LD (T_TYPE),A / LD (T_UFO),A / JP cheat path
  zx.pokeBlock(S, [0x3E, 4, 0x32, ...w(sym.NRECR), 0x32, ...w(sym.AQU), 0xCD, ...w(sym.RECRUT), 0xAF, 0x32, ...w(sym.T_INTR),
    0x32, ...w(sym.T_TYPE), 0x32, ...w(sym.T_UFO), 0xC3, ...w(parseInt(q.get('pc'), 16))]);
  zx.setRegisters({ pc: S, sp: 0x4030 });
  const tr = [];
  for (let i = 0; i < 12; i++) { tr.push(h(zx.captureRegisters().pc)); zx.step(1); }
  res.log.push('trace ' + tr.join(' '));
  res.log.push('mem88ba ' + Array.from(zx.peekBlock(0x88BA, 12)).map(h).join(' '));
  const r1 = zx.runTo(sym.YES_NO, 3000000);
  res.log.push('to YES_NO: ' + JSON.stringify(r1));
  for (let i = 0; i < 3000; i++) { F(1); const pc = zx.captureRegisters().pc; if (pc >= sym.YES_NO && pc < sym.YES_NO + 0x12) break; }
  F(20);
  res.log.push('before y pc=' + h(zx.captureRegisters().pc));
  shot('a');
  zx.keyDown('y'); F(10); zx.keyUp('y');
  for (let i = 0; i < 16; i++) {
    F(150);
    const r = zx.captureRegisters();
    res.log.push(`f${i} pc=${h(r.pc)} sp=${h(r.sp)} im=${r.im} i=${h(r.i)}`);
    if (i === 3) shot('b');
    if (i === 7) shot('c');
  }
  shot('d');
  await zx.report(res, 'result', 'battle');
  return { log: res.log };
}
