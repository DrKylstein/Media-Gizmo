#! /usr/bin/python

 # Copyright (c) 2012 Kyle Delaney
 # All rights reserved.
 #
 # Redistribution and use in source and binary forms, with or without
 # modification, are permitted provided that the following conditions
 # are met:
 #
 # Redistributions of source code must retain the above copyright notice,
 # this list of conditions and the following disclaimer.
 #
 # Redistributions in binary form must reproduce the above copyright
 # notice, this list of conditions and the following disclaimer in the
 # documentation and/or other materials provided with the distribution.
 #
 # Neither the name of the project's author nor the names of its
 # contributors may be used to endorse or promote products derived from
 # this software without specific prior written permission.
 #
 # THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
 # "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
 # LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
 # FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
 # HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
 # SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED
 # TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
 # PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
 # LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
 # NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
 # SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from __future__ import print_function
from __future__ import division
import serial
import subprocess
import time
import pygame.time
from unidecode import unidecode

import sys
#sys.stderr = sys.stdout = open('/home/kyle/ir-remote.log', mode='a+')

class Remote_Input(object):
    
    def __init__(self, tty):
        self._binds = {}
        self._serial = tty
        
    def bind(self, command, handler):
        self._binds[command] = handler
        
    def poll(self):
        command = self._serial.readline().strip()
        if command:
            if command in self._binds:
                self._binds[command]()
            #else:
                #print(command)
            print(command)
            
CMD_SET_TITLE = 0x80
CMD_SET_ARTIST = 0x81
CMD_SET_COLOR = 0x82
CMD_SET_MESSAGE = 0x83
CMD_SET_MESSAGE_COLOR = 0x84

class LCD(object):
    
    def __init__(self, serial):
        self._serial = serial
    
    def change_track(self, title, artist):
        self.change_title(title)
        self.change_artist(artist)
        
    def change_title(self, title):
        data = bytearray()
        data.append(CMD_SET_TITLE)
        data.append(len(title))
        data.extend(unidecode(title))
        self._serial.write(data);
        
    def change_artist(self, artist):
        data = bytearray()
        data.append(CMD_SET_ARTIST)
        data.append(len(artist))
        data.extend(unidecode(artist))
        self._serial.write(data);
        
    def display_message(self, text):
        data = bytearray()
        data.append(CMD_SET_MESSAGE)
        data.append(len(text))
        data.extend(text)
        self._serial.write(data)
        
    
class Media_Player(object):
    
    def __init__(self):
        self.playing = False
        self.artist = ''
        self.title = ''
        self._handler = None
        self._playback_handler = None
        
    def poll(self):
        if 'playing' in subprocess.check_output(['banshee', '--query-current-state', '--no-present']):
            if self.playing is not True and self._playback_handler is not None:
                self._playback_handler(True)
            self.playing = True
        elif 'pause' in subprocess.check_output(['banshee', '--query-current-state', '--no-present']):
            if self.playing is not False and self._playback_handler is not None:
                self._playback_handler(False)
            self.playing = False
        else:
            if self.playing is not None and self._playback_handler is not None:
                self._playback_handler(None)
            self.playing = None
            
        artist = subprocess.check_output(['banshee', '--query-artist', '--no-present'])[8:].rstrip()
        title = subprocess.check_output(['banshee', '--query-title', '--no-present'])[7:].rstrip()
        if (artist != self.artist or title != self.title) and self._handler is not None:
            self._handler(title, artist)
            self.title = title
            self.artist = artist
        
    def attach_track_change_listener(self, handler):
        self._handler = handler

    def attach_playback_listener(self, handler):
        self._playback_handler = handler

    def play(self):
        subprocess.call(['banshee', '--play', '--no-present'])
        
    def pause(self):
        subprocess.call(['banshee', '--pause', '--no-present'])
        
    def stop(self):
        subprocess.call(['banshee', '--stop', '--no-present'])
        
    def next_track(self):
        subprocess.call(['banshee', '--next', '--no-present'])
        
    def previous_track(self):
        subprocess.call(['banshee', '--previous', '--no-present'])
        
    def fullscreen(self):
        subprocess.call(['banshee', '--fullscreen'])
        
    def hide(self):
        subprocess.call(['banshee', '--hide'])
        
    def show(self):
        subprocess.call(['banshee', '--hide'])
        subprocess.call(['banshee', '--present'])


if __name__ == '__main__':
    while True:
        try:
            print(time.strftime('%Y-%m-%d %H:%M:%S'))

            serial_ = serial.Serial(port='/dev/serial/by-id/usb-Arduino__www.arduino.cc__Arduino_Uno_64932343938351F03281-if00', baudrate=9600, timeout=1)
            remote = Remote_Input(serial_)
            lcd = LCD(serial_)
            media_player = Media_Player()
            media_player.attach_track_change_listener(lcd.change_track)

            #media_player.attach_playback_listener(play_pause)

            def play():
                media_player.play()
                lcd.display_message('[Play]')
            def pause():
                media_player.pause()
                lcd.display_message('[Pause]')
            def next():
                media_player.next_track()
                lcd.display_message('[Next]')
            def previous():
                media_player.previous_track()
                lcd.display_message('[Previous]')
            def stop():
                media_player.stop()
            def display():
                media_player.fullscreen()
                lcd.display_message('[Fullscreen]')
            def options():
                media_player.hide()
                lcd.display_message('[Hide]')
            def menu():
                media_player.show()
                lcd.display_message('[Show]')
            def power():
                print(subprocess.check_output(['dbus-send', '--print-reply', '--system', '--dest=org.freedesktop.UPower', '/org/freedesktop/UPower','org.freedesktop.UPower.Suspend']))
            def yellow():
                lcd.display_message(time.strftime('%I:%M %p, %a'))
                
            remote.bind('play', play)
            remote.bind('pause', pause)
            remote.bind('next', next)
            remote.bind('previous', previous)
            remote.bind('stop', stop)
            remote.bind('display', display)
            remote.bind('options', options)
            remote.bind('menu', menu)
            remote.bind('power', power)
            remote.bind('yellow', yellow)

            clock = pygame.time.Clock()
            time.sleep(1) #Give Arduino some time to setup.
            while True:
                time_elapsed = clock.tick(15)
                media_player.poll()
                remote.poll()
        except serial.SerialException:
            time.sleep(5)
