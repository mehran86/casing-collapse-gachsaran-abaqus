"""Variants of a 2D V90W deck:  python make_sweep.py SRC DST MODE VALUE
 depth  z_m     : scale all depth-proportional loads (in-situ stress, tractions, pressures) from 3450 m to z; creep A from T = 0.0216 z + 23.8 C
 creepA A       : replace creep coefficient only (temperature swap)
 grade  fy,fu   : casing yield / tensile strength (MPa)
 angle  deg     : circumferential extent of the void (centred on the original void, multiples of 7.5 deg)"""
import sys, math, re
src, dst, mode, val = sys.argv[1:5]
L = open(src).read().replace('\r', '').split('\n')
def end(i):
    j = i + 1
    while j < len(L) and not L[j].startswith('*'): j += 1
    return j
def idx(exact):
    return [k for k, l in enumerate(L) if l.strip().lower() == exact.lower()][0]
def ids(exact):
    i = idx(exact); return [int(x) for l in L[i+1:end(i)] for x in l.split(',') if x.strip()]
def fmt(v): return [', '.join('%5d' % x for x in v[k:k+16]) for k in range(0, len(v), 16)]
note = ''
if mode == 'depth':
    z = float(val); s = z / 3450.0; T = 0.0216 * z + 23.8 + 273.15; A = 2.88e-8 * math.exp(-22600.0 / (8.314 * T))
    for k, l in enumerate(L):
        p = [x.strip() for x in l.split(',')]
        if 'TRVEC' in l and l.startswith('WELL-1.'): p[2] = '%.6g' % (float(p[2]) * s); L[k] = ', '.join(p)
        elif l.startswith('WELL-1.') and len(p) == 3 and p[1] == 'P': L[k] = '%s, P, %.6g' % (p[0], float(p[2]) * s)
        elif l.startswith('WELL-1.SALT, -'): L[k] = 'WELL-1.SALT, ' + ', '.join('%.6g' % (float(x) * s) for x in p[1:4]) + ', 0., '
    i = idx('*Creep, law=TIME'); L[i+1] = ' %.6g,3.,0.' % A
    note = 'DEPTH VARIANT: z = %g m, loads scaled by %.5f from 3450 m, T = %.1f C, creep A = %.5g' % (z, s, T - 273.15, A)
elif mode == 'creepA':
    i = idx('*Creep, law=TIME'); old = L[i+1]; L[i+1] = ' %s,3.,0.' % val; note = 'CREEP-COEFFICIENT VARIANT: A = %s (was %s)' % (val, old.strip())
elif mode == 'grade':
    fy, fu = val.split(','); i = idx('*Material, name=CASING'); j = [k for k in range(i, i + 8) if L[k].strip() == '*Plastic'][0]
    L[j+1] = '%s.,  0.' % fy; L[j+2] = '%s., 0.1' % fu; note = 'CASING GRADE VARIANT: yield %s MPa, tensile %s MPa' % (fy, fu)
elif mode == 'angle':
    a = float(val)
    i = idx('*Node'); N = {}
    for l in L[i+1:end(i)]:
        v = l.split(','); N[int(v[0])] = (float(v[1]), float(v[2]))
    i = idx('*Element, type=CPE8R'); C = {}
    for l in L[i+1:end(i)]:
        v = [int(x) for x in l.split(',')]; C[v[0]] = v[1:]
    FACE = {1: (0, 1, 4), 2: (1, 2, 5), 3: (2, 3, 6), 4: (3, 0, 7)}
    def ang(e):
        x = sum(N[n][0] for n in C[e][:4]); y = sum(N[n][1] for n in C[e][:4]); return math.degrees(math.atan2(y, x))
    def invoid(e):
        d = (ang(e) - 90.0 + 180.0) % 360.0 - 180.0; return abs(d) < a / 2.0
    casing, cem_all = ids('*Elset, elset=CASING'), ids('*Elset, elset=CEMENT_ALL')
    old_void = set(cem_all) - set(ids('*Elset, elset=CEMENT'))
    assert all(abs((ang(e) - 90 + 180) % 360 - 180) < 45 for e in old_void)
    void = [e for e in cem_all if invoid(e)]; cem = [e for e in cem_all if not invoid(e)]
    wall = [(e, 2) for e in ids('*Elset, elset=_WALL_ALL_S2, internal')] + [(e, 4) for e in ids('*Elset, elset=_WALL_ALL_S4, internal')]
    cemfaces = {frozenset(C[e][k] for k in FACE[f]) for e in cem_all for f in FACE}
    csg = [(e, f) for e in casing for f in FACE if frozenset(C[e][k] for k in FACE[f]) in cemfaces]
    assert len(csg) == len(wall) == 96, (len(csg), len(wall))
    def setblock(name, pairs):
        out = []; fs = sorted(set(f for e, f in pairs))
        for f in fs: out += ['*Elset, elset=_%s_S%d, internal' % (name, f)] + fmt(sorted(e for e, g in pairs if g == f))
        return out + ['*Surface, type=ELEMENT, name=%s' % name] + ['_%s_S%d, S%d' % (name, f, f) for f in fs]
    new = setblock('WALL_CEM', [p for p in wall if not invoid(p[0])]) + setblock('WALL_VOID', [p for p in wall if invoid(p[0])]) + setblock('CSG_OUT_VOID', [p for p in csg if invoid(p[0])])
    i0 = idx('*Elset, elset=_WALL_CEM_S2, internal'); i1 = end(idx('*Surface, type=ELEMENT, name=CSG_OUT_VOID'))
    L[i0:i1] = new
    for name, v in (('CEMENT', sorted(cem)), ('LINER_ACT', sorted(casing + cem))):
        i = idx('*Elset, elset=%s' % name); L[i+1:end(i)] = fmt(v)
    note = 'VOID-ANGLE VARIANT: void sector %g deg (%d cement elements removed, %d wall faces, %d casing faces in the void)' % (a, len(void), sum(invoid(p[0]) for p in wall), sum(invoid(p[0]) for p in csg))
L.insert(idx('*Heading') + 1, '** ' + note + ' (base %s)' % src.replace('\\', '/').split('/')[-1])
open(dst, 'w').write('\n'.join(L)); print(dst.replace('\\', '/').split('/')[-1], '|', note)
