# -*- coding: utf-8 -*-

"""
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

    Dieses Programm ist Freie Software: Sie können es unter den Bedingungen
    der GNU General Public License, wie von der Free Software Foundation,
    Version 3 der Lizenz oder (nach Ihrer Option) jeder späteren
    veröffentlichten Version, weiterverbreiten und/oder modifizieren.

    Dieses Programm wird in der Hoffnung, dass es nützlich sein wird, aber
    OHNE JEDE GEWÄHRLEISTUNG, bereitgestellt; sogar ohne die implizite
    Gewährleistung der MARKTFÄHIGKEIT oder EIGNUNG FÜR EINEN BESTIMMTEN ZWECK.
    Siehe die GNU General Public License für weitere Details.

    Sie sollten eine Kopie der GNU General Public License zusammen mit diesem
    Programm erhalten haben. Wenn nicht, siehe <http://www.gnu.org/licenses/>.
"""

import numpy as np
import sys
import warnings
import copy
import scipy.optimize


#def solve_quadratic(a,b,c,d):
#    cc = c-d
#    return np.array([(-b + np.sqrt(b**2 - 4*a*cc))/(2*a),(-b - np.sqrt(b**2 - 4*a*cc))/(2*a)])

class VectorLine:

    def __init__(self,name,scriptline,r0,u,form_mode="parameter",fixed=False, belongs_to_sheet="None"):
        self.name = name
        self.scriptline = scriptline
        self.points = []
        self.ls = []
        self.line_prec = 1e-10
        self.fixed = fixed
        self.belongs_to_sheets = [belongs_to_sheet]
        
        if (form_mode == "parameter"):
            self.r0 = np.array(r0.p)
            self.ls.append(0)
            self.points.append(r0)
            self.u = np.array(u)
        elif (form_mode == "two_points"):
            self.r0 = np.array(r0.p)
            self.u = self.r0 - np.array(u.p)
            self.u /= np.sqrt((self.u**2).sum())
            self.pos(r0)
            self.pos(u)
            self.fixed = True
        elif (form_mode == "normal"):
            self.r0 = np.array(r0.p)
            self.u = np.array([-u.u[1], u.u[0]])
            self.u /= np.sqrt((self.u**2).sum())
            self.ls.append(0)
            self.points.append(r0)

    def calc_from_two_points(a,b):
        return

    def support_point(self):
        return self.points[0]

    def point(self,l):
        self.points.append(self.r0+l*self.u)
        self.ls.append(float(l))
        return self.r0+l*self.u

    def pos(self,r):
        l = np.linalg.lstsq(np.transpose([self.u]),(r.p-self.r0))
        if l[1]<self.line_prec:
            self.points.append(r)
            self.ls.append(float(l[0]))
            return float(l[0])
        else:
            raise ValueError, "Point does not lie on Line "+self.name+" "+str(l[1])+" : "+str(r.p)+" - "+str(self.r0)

    def minmax(self):
        return (np.min(self.ls),np.max(self.ls))

    def minmax_points(self):
        return (self.point(np.min(self.ls)),self.point(np.max(self.ls)))

    def intersect(self,line):
        ls = np.linalg.solve(np.transpose(np.vstack([line.u,-self.u])),self.r0-line.r0)
        line.point(ls[0])
        return self.point(ls[1])

    def with_dist(self, point, dist, entry):
        if (entry=="min"):
            l = scipy.optimize.fsolve(lambda l: np.linalg.norm(self.r0 - point.p + l*self.u) - dist, -dist)
        elif (entry=="max"):
            l = scipy.optimize.fsolve(lambda l: np.linalg.norm(self.r0 - point.p + l*self.u) - dist, dist)
        else:
            raise ValueError, "entry must be min or max"
        self.point(l)
        return self.point(l)

class Point:
    def __init__(self, name, scriptline, p, fixed=False, show=False, on_lines=[], belongs_to_sheet="None"):
        self.name = name
        self.p = copy.deepcopy(p)
        self.scriptline = scriptline

        self.fixed = fixed
        self.show = show
        self.on_lines = on_lines

        self.acc_change = np.array([0.,0.])
        self.acc_lambda = 0.

        self.belongs_to_sheets = [belongs_to_sheet]

        if len(on_lines)>1: self.fixed = True

    def move_by(self,other):
        self.p += other

    def dist(self,other):
        return np.sqrt(((self.p-other.p)**2).sum())
        

