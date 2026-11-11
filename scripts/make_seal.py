"""Sealed (undrained) void variant of a 2D V90W deck.
The 90-deg void sector is filled at Install with a fluid-like solid (bulk modulus K, shear modulus G~0, hybrid elements).
The original constant void pressure stays on the void faces, so the filler carries only the pressure change:
p_void = p0 + PRESS(filler)  ->  sealed fluid with initial pressure p0 and bulk modulus K."""
import sys, re
src, dst, K = sys.argv[1], sys.argv[2], float(sys.argv[3]); G = 1.0
L = open(src).read().replace('\r', '').split('\n')
def kw(i): return L[i].startswith('*') and not L[i].startswith('**')
def block(start):
    j = start + 1
    while j < len(L) and not L[j].startswith('*'): j += 1
    return j
def find(prefix, n=0):
    hits = [i for i, l in enumerate(L) if l.replace(' ', '').lower().startswith(prefix.replace(' ', '').lower())]
    return hits[n]
def elset(name):
    i = [k for k, l in enumerate(L) if l.strip().lower() == ('*elset, elset=%s' % name).lower()][0]
    j = block(i); return [int(x) for l in L[i+1:j] for x in l.split(',') if x.strip()]
cem_all, cem = set(elset('CEMENT_ALL')), set(elset('CEMENT')); void = sorted(cem_all - cem)
assert len(void) > 0 and cem < cem_all
ie = find('*Element, type=CPE8R'); je = block(ie)
conn = {}
for l in L[ie+1:je]:
    v = [int(x) for x in l.split(',')]; conn[v[0]] = v[1:]
FACE = {1: (0, 1, 4), 2: (1, 2, 5), 3: (2, 3, 6), 4: (3, 0, 7)}
vfaces = {frozenset(conn[e][k] for k in FACE[f]) for e in void for f in FACE}
ends = {}
for e in sorted(cem):
    for f in FACE:
        if frozenset(conn[e][k] for k in FACE[f]) in vfaces: ends.setdefault(f, []).append(e)
nend = sum(len(v) for v in ends.values())
# monitor elements: void elements touching the casing-void surface, middle of the sector
i = find('*Elset, elset=_CSG_OUT_VOID_S4'); csgv = [int(x) for l in L[i+1:block(i)] for x in l.split(',') if x.strip()]
cfaces = {frozenset(conn[e][k] for k in FACE[4]) for e in csgv}
inner = [e for e in void if any(frozenset(conn[e][k] for k in FACE[f]) in cfaces for f in FACE)]
mon = inner[len(inner)//2 - 1: len(inner)//2 + 1] if inner else void[:2]
def fmt(ids):
    return [', '.join('%5d' % x for x in ids[k:k+16]) for k in range(0, len(ids), 16)]
# --- pressure in void (from Install step)
iv = find('WELL-1.CSG_OUT_VOID, P,'); p0 = float(L[iv].split(',')[-1])
out = []
i = 0
state = {'step': None}
while i < len(L):
    l = L[i]
    if i == ie:
        out.append(l); out += [x for x in L[ie+1:je] if int(x.split(',')[0]) not in set(void)]
        out.append('*Element, type=CPE8RH'); out += [x for x in L[ie+1:je] if int(x.split(',')[0]) in set(void)]
        i = je; continue
    if l.strip() == '*Elset, elset=CEMENT':
        out.append('*Elset, elset=VOID_FLUID'); out += fmt(void)
        out.append('*Elset, elset=VF_MON'); out += fmt(mon)
        for f, ids in ends.items():
            out.append('*Elset, elset=_CEM_VEND_S%d, internal' % f); out += fmt(ids)
        out.append('*Surface, type=ELEMENT, name=CEM_VOID_END'); out += ['_CEM_VEND_S%d, S%d' % (f, f) for f in ends]
    if l.strip() == '*Solid Section, elset=CEMENT_ALL, material=CEMENT':
        out += ['*Solid Section, elset=CEMENT, material=CEMENT', L[i+1], '** Section: SEC_VOIDFLUID', '*Solid Section, elset=VOID_FLUID, material=VOIDFLUID', ',']
        i += 2; continue
    if l.strip() == '*Material, name=CEMENT':
        E = 9 * K * G / (3 * K + G); nu = (3 * K - 2 * G) / (2 * (3 * K + G))
        out += ['*Material, name=VOIDFLUID', '*Elastic', '%.6g, %.8f' % (E, nu)]
    if l.startswith('*Step, name='): state['step'] = l.split('name=')[1].split(',')[0]
    if state['step'] == 'Install':
        if l.strip() == '*Model Change, add' and L[i+1].strip().startswith('WELL-1.LINER_ACT'):
            out += [l, L[i+1], 'WELL-1.VOID_FLUID,']; i += 2; continue
        if l.strip() == '*Model Change, type=CONTACT PAIR, add':
            out.append('** void contact pair not activated: the void is filled with fluid'); i += 2; continue
        if l.strip().startswith('WELL-1.WALL_VOID, P,'):
            out += [l, '** Name: P_CEM_VOID_END   Type: Pressure', '*Dsload, op=NEW', 'WELL-1.CEM_VOID_END, P, %g' % p0]; i += 1; continue
    if l.strip() == '*End Step' and state['step'] in ('Install', 'Prod1', 'Shut', 'Prod2'):
        out += ['** HISTORY OUTPUT: fluid pressure change in the sealed void (total = %g + PRESS)' % p0, '*Output, history', '*Element Output, elset=WELL-1.VF_MON', 'PRESS']
    out.append(l); i += 1
hi = find('*Heading')
out.insert(hi + 1, '** SEALED VOID VARIANT: void sector filled at Install with fluid-like solid, K = %g MPa, G = %g MPa, CPE8RH (%d elements); initial void pressure %g MPa kept as surface load; %d cement end faces loaded (base %s)' % (K, G, len(void), p0, nend, src.split('/')[-1]))
open(dst, 'w').write('\n'.join(out))
print(dst.split('/')[-1], 'void elems', len(void), 'end faces', {f: len(v) for f, v in ends.items()}, 'mon', mon, 'p0', p0)
