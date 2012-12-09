#! /usr/bin/env python
import framework
from math import pi
import math
import cairo

colors = {"black": (0,0,0), "red": (1,0,0), "green": (0,1,0)}

class Transform(framework.Screen):

    def recalc(self,point):
        pointx = point[0]
        pointy = point[1]
        if (self.aspect < self.maxaspect):
            # width is limiting factor
            pointx /= self.maxwidth
            pointy *= self.aspect/self.maxaspect/self.maxheight
        else:
            # height is limiting facto
            pointx *= self.maxaspect/self.aspect/self.maxwidth
            pointy /= self.maxheight
        return pointx,pointy


    def point(self, point, pointsize=10, color="black"):
        pointx,pointy = self.recalc(point)
        self.ctx.set_source_rgb (colors[color][0],colors[color][1],colors[color][2])
        self.ctx.save()
        self.ctx.translate(pointx, pointy)
        self.ctx.scale (1/(self.zoom*self.width), 1/(self.zoom*self.height)) 
        self.ctx.arc (0,0, 1, 0., 2*math.pi)
        self.ctx.set_line_width (pointsize)
        self.ctx.stroke()
        self.ctx.restore()

    def draw(self, ctx, width, height):
        self.width = float(width)
        self.height = float(height)
        self.aspect = self.width/self.height
        self.ctx = ctx
        self.zoom = .9*1.
    
        self.maxheight = 108.
        self.maxwidth = 40.
        self.maxaspect = self.maxwidth/self.maxheight

        ctx.scale (self.zoom*self.width, self.zoom*self.height) # Normalizing the canvas
        ctx.set_source_rgb (1, 1, 1)
        ctx.paint()

        ctx.translate (0.05, 0.05)
        self.point((0,0),color="red")
        self.point((0,self.maxheight),color="red")
        self.point((self.maxwidth,0),color="red")
        self.point((self.maxwidth,self.maxheight),color="green")

        self.ctx.stroke()

framework.run(Transform)
