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
import gtk, gobject

import pattern
import pattern_widget

def about_dialogue(event):
    dialog = gtk.MessageDialog(
        None,
        gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
        gtk.MESSAGE_QUESTION,
        gtk.BUTTONS_OK,
        None)
    dialog.set_markup('Pattern Drafter 0.0.1')
    dialog.format_secondary_text("2012 by Julius Schulz \n Licensed under GPL")
    dialog.show_all()

    a = dialog.run()
    dialog.destroy()



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

    btn1 = gtk.Button("Load Draft")
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
    pattern_canvas.move_id = statusbar.get_context_id("Position of picked Point")


    accel_group = gtk.AccelGroup()
    accel_group.connect_group(ord('q'), gtk.gdk.CONTROL_MASK,
    gtk.ACCEL_LOCKED, gtk.main_quit)
    window.add_accel_group(accel_group) 

    gobject.set_prgname("Pattern Drafter")
#    window.set_title("Pattern Draw   --   " + pattern.filename+"    ( "+pattern_canvas.save_name +" )")
    window.set_title("Pattern Drafter  0.0.1   --   "+pattern.name)

    window.present()
    gtk.main()


this_pattern = pattern.Pattern("trouser_script")
this_pattern.parse_script()
run(pattern_widget.PatternWidget, this_pattern)
