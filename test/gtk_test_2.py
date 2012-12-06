#! /usr/bin/env python
import framework
from math import pi
import math
import cairo

class Transform(framework.Screen):
    def draw(self, ctx, width, height):
        ctx.scale (width, height) # Normalizing the canvas

        pat = cairo.LinearGradient (0.0, 0.0, 0.0, 1.0)
        pat.add_color_stop_rgba (1, 0.7, 0, 0, 0.5) # First stop, 50% opacity
        pat.add_color_stop_rgba (0, 0.9, 0.7, 0.2, 1) # Last stop, 100% opacity

        ctx.rectangle (0, 0, 1, 1) # Rectangle(x0, y0, x1, y1)
        ctx.set_source (pat)
        ctx.fill ()

        #ctx.translate (0.1, 0.1) # Changing the current transformation matrix
        ctx.translate (0.2, 0.1) # Changing the current transformation matrix

        ctx.move_to (0, 0)
        ctx.arc (0.2, 0.1, 0.1, -math.pi/2, 0) # Arc(cx, cy, radius, start_angle, stop_angle)
        ctx.line_to (0.5, 0.1) # Line to (x,y)
        ctx.curve_to (0.5, 0.2, 0.5, 0.4, 0.2, 0.8) # Curve(x1, y1, x2, y2, x3, y3)
        ctx.close_path ()

        ctx.set_source_rgb (0.3, 0.2, 0.5) # Solid color
        ctx.set_line_width (0.02)
        ctx.stroke ()


"""
        cr.set_source_rgb(0.5, 0.5, 0.5)
        cr.rectangle(0, 0, width, height)
        cr.fill()

        # draw a rectangle
        cr.set_source_rgb(1.0, 1.0, 1.0)
        cr.rectangle(10, 10, width - 20, height - 20)
        cr.fill()

        # set up a transform so that (0,0) to (1,1)
        # maps to (20, 20) to (width - 40, height - 40)
        cr.translate(20, 20)
        cr.scale((width - 40) / 1.0, (height - 40) / 1.0)

        # draw lines
        cr.set_line_width(0.01)
        cr.set_source_rgb(0.0, 0.0, 0.8)
        cr.move_to(1 / 3.0, 1 / 3.0)
        cr.rel_line_to(0, 1 / 6.0)
        cr.move_to(2 / 3.0, 1 / 3.0)
        cr.rel_line_to(0, 1 / 6.0)
        cr.stroke()

        # and a circle
        cr.set_source_rgb(1.0, 0.0, 0.0)
        radius = 1
        cr.arc(0.5, 0.5, 0.5, 0, 2 * pi)
        cr.stroke()
        cr.arc(0.5, 0.5, 0.33, pi / 3, 2 * pi / 3)
        cr.stroke()
"""


framework.run(Transform)
