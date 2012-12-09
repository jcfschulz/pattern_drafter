#! /usr/bin/env python
import pygtk
pygtk.require('2.0')
import gtk, gobject, cairo

import copy
import numpy as np

import pattern


colors = {"black": (0,0,0), "red": (1,0,0), "green": (0,1,0)}

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
        #self.points = [ [0,0], [10,0], [20,0], [0,108], [40,0], [40,108] ]

        self.zoom = .9*1.
    
        self.translate_vector = [20.,20.]
        self.point_moving = False

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
            self.point_moving = True
        return True

    def do_button_release_event(self, event):
        if event.button == 1:
            self.point_moving = False
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
        for p in self.pattern.points.values():
            xx,yy = self.recalc(p.p)
            #yy = 1-yy
            if (np.sqrt( (xx - x)**2 + ((1-yy) - y)**2) < 0.01):
                if (self.point_moving==True):
                    dx,dy = self.reverse_recalc((xx - x, (yy - (1-y))))
                    p.p[0] -= dx
                    p.p[1] -= dy
                self.highlight_points.append(copy.deepcopy(p))
                break
        
        if len(self.highlight_points)>0:
            self.window.set_cursor(gtk.gdk.Cursor(gtk.gdk.HAND2))
        elif self.point_moving==True:
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


    def draw(self, width, height):
        self.width = float(width)
        self.height = float(height)
        self.aspect = self.width/self.height


        self.ctx.translate (self.translate_vector[0], self.translate_vector[1])
        self.ctx.scale (self.zoom*self.width, self.zoom*self.height)

        self.ctx.set_source_rgb (1, 1, 1)
        self.ctx.paint()

        for p in self.pattern.points.values():
            self.point(p.p,color="black")

        for p in self.highlight_points:
           self.point(p.p,color="red")

        self.ctx.stroke()


def run(Widget, pattern):
    window = gtk.Window()
    window.connect("delete-event", gtk.main_quit)
    
    #window.set_geometry_hints(min_aspect=0.5, max_aspect=0.5)
    window.set_default_size(200, 500)
    widget = Widget(pattern)
    widget.show()

    window.add(widget)
    window.present()
    gtk.main()

trouser = pattern.Pattern("trouser_script")
trouser.measures_from_argv()
run(PatternWidget, trouser)
