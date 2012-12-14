#! /usr/bin/env python
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

import pygtk
pygtk.require('2.0')
import gtk, gobject, cairo

import copy, pickle
import numpy as np

import pattern


def about_dialogue(event):
    dialog = gtk.MessageDialog(
        None,
        gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
        gtk.MESSAGE_QUESTION,
        gtk.BUTTONS_OK,
        None)
    dialog.set_markup('Pattern Draw 0.0.1')
    dialog.format_secondary_text("2012 by Julius Schulz \n Licensed under GPL")
    dialog.show_all()

    a = dialog.run()
    dialog.destroy()

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

        self.zoom = .9
    
        self.translate_vector_start = [100.,50.]
        self.translate_vector = copy.deepcopy(self.translate_vector_start)
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

        self.construction_color = "grey"
        self.bezier_color = "orange"
        self.showconstruct = True

        self.move_to_next_sheet = [2*self.maxwidth,0]

        self.save_name = "Untitled.pyc"

        self.context_id = 0

    def do_expose_event(self, event):
        self.ctx = self.window.cairo_create()
        self.ctx.rectangle(event.area.x, event.area.y, event.area.width, event.area.height)
        self.ctx.clip()
        self.draw(*self.window.get_size())

    def responseToDialog(self, entry, dialog, response):
        dialog.response(response)

    def getText_measures(self):
        dialog = gtk.MessageDialog(
            None,
            gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
            gtk.MESSAGE_QUESTION,
            gtk.BUTTONS_OK,
            None)
        dialog.set_markup('Please enter your measurements:')
    
        entries = {}
        hboxes = {}
        texts = {}

        for m in self.pattern.measures:
            entries[m] = gtk.Entry()
            entries[m].set_text(str(self.pattern.measures[m]))
            entries[m].connect("activate", self.responseToDialog, dialog, gtk.RESPONSE_OK)
            hboxes[m] = gtk.HBox()
            hboxes[m].pack_start(gtk.Label(self.pattern.measurenames[m]), False, 5, 5)
            hboxes[m].pack_end(entries[m])
            dialog.vbox.pack_start(hboxes[m], True, True, 0)

        dialog.show_all()

        a = dialog.run()
        if (a == gtk.RESPONSE_OK):
            for e in entries:
                texts[e] = entries[e].get_text()
        dialog.destroy()
        return texts

    def getText_extrapars(self):
        dialog = gtk.MessageDialog(
            None,
            gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
            gtk.MESSAGE_QUESTION,
            gtk.BUTTONS_OK,
            None)
        dialog.set_markup('Please enter your measurements:')
    
        entries = {}
        hboxes = {}
        texts = {}

        dialog.set_default_size(800, 800)

        scroll = gtk.ScrolledWindow()
        dialog.vbox.pack_start(scroll)
        myvbox = gtk.VBox()

        for m in self.pattern.extrapars:
            entries[m] = gtk.Entry()
            entries[m].set_text(str(self.pattern.extrapars[m]))
            entries[m].connect("activate", self.responseToDialog, dialog, gtk.RESPONSE_OK)
            hboxes[m] = gtk.HBox()
            hboxes[m].pack_start(gtk.Label(m), False, 5, 5)
            hboxes[m].pack_end(entries[m])
            myvbox.pack_start(hboxes[m], False, False, 0)
        
        scroll.add_with_viewport(myvbox)
        dialog.set_size_request(500, 500)
    
        dialog.show_all()

        a = dialog.run()
        if (a == gtk.RESPONSE_OK):
            for e in entries:
                texts[e] = entries[e].get_text()
        dialog.destroy()
        return texts



    def do_button_press_event(self, event):
        if event.button == 1:
            self.oldx = event.x
            self.oldy = event.y
            if len(self.highlight_points)>0:  self.point_moving = True
            else: self.canvas_moving = True
        self.queue_draw()
        return True

    def do_button_release_event(self, event):
        if event.button == 1:
            self.point_moving = False
            self.canvas_moving = False
            self.move_point = -1
        self.queue_draw()
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

        temp = (x,1-y)
        tx,ty = self.reverse_recalc(temp)
        self.statusbar.push(self.pos_id, "Position: "+str(round(tx,2))+", "+str(round(ty,2)))

        self.highlight_points = []
        if (self.point_moving==True):
            p = self.pattern.points.values()[self.move_point]
            if p.fixed != True:
                temp = self.move_to_next_sheet
                tx,ty = self.recalc(temp)
                xx,yy = self.recalc(p.p)

                try:
                    s = self.pattern.sheets.index(p.belongs_to_sheets[0])
                except ValueError: pass
                xx += s*tx
                yy += s*ty

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
                temp = self.move_to_next_sheet
                tx,ty = self.recalc(temp)
                xx,yy = self.recalc(p.p)

                try:
                    s = self.pattern.sheets.index(p.belongs_to_sheets[0])
                except ValueError: pass
                xx += s*tx
                yy += s*ty

                if (np.sqrt( (xx - x)**2 + ((1-yy) - y)**2) < 0.005):
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
        else:            # height is limiting factor
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

    def seamline(self, bez, linewidth=3, color="black", control_color="orange", show_control=True):
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
        if (self.showconstruct and show_control):
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
     
    def showshide_construction(self, event):
        self.showconstruct = not self.showconstruct
        self.queue_draw()

    def reset_view(self, event):
        self.translate_vector = copy.deepcopy(self.translate_vector_start)
        self.zoom = .9
        self.queue_draw()

    def reset_measures(self, event):
        self.pattern.reset_to_measures()
        self.queue_draw()

    def change_measures(self, event):
        new_measures = self.getText_measures()
        for m in new_measures:
            self.pattern.measures[m] = float(new_measures[m])
        self.pattern.reset_to_measures()
        self.queue_draw()

    def change_extrapars(self, event):
        new_extrapars = self.getText_extrapars()
        for m in new_extrapars:
            self.pattern.extrapars[m] = eval(new_extrapars[m])
        self.pattern.parse_script(0)
        self.queue_draw()

    def open_pattern(self, event):
        chooser = gtk.FileChooserDialog(title=None,action=gtk.FILE_CHOOSER_ACTION_OPEN,
                                  buttons=(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_OPEN,gtk.RESPONSE_OK))
        response = chooser.run()
        if response == gtk.RESPONSE_OK:
            self.pattern = pattern.Pattern(chooser.get_filename())
            self.pattern.parse_script()
            self.queue_draw()
        chooser.destroy()

    def load_state(self, event):
        chooser = gtk.FileChooserDialog(title=None,action=gtk.FILE_CHOOSER_ACTION_OPEN,
                                  buttons=(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_OPEN,gtk.RESPONSE_OK))
        response = chooser.run()
        if response == gtk.RESPONSE_OK:
            self.save_name = chooser.get_filename()
            data = pickle.load( open( self.save_name, "r" ) )
            self.pattern.input_data(data)
            self.queue_draw()
        chooser.destroy()
        self.window.set_title("** Pattern Draw   --   " + self.pattern.filename+"    ( "+self.save_name +" )")


    def save_state(self, event):
        chooser = gtk.FileChooserDialog(title=None,action=gtk.FILE_CHOOSER_ACTION_SAVE,
                                  buttons=(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_OPEN,gtk.RESPONSE_OK))
        response = chooser.run()
        if response == gtk.RESPONSE_OK:
            self.save_name = chooser.get_filename()
            pickle.dump( self.pattern.return_data(), open( self.save_name, "wb" ), -1 )
        chooser.destroy()

        self.window.set_title("** Pattern Draw   --   " + self.pattern.filename+"    ( "+self.save_name +" )")

    def export_chooser(self, event):
        chooser = gtk.FileChooserDialog(title=None,action=gtk.FILE_CHOOSER_ACTION_SAVE,
                                  buttons=(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_OPEN,gtk.RESPONSE_OK))
        response = chooser.run()
        if response == gtk.RESPONSE_OK:
            export_name = chooser.get_filename()
            self.export_to_file(export_name)
        chooser.destroy()

    def export_to_file(self, filename="Untitled.pdf", construction_color="grey", color="black", construction_pointsize=1, construction_linewidth=0.1, linewidth=0.3):
        conv = lambda x: 28.3464567*x 

        construction_pointsize = conv(construction_pointsize)
        construction_linewidth = conv(construction_linewidth)
        linewidth = conv(linewidth)

        s_num = len(self.pattern.sheets)
        width = conv( 10 + s_num*self.maxwidth + (s_num-1)*self.move_to_next_sheet[0] + 10)
        height = conv( 10 + self.maxheight + 10)

        if filename.split(".")[1] == "pdf":
            #print "PDF: ", filename
            surface = cairo.PDFSurface(filename.split(".")[0] + '.pdf', width, height)
        elif filename.split(".")[1] == "svg":
            #print "SVG: ", filename
            surface = cairo.SVGSurface(filename.split(".")[0] + '.svg', width, height)
        cr = cairo.Context(surface)

        cr.translate(conv(10), conv(10))

        for s in range(len(self.pattern.sheets)):
            if (self.showconstruct):
                for p in self.pattern.points.values():
                    if self.pattern.sheets[s] in p.belongs_to_sheets:
                        pointx,pointy = p.p
                        cr.set_source_rgb (colors[construction_color][0],colors[construction_color][1],colors[construction_color][2])
                        cr.save()
                        cr.translate(conv(pointx), conv(self.maxheight-pointy))
                        cr.arc (0,0, 1, 0., 2*np.pi)
                        cr.set_line_width (construction_pointsize)
                        cr.stroke()
                        cr.restore()
                for l in self.pattern.lines.values():
                    if self.pattern.sheets[s] in l.belongs_to_sheets:
                        p1,p2 = l.minmax_points()
                        point1x,point1y = p1
                        point2x,point2y = p2
                        cr.set_source_rgb (colors[construction_color][0],colors[construction_color][1],colors[construction_color][2])
                        cr.move_to(conv(point1x), conv(self.maxheight-point1y))
                        cr.line_to(conv(point2x), conv(self.maxheight-point2y))
                        cr.save()
                        cr.set_line_width(construction_linewidth)
                        cr.stroke()
                        cr.restore()
            for b in self.pattern.beziers:
                if self.pattern.sheets.index(self.pattern.bezier_belongsto[b][0])==s:
                    cr.set_source_rgb (colors[color][0],colors[color][1],colors[color][2])
                    bez = self.pattern.beziers[b]
                    point1x,point1y = bez[0][0]
                    cr.move_to(conv(point1x), conv(self.maxheight-point1y))
                    for bb in bez:
                        point2x,point2y = bb[1]
                        if len(bb)==2:
                            cr.line_to(conv(point2x), conv(self.maxheight-point2y))
                        else:
                            try:
                                point3x,point3y = bb[2]
                                point4x,point4y = bb[3]
                                cr.curve_to(conv(point2x), conv(self.maxheight-point2y), conv(point3x), conv(self.maxheight-point3y), conv(point4x), conv(self.maxheight-point4y))
                            except IndexError: print "IndexError", bb

                    cr.save()
                    cr.set_line_width (linewidth)
                    cr.stroke()
                    cr.restore()
                if (self.showconstruct):
                    for other in self.pattern.bezier_belongsto[b][1:]:
                        if self.pattern.sheets.index(other)==s:
                            cr.set_source_rgb (colors[construction_color][0],colors[construction_color][1],colors[construction_color][2])
                            bez = self.pattern.beziers[b]
                            point1x,point1y = bez[0][0]
                            cr.move_to(conv(point1x), conv(self.maxheight-point1y))
                            for bb in bez:
                                point2x,point2y = bb[1]
                                if len(bb)==2:
                                    cr.line_to(conv(point2x), conv(self.maxheight-point2y))
                                else:
                                    try:
                                        point3x,point3y = bb[2]
                                        point4x,point4y = bb[3]
                                        cr.curve_to(conv(point2x), conv(self.maxheight-point2y), conv(point3x), conv(self.maxheight-point3y), conv(point4x), conv(self.maxheight-point4y))
                                    except IndexError: print "IndexError", bb

                            cr.save()
                            cr.set_line_width (construction_linewidth)
                            cr.stroke()
                            cr.restore()
            
            tx,ty = self.move_to_next_sheet
            cr.translate(conv(tx), conv(ty))
    
        cr.show_page()
        surface.finish()

    def draw(self, width, height):
        self.width = float(width)
        self.height = float(height)
        self.aspect = self.width/self.height


        self.ctx.translate (self.translate_vector[0], self.translate_vector[1])
        self.ctx.scale (self.zoom*self.width, self.zoom*self.height)

        self.ctx.set_source_rgb (1, 1, 1)
        self.ctx.paint()

        for s in range(len(self.pattern.sheets)):
            if (self.showconstruct):
                for p in self.pattern.points.values():
                    if self.pattern.sheets[s] in p.belongs_to_sheets:
                        self.point(p.p,color=self.construction_color)
                for l in self.pattern.lines.values():
                    if self.pattern.sheets[s] in l.belongs_to_sheets:
                        p1,p2 = l.minmax_points()
                        self.line(p1,p2,color=self.construction_color)
                for p in self.highlight_points:
                    if self.pattern.sheets[s] in p.belongs_to_sheets:
                        self.point(p.p,color="green")
            for b in self.pattern.beziers:
                if self.pattern.sheets.index(self.pattern.bezier_belongsto[b][0])==s:
                    self.seamline(self.pattern.beziers[b], color="black", control_color=self.bezier_color)
                if (self.showconstruct):
                    for other in self.pattern.bezier_belongsto[b][1:]:
                        if self.pattern.sheets.index(other)==s:
                            self.seamline(self.pattern.beziers[b], color="black", linewidth=1, control_color=self.bezier_color, show_control=False)
            
            temp = self.move_to_next_sheet
            tx,ty = self.recalc(temp)
            self.ctx.translate(tx, ty)




