# -*- coding: iso-8859-1 -*-

#   Copyright 2010 Pepijn de Vos
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

from Quartz import *
from AppKit import NSEvent
from base import PyMouseMeta, PyMouseEventMeta
from time import time

pressID = [None, kCGEventLeftMouseDown, kCGEventRightMouseDown, kCGEventOtherMouseDown]
releaseID = [None, kCGEventLeftMouseUp, kCGEventRightMouseUp, kCGEventOtherMouseUp]
dragID = [ None, kCGEventLeftMouseDragged, kCGEventRightMouseDragged, kCGEventOtherMouseDragged ]

class PyMouse(PyMouseMeta):

    def __init__(self, *args):
        PyMouseMeta.__init__(self, *args)
        self.buttondown = [ False, False, False, False ]
        self.last_click_button = None
        self.last_click_time = 0
        self.last_click_count = 0

    def _double_click_time(self):
        # TODO: Read system setting for double click time.
        return 0.5

    def press(self, x, y, button = 1):

        event = CGEventCreateMouseEvent(None, pressID[button], (x, y), button - 1)

        # Detect double/triple clicks:

        now = time()

        if button != self.last_click_button \
           or (now - self.last_click_time) > self._double_click_time():
           self.last_click_count = 0

        self.last_click_count += 1

        # Set number-of-clicks field:

        CGEventSetIntegerValueField(event, kCGMouseEventClickState,
                                    self.last_click_count)

        CGEventPost(kCGHIDEventTap, event)

        self.buttondown[button] = True
        self.last_click_time = now
        self.last_click_button = button

    def release(self, x, y, button = 1):

        event = CGEventCreateMouseEvent(None, releaseID[button], (x, y), button - 1)
        CGEventSetIntegerValueField(event, kCGMouseEventClickState,
                                    self.last_click_count)

        CGEventPost(kCGHIDEventTap, event)
        self.buttondown[button] = False

    def move(self, x, y):

	# Double click is invalid if the mouse moves:
	self.last_click_time = 0

        if True in self.buttondown:
            button = self.buttondown.index(True)
            event_type = dragID[button]
        else:
            event_type = kCGEventMouseMoved

        move = CGEventCreateMouseEvent(None, event_type, (x, y), 0)
        CGEventPost(kCGHIDEventTap, move)

    def position(self):
        loc = NSEvent.mouseLocation()
        return loc.x, CGDisplayPixelsHigh(0) - loc.y

    def screen_size(self):
        return CGDisplayPixelsWide(0), CGDisplayPixelsHigh(0)

class PyMouseEvent(PyMouseEventMeta):
    def run(self):
        tap = CGEventTapCreate(
            kCGSessionEventTap,
            kCGHeadInsertEventTap,
            kCGEventTapOptionDefault,
            CGEventMaskBit(kCGEventMouseMoved) |
            CGEventMaskBit(kCGEventLeftMouseDown) |
            CGEventMaskBit(kCGEventLeftMouseUp) |
            CGEventMaskBit(kCGEventRightMouseDown) |
            CGEventMaskBit(kCGEventRightMouseUp) |
            CGEventMaskBit(kCGEventOtherMouseDown) |
            CGEventMaskBit(kCGEventOtherMouseUp),
            self.handler,
            None)

        loopsource = CFMachPortCreateRunLoopSource(None, tap, 0)
        loop = CFRunLoopGetCurrent()
        CFRunLoopAddSource(loop, loopsource, kCFRunLoopDefaultMode)
        CGEventTapEnable(tap, True)

        while self.state:
            CFRunLoopRunInMode(kCFRunLoopDefaultMode, 5, False)

    def handler(self, proxy, type, event, refcon):
        (x, y) = CGEventGetLocation(event)
        if type in pressID:
            self.click(x, y, pressID.index(type), True)
        elif type in releaseID:
            self.click(x, y, releaseID.index(type), False)
        else:
            self.move(x, y)
        
        if self.capture:
            CGEventSetType(event, kCGEventNull)

        return event
