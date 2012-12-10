#! /usr/bin/env python
import pygtk
pygtk.require('2.0')
import gtk, gobject, cairo

import copy
import numpy as np

import pattern


colors = {"black": (0,0,0), "red": (1,0,0), "green": (0,1,0), "grey": (0.5,0.5,0.5), "orange": (255/255.,127/255.,80/255.), "white": (1,1,1)}

class PatternWidget(gtk.DrawingArea):
    __gsignals__ = { "expose-event": "override", "motion-notify-event": "override", "button-press-event": "override", "button-release-event": "override", "scroll-event": "override"}

    def __init__(self, thispattern):
        super(gtk.DrawingArea, self).__init__()
        self.set_events(gtk.gdk.EXPOSURE_MASK
                            | gtk.gdk.LEAVE_NOTIFY_MASK
                            | gtk.gdk.BUTTON_PRESS_MASK
                            | gtk.gdk.BUTTON_RELEASE_MASK
                            | gtk.gdk.POINTER_MOTION_MASK
                            | gtk.gdk.SCROLL_MASK
                            | gtk.gdk.POINTER_MOTION_HINT_MASK)
        
        self.highlight_points = []

        self.zoom = .9*1.
    
        self.translate_vector = [30.,30.]
        self.point_moving = False
        self.canvas_moving = False
        self.move_point = -1

        self.pattern = thispattern

        self.maxheight = 0.
        self.maxwidth = 0.
        for p in self.pattern.points.values():
            if p.p[0]>self.maxwidth: self.maxwidth=p.p[0]
            if p.p[1]>self.maxheight: self.maxheight=p.p[1]
        self.maxaspect = self.maxwidth/self.maxheight


    def do_expose_event(self, event):
        self.ctx = self.window.cairo_create()
        self.ctx.rectangle(event.area.x, event.area.y, event.area.width, event.area.height)
        self.ctx.clip()
        self.draw(*self.window.get_size())

    def do_button_press_event(self, event):
        if event.button == 1:
            self.oldx = event.x
            self.oldy = event.y
            if len(self.highlight_points)>0:  self.point_moving = True
            else: self.canvas_moving = True
        return True

    def do_button_release_event(self, event):
        if event.button == 1:
            self.point_moving = False
            self.canvas_moving = False
            self.move_point = -1
        return True
    
    def do_scroll_event(self, event):
        if (event.direction == gtk.gdk.SCROLL_UP):
