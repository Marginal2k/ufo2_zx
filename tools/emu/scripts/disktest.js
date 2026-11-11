// Test of the game's disk layer in the running game: save/load of the 4K save block, and an encyclopedia page
// read + unpacked in place exactly as USA (xlix.asm) does it.
import { bootGame } from './common.js';
export async function run(zx, q) {
  const { sp, F, sym, log } = await bootGame(zx, { cheat: false });
  const res = { log };
  const w = v => [v & 255, v >> 8];
  const S = 0xA800;
  const call = (code) => {
    zx.pause(); zx.runToInterrupt(400000); zx.step(12);
    zx.pokeBlock(S, [0xF3, ...code, 0x18, 0xFE]);
    zx.setRegisters({ pc: S, sp: 0x4030 });
    const r = zx.runTo(S + 1 + code.length, 200000000);
    return r.reached;
  };
  // ---- save / load
  const pat = []; for (let i = 0; i < 4096; i++) pat.push((i * 7 + (i >> 8)) & 255);
  zx.pokeBlock(0x9000, pat);
  res.log.push('save ' + call([0xCD, ...w(sym.S_DSCR)]));
  zx.pokeBlock(0x9000, new Array(4096).fill(0));
  res.log.push('load ' + call([0xCD, ...w(sym.L_DSCR)]));
  const back = zx.peekBlock(0x9000, 4096);
  let bad = 0; for (let i = 0; i < 4096; i++) if (back[i] !== pat[i]) bad++;
  res.log.push('save/load differences: ' + bad);
  // ---- encyclopedia page n: as USA does
  for (const n of [54, 59, 73]) {
    const code = [0xCD, ...w(sym.LDASM3), 0x3E, 0x06, 0xCD, ...w(sym.MEM),
      0x3E, n, 0x21, 0x00, 0xC0, 0xCD, ...w(sym.READ),
      0xED, 0x4B, 0x00, 0xC0, 0x21, 0x02, 0xC0, 0x09, 0x2B, 0x11, 0xFE, 0xFF, 0xED, 0xB8, 0xEB, 0x23, 0x11, 0x00, 0xC0,
      0xCD, ...w(sym.DELPC), 0xCD, ...w(sym.LDASM2)];
    const ok = call(code);
    const got = zx.peekBank(6).slice(0, 16128);
    const name = n === 54 ? '54_up1' : n === 59 ? '59_up6' : '73_up20';
    const want = new Uint8Array(await (await fetch('/media/data/res_raw/' + name + '.bin?' + Date.now())).arrayBuffer());
    let d = 0; for (let i = 0; i < 16128; i++) if (got[i] !== want[i]) d++;
    res.log.push(`resource ${n}: returned ${ok}, differences ${d}`);
  }
  res.log.push('drive byte ' + zx.peek(sym.DSKDRV));
  await zx.report(res, 'result', 'disktest');
  return res;
}
