"""Two-mechanism creep variant: python make_dm.py SRC DSTJOB B
 strain rate = A q^3 + B q  (A from the base deck, B in MPa^-1 s^-1); writes DSTJOB.inp and DSTJOB.for (user subroutine CREEP)"""
import sys
src, job, B = sys.argv[1], sys.argv[2], float(sys.argv[3])
L = open(src).read().replace('\r', '').split('\n')
i = [k for k, l in enumerate(L) if l.strip() == '*Creep, law=TIME'][0]
A = float(L[i+1].split(',')[0]); L[i:i+2] = ['*Creep, law=USER']
h = [k for k, l in enumerate(L) if l.startswith('*Heading')][0]
L.insert(h + 1, '** TWO-MECHANISM CREEP VARIANT: rate = A q^3 + B q, A = %.6g MPa^-3 s^-1, B = %.3g MPa^-1 s^-1, user subroutine CREEP in %s.for (base %s)' % (A, B, job, src.replace('\\', '/').split('/')[-1]))
open(job + '.inp', 'w').write('\n'.join(L))
F = """      SUBROUTINE CREEP(DECRA,DESWA,STATEV,SERD,EC,ESW,P,QTILD,
     1 TEMP,DTEMP,PREDEF,DPRED,TIME,DTIME,CMNAME,LEXIMP,LEND,
     2 COORDS,NSTATV,NOEL,NPT,LAYER,KSPT,KSTEP,KINC)
C     Two-mechanism salt creep: rate = A*q**3 + B*q  (units MPa, s)
      INCLUDE 'ABA_PARAM.INC'
      CHARACTER*80 CMNAME
      DIMENSION DECRA(5),DESWA(5),STATEV(*),PREDEF(*),DPRED(*),
     1 TIME(3),COORDS(*),EC(2),ESW(2)
      PARAMETER (A=%sD0, B=%sD0)
      Q = QTILD
      IF (Q.LT.0.D0) Q = 0.D0
      DECRA(1) = (A*Q**3 + B*Q)*DTIME
      IF (LEXIMP.EQ.1) THEN
        DECRA(5) = (3.D0*A*Q**2 + B)*DTIME
      END IF
      RETURN
      END
""" % (('%.6E' % A).replace('E', 'D').replace('D0', 'D0') if False else '%.6E' % A, '%.6E' % B)
F = F.replace('E-', 'D-').replace('D0, B', ', B').replace('D0)', ')')
open(job + '.for', 'w').write(F); print(job, A, B)
