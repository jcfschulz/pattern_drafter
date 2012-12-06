import numpy as np
import sys
import stabledict   # replace by OrderedDict from Python 2.7
import warnings

class VectorLine:

    def __init__(self,r0,u,form_mode="parameter"):
        self.points = []
        self.ls = []
        self.line_prec = 1e-10
        
        if (form_mode == "parameter"):
            self.r0 = np.array(r0)
            self.ls.append(0)
            self.points.append(r0)
            self.u = np.array(u)
        elif (form_mode == "two_points"):
            self.r0 = np.array(r0)
            self.u = self.r0 - np.array(u)
            self.u /= np.sqrt((self.u**2).sum())
            self.pos(r0)
            self.pos(u)
        elif (form_mode == "normal"):
            self.r0 = np.array(r0)
            self.u = np.array([-u.u[1], u.u[0]])
            self.u /= np.sqrt((self.u**2).sum())
            self.ls.append(0)
            self.points.append(r0)

    def calc_from_two_points(a,b):
        return

    def point(self,l):
        self.points.append(self.r0+l*self.u)
        self.ls.append(float(l))
        return self.r0+l*self.u

    def pos(self,r):
        l = np.linalg.lstsq(np.transpose([self.u]),(r-self.r0))
        if l[1]<self.line_prec:
            self.points.append(r)
            self.ls.append(float(l[0]))
            return float(l[0])
        else:
            raise ValueError, "Point does not lie on Line"

    def minmax(self):
        return (np.min(self.ls),np.max(self.ls))

    def minmax_points(self):
        return (self.point(np.min(self.ls)),self.point(np.max(self.ls)))

    def intersect(self,line):
        ls = np.linalg.solve(np.transpose(np.vstack([line.u,-self.u])),self.r0-line.r0)
        line.point(ls[0])
        return self.point(ls[1])

class Point:
    def __init__(self, p, scriptline, moveable=False, show=False, on_lines=[]):
        self.p = p
        self.scriptline = scriptline

        self.moveable = moveable
        self.show = show
        self.on_lines = on_lines

        

class Pattern:

    def __init__(self,filename):
        self.script_lines = []

        self.measures = stabledict.StableDict()
        self.extrapars = stabledict.StableDict()
        self.points = stabledict.StableDict()
        self.lines = stabledict.StableDict()
        self.beziers = stabledict.StableDict()
 
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            self.directions = stabledict.StableDict({"up" : np.array((0.,1.)), "down" : np.array((0.,-1.)), "right": np.array((1.,0.)), "left": np.array((-1.,0.))})
            self.functions = stabledict.StableDict({"dist": self.dist, "sqrt": np.sqrt})

        self.alldicts = self.measures.copy()
        self.alldicts.update(self.points)
        self.alldicts.update(self.lines)
        self.alldicts.update(self.beziers)
        self.alldicts.update(self.directions)
        self.alldicts.update(self.functions)
        self.alldicts.update(self.extrapars)

        self.parse_file(filename)

    def dist(self,point1,point2):
        return np.sqrt(((point1-point2)**2).sum())

    def parse_file(self,filename):
        file_lines = open(filename).readlines()

        for l in file_lines:
            self.alldicts.update(self.measures)
            self.alldicts.update(self.points)
            self.alldicts.update(self.lines)
            self.alldicts.update(self.extrapars)
            self.alldicts.update(self.beziers)

            words = l.split()
            if len(words)==0: continue
            
            if words[0]=="measure":
                #measures[words[1]] = float(input(words[1]+": "))
                self.measures[words[1]] = 0. 
            elif words[0]=="extrapar":
                self.extrapars[words[1]] = eval(''.join(words[3:]),self.alldicts)
            elif words[0][0]=="#":
                pass
            else:
                self.script_lines.append(l)

    def measures_from_argv(self):
        count = 0
        for m in self.measures:
            count += 1
            self.measures[m] = float(sys.argv[count])
        self.parse_script()

    def measures_from_input(self):
        for m in self.measures:  self.measures[m] = float(input(m+": "))
        self.parse_script()

    def parse_script(self):
        li = 0
        for l in self.script_lines:
            self.alldicts.update(self.measures)
            self.alldicts.update(self.points)
            self.alldicts.update(self.lines)
            self.alldicts.update(self.extrapars)
            self.alldicts.update(self.beziers)

            words = l.split()
         
            if words[0]=="point":
                if words[2] == "is":
                    self.points[words[1]] = np.array(eval(''.join(words[3:]),self.alldicts))
                if words[2] == "on":
                    thisline = self.lines[words[3]]
                    self.points[words[1]] = thisline.point(thisline.pos(self.points[words[5]])+eval(''.join(words[7:]),self.alldicts))
                if words[2]=="intersect":
                    line1 = self.lines[words[3]]
                    line2 = self.lines[words[4]]
                    self.points[words[1]] = line1.intersect(line2)
            
            elif words[0]=="move":
                    self.points[words[1]] += np.array(eval(''.join(words[2:]),self.alldicts))

            elif words[0]=="line":
                if words[2] == "normal":
                    self.lines[words[1]] = VectorLine(self.points[words[3]],self.lines[words[4]],"normal")
                elif words[4] == "to":
                    self.lines[words[1]] = VectorLine(self.points[words[3]],self.points[words[5]],"two_points")
                else:
                    self.lines[words[1]] = VectorLine(self.points[words[3]],eval(words[4],self.alldicts))
            
            elif words[0]=="seamline":
                if self.beziers.has_key(words[1])==False:
                    temp = []
                    for i in words[2:]: temp.append(self.points[i])
                    self.beziers[words[1]] = [temp]
                else:
                    temp = []
                    for i in words[2:]: temp.append(self.points[i])
                    self.beziers[words[1]].append(temp)
            li += 1



"""
further ideas:
    point properties:
        moveable/fixed
        show/invis   (treat bezier control points as non visible, but show with handles)
        on_line => created by point on line => can only move 

    line properties:
        moveable/fixed -> moves support point
        show/invis
