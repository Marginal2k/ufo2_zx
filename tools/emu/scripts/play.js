// Boot build/ufo2.trd and play a scripted sequence.
//   p:ADDR:VAL = poke (hex), j:ADDR = set PC (hex)
//   KX = hold key X for 70 frames (the title program looks at the keys only twice a second)
//   steps=w300,k2,w900,s:title,kENTER,...     wN = run N frames, kX = press key X, s:name = screenshot
//   (a screenshot is the screen that is shown: page 7 when bit 3 of port #7FFD is set, else page 5)
// Result: shots {name: 6912 bytes}, regs, the last value written to #7FFD.
export async function run(zx, q) {
  const machine = q.get('machine') || 'pentagon';
  await zx.ready({ machine });
  await zx.start({ machine });
  const sp = zx.spectrum;
  const F = n => { for (let i = 0; i < n; i++) sp.runFrame(); };
  const trd = q.get('trd') || '/media/ufo2.trd';
  await zx.loadUrl(trd + '?' + Date.now(), { name: 'ufo2.trd' });
  zx.pause();
  sp.bootTrdos();
  const res = { shots: {}, log: [] };
  const shown = () => {
    const bank = sp.memory.screenBank || 5;
    res.p7ffd = bank;
    return Array.from(zx.peekBank(bank).slice(0, 6912));
  };
  for (const st of (q.get('steps') || 'w600,s:boot').split(',')) {
    if (st[0] === 'w') F(+st.slice(1));
    else if (st[0] === 'k') { const k = st.slice(1); zx.keyDown(k); F(8); zx.keyUp(k); F(8); }
    else if (st[0] === 'p') { const [a, v] = st.slice(2).split(':'); zx.pokeBlock(parseInt(a, 16), [parseInt(v, 16)]); }
    else if (st[0] === 'j') { zx.pause(); zx.setRegisters({ pc: parseInt(st.slice(2), 16) }); }
    else if (st[0] === 'K') { const k = st.slice(1); zx.keyDown(k); F(70); zx.keyUp(k); F(8); }
    else if (st[0] === 'd') zx.keyDown(st.slice(1));
    else if (st[0] === 'u') zx.keyUp(st.slice(1));
    else if (st[0] === 's') { res.shots[st.slice(2)] = shown(); res.log.push(st.slice(2) + ' pc=' + zx.captureRegisters().pc.toString(16) + ' 7ffd=' + res.p7ffd); }
  }
  res.regs = zx.captureRegisters();
  await zx.report(res, 'result', q.get('name') || 'play');
  return { log: res.log, regs: res.regs };
}