class Pattern:

    def __init__(self,filename):
        self.script_lines = []
 
        self.measures = {}
        self.extrapars = {}
        self.points = {}
        self.lines = {}
        self.beziers = {}
        self.measurenames = {}
        self.bezier_belongsto = {}

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            self.directions = {"up" : np.array((0.,1.)), "down" : np.array((0.,-1.)), "right": np.array((1.,0.)), "left": np.array((-1.,0.))}
            self.functions = {"dist": self.dist, "sqrt": np.sqrt, "normal": self.normal}

        self.alldicts = self.measures.copy()
        self.alldicts.update(self.points)
        self.alldicts.update(self.lines)
        self.alldicts.update(self.beziers)
        self.alldicts.update(self.directions)
        self.alldicts.update(self.functions)
        self.alldicts.update(self.extrapars)
        self.alldicts.update(self.measurenames)
        self.alldicts.update(self.bezier_belongsto)

        self.calc_num = 0
        self.sheets = []
        self.name = "Unknown"

        self.parse_file(filename)
        self.filename = filename

    def return_data(self):
        return [self.script_lines, self.measures, self.extrapars, self.points, self.lines, self.beziers, self.measurenames, self.calc_num, self.bezier_belongsto, self.sheets]

    def input_data(self,data):
        self.script_lines = copy.deepcopy(data[0])
        self.measures = copy.deepcopy(data[1])
        self.extrapars = copy.deepcopy(data[2]) 
        self.points = copy.deepcopy(data[3])
        self.lines = copy.deepcopy(data[4])
        self.beziers = copy.deepcopy(data[5])
        self.measurenames = copy.deepcopy(data[6])
        self.calc_num = copy.deepcopy(data[7])
        self.bezier_belongsto = copy.deepcopy(data[8])
        self.sheets = copy.deepcopy(data[9])

        self.alldicts = self.measures.copy()
        self.alldicts.update(self.points)
        self.alldicts.update(self.lines)
        self.alldicts.update(self.beziers)
        self.alldicts.update(self.directions)
        self.alldicts.update(self.functions)
        self.alldicts.update(self.extrapars)
        self.alldicts.update(self.measurenames)
        self.alldicts.update(self.bezier_belongsto)


    def dist(self,point1,point2):
        return point1.dist(point2)

    def normal(self, u):
        return np.array([-u[1], u[0]])

    def parse_file(self,filename):
        file_lines = open(filename).readlines()

        for l in file_lines:
            self.alldicts.update(self.measures)
            self.alldicts.update(self.points)
            self.alldicts.update(self.lines)
            self.alldicts.update(self.extrapars)
            self.alldicts.update(self.beziers)
            self.alldicts.update(self.measurenames)
            self.alldicts.update(self.bezier_belongsto)

            words = l.split()
            if len(words)==0: continue
            
            if words[0]=="measure":
                self.measures[words[1]] = float(words[3])
                self.measurenames[words[1]] = words[2]
            elif words[0]=="extrapar":
                self.extrapars[words[1]] = eval(''.join(words[3:]),self.alldicts)
            elif words[0]=="name":
                self.name = ' '.join(words[1:])
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

    def reset_to_measures(self):
        self.calc_num = 0
        self.parse_script()

    def parse_script(self,startline = -1):
        li = startline+1
        self.beziers = {}
        self.sheets = []
        belongs_to_sheet = "None"
        for l in self.script_lines:
            self.alldicts.update(self.measures)
            self.alldicts.update(self.points)
            self.alldicts.update(self.lines)
            self.alldicts.update(self.extrapars)
            self.alldicts.update(self.beziers)
            self.alldicts.update(self.bezier_belongsto)

            words = l.split()
            
            if words[0]=="start":
                belongs_to_sheet = words[1]
                self.sheets.append(words[1])
            elif words[0]=="print":
                print eval(''.join(words[1:]),self.alldicts)
            elif words[0]=="sheet":
                if words[2]=="add":
                    for w in words[3:]:
                        self.alldicts[w].belongs_to_sheets.append(words[1])
                if words[2]=="show":
                    for w in words[3:]:
                        self.bezier_belongsto[w].append(words[1])
            elif words[0]=="point":
                if words[2] == "is":
                    val = np.array(eval(''.join(words[3:]),self.alldicts))
                    on_lines = []
                    fixed=False
                if words[2] == "from":
                    thisline = self.lines[words[5]]
                    val = thisline.with_dist(self.points[words[3]],eval(''.join(words[8:]),self.alldicts), words[7])
                    on_lines = [thisline]
                    fixed=False
                if words[2] == "on":
                    thisline = self.lines[words[3]]
                    val = thisline.point(thisline.pos(self.points[words[5]])+eval(''.join(words[7:]),self.alldicts))
                    on_lines=[thisline]
                    fixed=False
                if words[2]=="intersect":
                    line1 = self.lines[words[3]]
                    line2 = self.lines[words[4]]
                    val = line1.intersect(line2)
                    on_lines=[line1,line2]
                    fixed=True
                if (self.calc_num == 0):
                    self.points[words[1]] = Point(words[1], li, val, fixed=fixed,on_lines=on_lines, belongs_to_sheet=belongs_to_sheet)
                else:
                    self.points[words[1]].on_lines = on_lines
                    if len(on_lines) == 0:
                        self.points[words[1]].p = val+self.points[words[1]].acc_change
                    elif len(on_lines) == 1:
                        lambd = self.points[words[1]].acc_lambda
                        lambd += on_lines[0].pos(Point("temp",-1,val))
                        self.points[words[1]].p = on_lines[0].point(lambd)
                    elif len(on_lines)==2:
                        self.points[words[1]].p = val
            
            elif words[0]=="move":
                    self.points[words[1]].move_by(np.array(eval(''.join(words[2:]),self.alldicts)))

            elif words[0]=="line":
                if words[2] == "normal":
                    self.lines[words[1]] = VectorLine(words[1], li, self.points[words[3]],self.lines[words[4]],"normal", belongs_to_sheet=belongs_to_sheet)
                elif words[4] == "to":
                    self.lines[words[1]] = VectorLine(words[1], li, self.points[words[3]],self.points[words[5]],"two_points", fixed=True, belongs_to_sheet=belongs_to_sheet)
                else:
                    self.lines[words[1]] = VectorLine(words[1], li, self.points[words[3]],eval(words[4],self.alldicts), belongs_to_sheet=belongs_to_sheet)
            
            elif words[0]=="cutline":
                if self.beziers.has_key(words[1])==False:
                    temp = []
                    for i in words[2:]: temp.append(copy.deepcopy(self.points[i].p))
                    self.beziers[words[1]] = [temp]
                    self.bezier_belongsto[words[1]] = [belongs_to_sheet]
                else:
                    temp = []
                    for i in words[2:]: temp.append(copy.deepcopy(self.points[i].p))
                    self.beziers[words[1]].append(temp)
            li += 1
        self.calc_num += 1