def run(Widget, pattern):
    window = gtk.Window()
    window.connect("delete-event", gtk.main_quit)
    
    window.set_default_size(800, 800)
    window.maximize()

    canvas = gtk.Table(20, 10, False)
    window.add(canvas)
    canvas.show()

    pattern_canvas = Widget(pattern)
    canvas.attach(pattern_canvas,1,10,0,19)
    pattern_canvas.show()

    btn1 = gtk.Button("Load Pattern")
    btn1.connect("clicked", pattern_canvas.open_pattern)
    btn2 = gtk.Button("Load State")
    btn2.connect("clicked", pattern_canvas.load_state)
    btn3 = gtk.Button("Save State")
    btn3.connect("clicked", pattern_canvas.save_state)
    btn4 = gtk.Button("Export PDF/SVG")
    btn4.connect("clicked", pattern_canvas.export_chooser)


    btn5 = gtk.Button("Change Measures")
    btn5.connect("clicked", pattern_canvas.change_measures)
    btn_editextrapars = gtk.Button("Change Extra Parameters")
    btn_editextrapars.connect("clicked", pattern_canvas.change_extrapars)
    btn6 = gtk.Button("Reset to measures")
    btn6.connect("clicked", pattern_canvas.reset_measures)

    btn7 = gtk.Button("Reset View")
    btn7.connect("clicked", pattern_canvas.reset_view)
    btn8 = gtk.Button("Show/Hide Construction Points")
    btn8.connect("clicked", pattern_canvas.showshide_construction)

    btn_about = gtk.Button("About")
    btn_about.connect("clicked", about_dialogue)



    canvas.attach(btn1,0,1,0,1,xpadding=5)
    canvas.attach(btn2,0,1,1,2,xpadding=5)
    canvas.attach(btn3,0,1,2,3,xpadding=5)
    canvas.attach(btn4,0,1,3,4,xpadding=5)

    canvas.attach(btn5,0,1,4,5,xpadding=5)
    canvas.attach(btn_editextrapars,0,1,5,6,xpadding=5)
    canvas.attach(btn6,0,1,6,7,xpadding=5)

    canvas.attach(btn7,0,1,7,8,xpadding=5)
    canvas.attach(btn8,0,1,8,9,xpadding=5)

    canvas.attach(btn_about,0,1,9,10,xpadding=5)

    btn1.show()
    btn2.show()
    btn3.show()
    btn4.show()
    btn5.show()
    btn_editextrapars.show()
    btn6.show()
    btn7.show()
    btn8.show()
    btn_about.show()

    statusbar = gtk.Statusbar()
    statusbar.show()
    canvas.attach(statusbar,0,10,19,20)
    pattern_canvas.statusbar = statusbar
    pattern_canvas.pos_id = statusbar.get_context_id("Position")


    accel_group = gtk.AccelGroup()
    accel_group.connect_group(ord('q'), gtk.gdk.CONTROL_MASK,
    gtk.ACCEL_LOCKED, gtk.main_quit)
    window.add_accel_group(accel_group) 

    gobject.set_prgname("Pattern Draw")
    window.set_title("Pattern Draw   --   " + pattern.filename+"    ( "+pattern_canvas.save_name +" )")

    window.present()
    gtk.main()


trouser = pattern.Pattern("trouser_script")
trouser.parse_script()
run(PatternWidget, trouser)


""" todo:
before release:
- finish back waist (incl darts)
- make back control points relative
- correct front trouser crotch curve
- nice title (half working)
- rulers
- export pdf/svg


after release:
intersect bezierline
measure bezierlength
advance change extrapars (on the fly, cancel reverts changes)
measurement tape
statusbar -> show pos
real zoom
scroll bars
make bezier points freely moveable
undo
add buttons: set comments
"""
