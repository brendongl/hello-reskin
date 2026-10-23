#!/usr/bin/env python3
"""PFS0 (NSP) pack / unpack.
  pfs0.py out.nsp file...          pack files into an NSP
  pfs0.py -x game.nsp outdir       unpack; also writes outdir/title.keys from a common .tik (rights_id = title key)"""
import os, struct, sys

def unpack(nsp, outdir):
    os.makedirs(outdir, exist_ok=True)
    with open(nsp, 'rb') as f:
        magic, n, stlen, _ = struct.unpack('<4sIII', f.read(16)); assert magic == b'PFS0', 'not an NSP/PFS0'
        ents = [struct.unpack('<QQII', f.read(24)) for _ in range(n)]; st = f.read(stlen); base = 16 + 24 * n + stlen
        for off, sz, noff, _ in ents:
            name = st[noff:st.index(b'\0', noff)].decode(); f.seek(base + off); left = sz
            with open(os.path.join(outdir, name), 'wb') as o:
                while left:
                    b = f.read(min(left, 1 << 22)); o.write(b); left -= len(b)
            print(name, sz)
            if name.endswith('.tik'):
                t = open(os.path.join(outdir, name), 'rb').read()
                key, rid = t[0x180:0x190].hex(), t[0x2A0:0x2B0].hex()
                with open(os.path.join(outdir, 'title.keys'), 'a') as k: k.write(f'{rid} = {key}\n')
                print('  title key written to', os.path.join(outdir, 'title.keys'))

def pack(out, files):
    names = [os.path.basename(f).encode() + b'\0' for f in files]
    strtab = b''.join(names); hdr_len = 16 + 24 * len(files) + len(strtab); strtab += b'\0' * ((-hdr_len) % 0x20)
    entries, off, noff = b'', 0, 0
    for f, n in zip(files, names):
        sz = os.path.getsize(f); entries += struct.pack('<QQII', off, sz, noff, 0); off += sz; noff += len(n)
    with open(out, 'wb') as o:
        o.write(b'PFS0' + struct.pack('<III', len(files), len(strtab), 0) + entries + strtab)
        for f in files:
            with open(f, 'rb') as i:
                while True:
                    b = i.read(1 << 22)
                    if not b: break
                    o.write(b)
    print(out, off)

if __name__ == '__main__':
    if sys.argv[1] == '-x': unpack(sys.argv[2], sys.argv[3])
    else: pack(sys.argv[1], sys.argv[2:])
