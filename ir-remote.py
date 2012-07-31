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
from functools import partial
from unidecode import unidecode

import sys
#sys.stderr = sys.stdout = open('/home/kyle/ir-remote.log', mode='a+')

class ArduinoException(Exception):
    pass

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
            
class LCD(object):
    
    def __init__(self, serial):
        self._serial = serial
    
    def change_track(self, title, artist):
        self.change_title(title)
        self.change_artist(artist)
        
    #sometimes reports from the remote are read where command responses are expected, so checking is disabled.
    def change_title(self, title):
        self._serial.write('T{}\n'.format(unidecode(title)))
        #~ response = self._serial.readline().strip()
        #~ if response != 'Ok.':
            #~ raise ArduinoException, 'Unexpected or no response "{}"'.format(response)
        
    def change_artist(self, artist):
        self._serial.write('A{}\n'.format(unidecode(artist)))
        #~ response = self._serial.readline().strip()
        #~ if response != 'Ok.':
            #~ raise ArduinoException, 'Unexpected or no response "{}"'.format(response)
            
    def clear(self):
        self._serial.write('C\n')
        #~ response = self._serial.readline().strip()
        #~ if response != 'Ok.':
            #~ raise ArduinoException, 'Unexpected or no response "{}"'.format(response)

        
    def display_message(self, text):
        self._serial.write('M{}\n'.format(unidecode(text)))
        #~ response = self._serial.readline().strip()
        #~ if response != 'Ok.':
            #~ raise ArduinoException, 'Unexpected or no response "{}"'.format(response)

    
class Media_Player(object):
    
    def __init__(self):
        self.playing = False
        self.artist = ''
        self.title = ''
        self._listener = None
        
    def poll(self):
        changed = False
        artist = subprocess.check_output(['banshee', '--query-artist', '--no-present'])[8:].rstrip()
        title = subprocess.check_output(['banshee', '--query-title', '--no-present'])[7:].rstrip()
        if artist != self.artist or title != self.title:
            changed = True
            self.title = title
            self.artist = artist

        if 'playing' in subprocess.check_output(['banshee', '--query-current-state', '--no-present']):
            if self.playing is not True:
                changed = True
            self.playing = True
        elif 'pause' in subprocess.check_output(['banshee', '--query-current-state', '--no-present']):
            if self.playing is not False:
                changed = True
            self.playing = False
        else:
            if self.playing is not None:
                changed = True
            self.playing = None
            
        if changed  and self._listener is not None:
            self._listener(self.playing, self.title, self.artist)
            
        return self.playing, self.title, self.artist
        
    def attach_listener(self, listener):
        self._listener = listener

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

def simulate_key(key):
    subprocess.call(["xdotool", "key", key])
    
if __name__ == '__main__':
    while True:
        try:
            print(time.strftime('%Y-%m-%d %H:%M:%S'))

            serial_ = serial.Serial(port='/dev/serial/by-id/usb-Arduino__www.arduino.cc__Arduino_Uno_64932343938351F03281-if00', baudrate=9600, timeout=1)
            remote = Remote_Input(serial_)
            lcd = LCD(serial_)
            media_player = Media_Player()

            def player_changed(state, title, artist):
                if not state:
                    lcd.clear();
                else:
                    lcd.change_title(title)
                    lcd.change_artist(artist)

            media_player.attach_listener(player_changed)

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
                lcd.display_message('[Stop]')
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
            def show_time():
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
            remote.bind('yellow', show_time)
            remote.bind('red', partial(simulate_key, "space"))
            remote.bind('up', partial(simulate_key, "Up"))
            remote.bind('down', partial(simulate_key, "Down"))
            remote.bind('left', partial(simulate_key, "Tab"))
            remote.bind('right', partial(simulate_key, "shift+Tab"))
            remote.bind('enter', partial(simulate_key, "Return"))
            remote.bind('exit', partial(simulate_key, "Escape"))

            time.sleep(1) #Give Arduino some time to setup.
            while True:
                time.sleep(0.06)
                media_player.poll()
                remote.poll()
        except serial.SerialException:
            time.sleep(5)