#            self.translate_vector[0] -= event.x 
#            self.translate_vector[1] -= event.y
            self.zoom *= 1.1
        elif (event.direction == gtk.gdk.SCROLL_DOWN):
            self.zoom *= 0.9

    def do_motion_notify_event(self, event):
        if event.is_hint:
            x, y, state = event.window.get_pointer()
        else:
            x = event.x
            y = event.y
            state = event.state

        x-=self.translate_vector[0]
        y-=self.translate_vector[1]
        x /= self.width
        y /= self.height
        x/=self.zoom
        y/=self.zoom

        self.highlight_points = []
        if (self.point_moving==True):
            p = self.pattern.points.values()[self.move_point]
            if p.fixed != True:
                xx,yy = self.recalc(p.p)
                self.highlight_points = [ p ]
                dx,dy = self.reverse_recalc((xx - x, (yy - (1-y))))
                px = p.p[0] - dx
                py = p.p[1] - dy

                if len(p.on_lines)==1:
                    templine = pattern.VectorLine("temp", -1, pattern.Point("temp",-1,(px,py)), p.on_lines[0], "normal")
                    px,py = templine.intersect(p.on_lines[0])
                    templambda = p.on_lines[0].pos(pattern.Point("temp",-1,(px,py)))
                    p.acc_lambda += templambda - p.on_lines[0].pos(p)

                p.acc_change[0] += px - p.p[0]
                p.acc_change[1] += py - p.p[1]

                p.p[0] = px
                p.p[1] = py
                self.pattern.parse_script(p.scriptline)
        else:
            for p in self.pattern.points.values():
                xx,yy = self.recalc(p.p)
                if (np.sqrt( (xx - x)**2 + ((1-yy) - y)**2) < 0.01):
                    self.highlight_points.append(copy.deepcopy(p))
                    self.move_point = self.pattern.points.values().index(p)
                    break
        
        if len(self.highlight_points)>0:
            self.window.set_cursor(gtk.gdk.Cursor(gtk.gdk.HAND2))
        elif self.canvas_moving==True:
            self.window.set_cursor(gtk.gdk.Cursor(gtk.gdk.FLEUR))
            self.translate_vector[0] += (event.x - self.oldx)
            self.translate_vector[1] += (event.y - self.oldy)
        else:
            self.window.set_cursor(gtk.gdk.Cursor(gtk.gdk.ARROW))

        self.queue_draw()

        self.oldx = event.x
        self.oldy = event.y
        
        return True


    def recalc(self,point):
        pointx = point[0]
        pointy = point[1]
        if (self.aspect < self.maxaspect):            # width is limiting factor
            pointx /= self.maxwidth
            pointy *= self.aspect/self.maxaspect/self.maxheight
        else:            # height is limiting facto
            pointx *= self.maxaspect/self.aspect/self.maxwidth
            pointy /= self.maxheight
        return pointx,pointy

    def reverse_recalc(self,point):
        pointx = point[0]
        pointy = point[1]
        if (self.aspect < self.maxaspect):            # width is limiting factor
            pointx *= self.maxwidth
            pointy /= self.aspect/self.maxaspect/self.maxheight
        else:            # height is limiting facto
            pointx /= self.maxaspect/self.aspect/self.maxwidth
            pointy *= self.maxheight
        return pointx,pointy


    def point(self, point, pointsize=5, color="black"):
        pointx,pointy = self.recalc(point)
        self.ctx.set_source_rgb (colors[color][0],colors[color][1],colors[color][2])
        self.ctx.save()
        self.ctx.translate(pointx, 1-pointy)
        self.ctx.scale (1/(self.zoom*self.width), 1/(self.zoom*self.height)) 
        self.ctx.arc (0,0, 1, 0., 2*np.pi)
        self.ctx.set_line_width (pointsize)
        self.ctx.stroke()
        self.ctx.restore()


    def line(self,point1, point2, linewidth=1, color="black"):
        point1x,point1y = self.recalc(point1)
        point2x,point2y = self.recalc(point2)
        self.ctx.set_source_rgb (colors[color][0],colors[color][1],colors[color][2])
        self.ctx.move_to(point1x,1-point1y)
        self.ctx.line_to(point2x,1-point2y)
        self.ctx.save()
        self.ctx.scale (1/(self.zoom*self.width), 1/(self.zoom*self.height)) 
        self.ctx.set_line_width (linewidth)
        self.ctx.stroke()
        self.ctx.restore()

    def seamline(self, bez, linewidth=3, color="black", control_color="orange"):
        self.ctx.set_source_rgb (colors[color][0],colors[color][1],colors[color][2])

        point1x,point1y = self.recalc(bez[0][0])
        self.ctx.move_to(point1x,1-point1y)
        for b in bez:
            point2x,point2y = self.recalc(b[1])
            if len(b)==2:
                self.ctx.line_to(point2x,1-point2y)
            else:
                try:
                    point3x,point3y = self.recalc(b[2])
                    point4x,point4y = self.recalc(b[3])
                    self.ctx.curve_to(point2x,1-point2y, point3x,1-point3y, point4x,1-point4y)
                except IndexError: print b

        self.ctx.save()
        self.ctx.scale (1/(self.zoom*self.width), 1/(self.zoom*self.height)) 
        self.ctx.set_line_width (linewidth)
        self.ctx.stroke()
        self.ctx.restore()
        for b in bez:
            if len(b)==2: continue
            point1x,point1y = self.recalc(b[0])
            self.point(b[1],color=control_color)
            point2x,point2y = self.recalc(b[1])
            point3x,point3y = self.recalc(b[2])
            point4x,point4y = self.recalc(b[3])
            self.point(b[2],color=control_color)
            self.line(b[0],b[1],color=control_color)
            self.line(b[2],b[3],color=control_color)
    
    def draw_ruler(self):
        startpoint = reverse_recalc(0,0)
        pass
        

    def draw(self, width, height):
        self.width = float(width)
        self.height = float(height)
        self.aspect = self.width/self.height


        self.ctx.translate (self.translate_vector[0], self.translate_vector[1])
        self.ctx.scale (self.zoom*self.width, self.zoom*self.height)

        self.ctx.set_source_rgb (1, 1, 1)
        self.ctx.paint()


        tempcolor = "grey"
        #tempcolor = "white"
        for p in self.pattern.points.values():
            self.point(p.p,color=tempcolor)

        for l in self.pattern.lines.values():
            p1,p2 = l.minmax_points()
            self.line(p1,p2,color=tempcolor)

        for b in self.pattern.beziers.values():
            self.seamline(b, color="black", control_color="orange")


        for p in self.highlight_points:
           self.point(p.p,color="red")


        self.ctx.stroke()


def run(Widget, pattern):
    window = gtk.Window()
    window.connect("delete-event", gtk.main_quit)
    
    #window.set_geometry_hints(min_aspect=0.5, max_aspect=0.5)
    window.set_default_size(400, 900)
    window.maximize()

    widget = Widget(pattern)
    widget.show()

    window.add(widget)
    window.present()
    gtk.main()

trouser = pattern.Pattern("trouser_script")
trouser.measures_from_argv()
run(PatternWidget, trouser)


""" todo:
rulers
statusbar -> show pos
multiple pattern sheets + change buttons
buttons for: complete recalc, enter measures, save, export
export pdf/svg
real zoom
scroll bars
make bezier points freely moveable
"""
