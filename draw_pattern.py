import numpy as np
import bezier as bez
import pattern

trouser = pattern.Pattern("trouser_script")
trouser.measures_from_argv()
        
import matplotlib.pyplot as p

a=np.transpose(np.array(trouser.points.values()))
p.plot(a[0],a[1],"o",color="grey")

for l in trouser.lines:
    a=np.transpose(np.array(trouser.lines[l].minmax_points()))
    p.plot(a[0],a[1],color="grey")

for b in trouser.beziers:
    for bb in trouser.beziers[b]:
        vp = []
        for bbb in bb: vp.append(bez.pt2(bbb))
        bez.plotBezier(bez.Bezier(vp), 100)

p.show()
