#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2011 Deepin, Inc.
#               2011 Wang Yong
#
# Author:     Wang Yong <lazycat.manatee@gmail.com>
#             Zhang Cheng <zhangcheng@linuxdeepin.com>
#             Hou ShaoHui <houshaohui@linuxdeepin.com>
#             Long Changjin <admin@longchangjin.cn>

# Maintainer: Wang Yong <lazycat.manatee@gmail.com>
#             Zhang Cheng <zhangcheng@linuxdeepin.com>
#             Hou Shaohui <houshaohui@linuxdeepin.com>
#             Long Changjin <admin@longchangjin.cn>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from action import *
#from utils import *
#from math import *
from draw import *
from constant import *
from window import *
from lang import _
from widget import RootWindow, RightMenu 
from toolbar import Colorbar, Toolbar

import pygtk
import subprocess

pygtk.require('2.0')
import gtk


class DeepinScreenshot():
    '''Main screenshot.'''
    def __init__(self, save_file=""):
        '''Init Main screenshot.'''
        # Init.
        self.action = ACTION_WINDOW
        self.screenshot_window_info = get_screenshot_window_info()
        self.width = SCREEN_WIDTH
        self.height = SCREEN_HEIGHT
        self.monitor_x = SCREEN_X
        self.monitor_y = SCREEN_Y
        self.x = self.y = self.rect_width = self.rect_height = 0

        self.save_op_index = SAVE_OP_AUTO

        #self.buttonToggle = None
        self.drag_position = None
        self.last_drag_position = None
        self.dragStartX = self.dragStartY = self.dragStartOffsetX = self.dragStartOffsetY = 0
        self.textDragOffsetX = self.textDragOffsetY = 0
        
        self.drag_flag = False
        self.show_toolbar_flag = False
        self.show_colorbar_flag = False 
        self.show_text_window_flag = False
        self.text_drag_flag = False
        self.text_modify_flag = False
        self.draw_text_layout_flag = False
        self.share_to_flag = False

        self.saveFiletype = 'png'
        self.saveFilename = save_file
        
        # make sure the toolbar in this monitor
        self.toolbarOffsetX = self.monitor_x + 10
        self.toolbarOffsetY = self.monitor_y + 10
        #self.toolbarOffsetX = 10
        #self.toolbarOffsetY = 10
        #self.toolbar_height = 50
        
        self.action_size = ACTION_SIZE_SMALL
        self.action_color = "#FF0000"
        self.font_name = "Sans"
        self.font_size = 10
        
        # default window 
        self.window_flag = True         # has not selected area or window
        
        # Init action list.
        self.current_action = None
        self.action_list = []
        self.current_text_action = None
        self.text_action_list = []
        self.text_action_info = {}

        # Get desktop background.
        self.desktop_background = self.get_desktop_snapshot()
        self.desktop_background_pixels= self.desktop_background.get_pixels()
        self.desktop_background_n_channels = self.desktop_background.get_n_channels()
        self.desktop_background_rowstride = self.desktop_background.get_rowstride()
        
        # Init window.
        self.window = RootWindow(self)
        
        # Init toolbar window.
        self.toolbar = Toolbar(self.window.window, self)
        
        # Init color window.
        self.colorbar = Colorbar(self.window.window, self)

        # Init text window
        #self.text_window = TextWindow(self.window.window, self)

        # right button press menu
        self.right_menu = RightMenu(self)
        # Show.
        self.window.show()
        self.window.set_cursor(ACTION_WINDOW)

    def set_action_type(self, aType):         # 设置操作类型
        '''Set action. type'''
        self.action = aType    
        self.current_action = None
    
    def save_snapshot(self, filename=None, filetype='png', clip_flag=False):
        '''Save snapshot.'''
        failed_flag = False
        tipContent = ""
        # Save snapshot.
        if self.rect_width == 0 or self.rect_height == 0:
            tipContent = _("Tip area width or height cannot be 0")
            failed_flag = True
        else:
            self.window.finish_flag = True
            surface = self.make_pic_file(
                self.desktop_background.subpixbuf(*self.get_rectangel_in_monitor()))
            # Save to file
            if filename:
                tipContent = "%s'%s'" % (_("Tip save to file"), filename)
                try:
                    surface.write_to_png(filename)
                    # copy to clipboard
                    if clip_flag:
                        pixbuf = gtk.gdk.pixbuf_new_from_file(filename)
                        clipboard = gtk.Clipboard(selection="CLIPBOARD")
                        clipboard.set_image(pixbuf)
                        clipboard.store()
                        tipContent += _("Tip save to clipboard")
                except Exception, e:
                    tipContent = "%s:%s" % (_("Tip save failed"), str(e))
            # Save snapshot to clipboard
            else:
                import StringIO
                fp = StringIO.StringIO()
                surface.write_to_png(fp)
                contents = fp.getvalue()
                fp.close()
                loader = gtk.gdk.PixbufLoader("png")
                loader.write(contents, len(contents))
                pixbuf = loader.get_pixbuf()
                loader.close()

                clipboard = gtk.Clipboard(selection="CLIPBOARD")
                if pixbuf:
                    clipboard.set_image(pixbuf)
                clipboard.store()
                tipContent += _("Tip save to clipboard")

        # Exit
        self.window.quit()
        if self.share_to_flag and not failed_flag:
            # share window
            win_x = self.monitor_x + (self.width / 2) - 300
            win_y = self.monitor_y + (self.height/ 2) - 200
            try:
                cmd = ('python2', 'share.py', filename, str(win_x), str(win_y))
                subprocess.Popen(cmd)
            except OSError:    
                cmd = ('python', 'share.py', filename, str(win_x), str(win_y))
                subprocess.Popen(cmd)
        
        # tipWindow
        try:
            cmd = ('python2', 'tipswindow.py', tipContent)
            subprocess.Popen(cmd)
        except OSError:    
            cmd = ('python', 'tipswindow.py', tipContent)
            subprocess.Popen(cmd)

    def make_pic_file(self, pixbuf):
        ''' use cairo make a picture file '''
        surface = cairo.ImageSurface(cairo.FORMAT_RGB24, pixbuf.get_width(), pixbuf.get_height())
        cr = cairo.Context(surface)
        gdkcr = gtk.gdk.CairoContext(cr)
        gdkcr.set_source_pixbuf(pixbuf, 0, 0)
        gdkcr.paint()

        for action in self.action_list:
            if action is not None:
                action.start_x -= self.x
                action.start_y -= self.y
                if not isinstance(action, (TextAction)):
                    action.end_x -= self.x
                    action.end_y -= self.y
                if isinstance(action, (LineAction)):
                    for track in action.track:
                        track[0] -= self.x
                        track[1] -= self.y
                action.expose(cr)
        
        # Draw Text Action list.
        for each in self.text_action_list:
            if each is not None:
                each.expose(cr)
        return surface

    def get_desktop_snapshot(self):
        '''Get desktop snapshot.'''
        return get_screenshot_pixbuf()
        
    def undo(self, widget=None):
        '''Undo'''
        if self.show_text_window_flag:
            self.window.hide_text_window()
        if self.current_text_action:
            self.current_text_action = None

        if self.action_list:        # undo the previous action
            tempAction = self.action_list.pop()
            if tempAction.get_action_type() == ACTION_TEXT:
                self.text_action_list.pop()
                if tempAction in self.text_action_info:
                    del self.text_action_info[tempAction]
        else:       # back to select area
            self.window.set_cursor(ACTION_WINDOW)
            self.action = ACTION_WINDOW
            self.x = self.y = self.rect_width = self.rect_height = 0
            self.window_flag = True
            self.drag_flag = False
            if self.show_colorbar_flag:
                self.toolbar.set_all_inactive()
            self.window.hide_toolbar()
            self.window.hide_colorbar()
        self.window.refresh()
        
    def get_rectangel(self):
        '''get select rectangle'''
        return (int(self.x), int(self.y), int(self.rect_width), int(self.rect_height))
    
    def get_rectangel_in_monitor(self):
        '''get select rectangle in the monitor'''
        return (int(self.x-self.monitor_x), int(self.y-self.monitor_y),
                int(self.rect_width), int(self.rect_height))
    
    def get_monitor_info(self):
        '''get monitor info'''
        return (self.monitor_x, self.monitor_y, self.width, self.height)
    
def main(name=""):
    ''' main function '''
    gtk.gdk.threads_init()
    DeepinScreenshot(name)
    gtk.main()

if __name__ == '__main__':
    main()
