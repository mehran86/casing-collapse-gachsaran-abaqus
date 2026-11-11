"""Sealed void that loses its pressure: FK deck + Trigger step after Prod1 (10 yr) that removes the fluid filler
(pressure ramps down to the initial void pressure, which stays as a surface load) and activates wall-casing contact."""
import sys
src, dst = sys.argv[1], sys.argv[2]
L = open(src).read().replace('\r', '').split('\n')
VF = ['*Output, history', '*Element Output, elset=WELL-1.VF_MON', 'PRESS']
out = []; step = None; i = 0; inst_out = []; grab = False
while i < len(L):
    l = L[i]
    if l.startswith('*Step, name='): step = l.split('name=')[1].split(',')[0]
    if step == 'Install':
        if l.startswith('** OUTPUT REQUESTS'): grab = True
        if l.strip() == '*End Step': grab = False
        if grab: inst_out.append(l)
    # drop fluid-pressure history after the leak
    if step in ('Shut', 'Prod2') and L[i+1:i+4] == VF and l.startswith('** HISTORY OUTPUT: fluid pressure'):
        i += 4; continue
    if step in ('Shut', 'Prod2') and l.startswith('*Visco, cetol='):
        out += [l + ', stabilize=0.0002, allsdtol=0.05, continue=NO', L[i+1], '*Controls, parameters=line search', '5, 4., 0.25, 0.25, 0.1']; i += 2; continue
    out.append(l)
    if step == 'Prod1' and l.strip() == '*End Step':
        blk = [x for x in inst_out]
        # remove the VF_MON history block from the copied output requests
        for j in range(len(blk) - 3):
            if blk[j+1:j+4] == VF: del blk[j:j+4]; break
        out += ['** ----------------------------------------------------------------', '** ', '** STEP: Trigger (sealed void loses its pressure)', '** ',
                '*Step, name=Trigger, nlgeom=YES, inc=2000, unsymm=YES', '*Static', '0.05, 1., 1e-08, 0.1', '** ', '** INTERACTIONS', '** ',
                '*Model Change, remove', 'WELL-1.VOID_FLUID,', '*Model Change, type=CONTACT PAIR, add', 'WELL-1.WALL_VOID, WELL-1.CSG_OUT_VOID', '** '] + blk + ['*End Step']
        step = 'Trigger'
    i += 1
hi = [k for k, l in enumerate(out) if l.startswith('*Heading')][0]
out.insert(hi + 1, '** LEAK VARIANT: fluid filler removed and void contact activated in step Trigger at the end of Prod1 (10 yr); stabilize + line search in Shut and Prod2 (base %s)' % src.replace('\\', '/').split('/')[-1])
open(dst, 'w').write('\n'.join(out)); print(dst, len(out) - len(L), 'lines added')
