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
 # 'AS IS' AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
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
import subprocess
import time
from functools import partial
import logging
import os.path
#nonstandard
import serial
#local
from ir_recieve import LCD, Remote_Input
from mediaplayer_banshee import Media_Player
from weather import Weather

ARDUINO_PORT = '/dev/serial/by-id/usb-Arduino__www.arduino.cc__Arduino_Uno_64932343938351F03281-if00'
WEATHER_URL = 'http://rss.wunderground.com/auto/rss_full/FL/Bradenton.xml?units=english'
TIME_PERIOD = 5
TIME_INTERVAL = 30
SONY_BD = {
   'play':0x58B47,
   'next':0x6AB47,
   'previous':0xEAB47,
   'pause':0x98B47,
   'stop':0x18B47,
   'fast forward':0x38B47,
   'rewind':0xD8B47,
   'menu':0x42B47,
   'left':0xDCB47,
   'right':0x3CB47,
   'up':0x9CB47,
   'down':0x5CB47,
   'enter':0xBCB47,
   'exit':0xC2B47,
   'power':0xA8B47,
   'guide':0x54B47,
   'yellow':0x96B47,
   'blue':0x66B47,
   'red':0xE6B47,
   'green':0x16B47,
   'options':0xFCB47,
   'top menu':0x34B47,
   'pop up/menu':0x94B47,
   'audio':0x26B47,
   'subtitle':0xC6B47,
   'angle':0xA6B47,
   'display':0x82B47
    }
    #~ CONDITION_ICONS = [
        #~ ('clear','&sun;'), 
        #~ ('sun','&sun;'), 
        #~ ('overcast','&cloud;'), 
        #~ ('cloud','&cloud;'), 
        #~ ('rain','&rain;'), 
        #~ ('shower','&rain;'), 
        #~ ('storm','&storm;'), 
        #~ ('thunder','&storm;'), 
        #~ ]
#~ def condition_to_icon(text):
    #~ for pair in condition_icons:
        #~ if text.lower().count(pair[0]):
            #~ return pair[1]
    #~ logging.warning('No icon for {}'.format(text))
    #~ return '?'

class WeatherClock(object):
    
    any_handler = None
    interval = 60
    
    def __init__(self, url):
        self._weather = Weather(WEATHER_URL, 10)
        self._weather.refresh()
        self.time = time.time()
        self._prev_time = time.time()
        self.temperature = int(float(self._weather.current_conditions()['Temperature']))
        self._prev_temperature = int(float(self._weather.current_conditions()['Temperature']))
        self.conditions = self._weather.current_conditions()['Conditions']
        self._prev_conditions = self._weather.current_conditions()['Conditions']

    def poll(self):
        self._weather.poll()
        self.time = time.time()
        self.temperature = int(float(self._weather.current_conditions()['Temperature']))
        self.conditions = self._weather.current_conditions()['Conditions']
        if self.time - self._prev_time > self.interval or self.temperature != self._prev_temperature or self.conditions != self._prev_conditions:
            if self.handler is not None:
                self.handler(self.time, self.temperature, self.conditions)
            self._prev_time = self.time
            self._prev_conditions = self.conditions
            self._prev_temperature = self.temperature
    
class MediaGizmo(object):
    
    def _update_display(self):
        if self._media_player.playing and self._last_info_time > 0:
            self._lcd.change_title(self._media_player.title)

            self._lcd.change_artist(self._media_player.artist)

            #~ if self._media_player.album:
                #~ self._lcd.change_artist(u'{} [{}]'.format(self._media_player.artist, self._media_player.album))
            #~ else:
                #~ self._lcd.change_artist(self._media_player.artist)
        else:
            self._lcd.change_title(time.strftime('%a %d %I:%M%p', time.localtime(self._weather_clock.time)))
            self._lcd.change_artist('{}&deg;F {}'.format(self._weather_clock.temperature, self._weather_clock.conditions))
            self._last_info_time = time.time()
    
    def _player_changed(self, state, title, artist, album):
        self._update_display()
        #~ if state:
            #~ self._lcd.change_title(title)
            #~ if album:
                #~ self._lcd.change_artist(u'{} [{}]'.format(artist, album))
            #~ else:
                #~ self._lcd.change_artist(artist)
        #~ else:
            #~ self._info_changed(self._weather_clock.time, self._weather_clock.temperature, self._weather_clock.conditions)
    
    def _info_changed(self, current_time, temperature, conditions):
        self._update_display()
        #~ self._lcd.change_title(time.strftime('%a %d %I:%M%p', time.localtime(current_time)))
        #~ self._lcd.change_artist('{}&deg;F {}'.format(temperature, conditions))
        #~ self._last_info_time = time.time()

    def _power(self):
        logging.info(subprocess.check_output(['dbus-send', '--print-reply', '--system', '--dest=org.freedesktop.UPower', '/org/freedesktop/UPower','org.freedesktop.UPower.Suspend']))

    def recover(self):
        self._arduino.close()
        time.sleep(3)

    def __init__(self):
        self._arduino = serial.Serial()
        self._arduino.port=ARDUINO_PORT
        self._arduino.baudrate=9600
        self._arduino.timeout=1
        self._remote = Remote_Input(self._arduino)
        self._lcd = LCD(self._arduino)
        self._weather_clock = WeatherClock(WEATHER_URL)
        self._weather_clock.interval = TIME_INTERVAL
        self._media_player = Media_Player()
        self._last_info_time = 0

        self._media_player.attach_listener(self._player_changed)
        self._weather_clock.handler = self._info_changed
                                        
        self._remote.bind(SONY_BD['play'], self._media_player.play)
        self._remote.bind(SONY_BD['pause'], self._media_player.pause)
        self._remote.bind(SONY_BD['next'], self._media_player.next_track)
        self._remote.bind(SONY_BD['previous'], self._media_player.previous_track)
        self._remote.bind(SONY_BD['stop'], self._media_player.stop)
        self._remote.bind(SONY_BD['display'], self._media_player.fullscreen)
        self._remote.bind(SONY_BD['options'], self._media_player.hide)
        self._remote.bind(SONY_BD['menu'], self._media_player.show)
        self._remote.bind(SONY_BD['power'], self._power)
        self._remote.bind(SONY_BD['blue'], partial(self._lcd.display_message, '[Ping!]'))
        
        self._remote.bind(SONY_BD['up'], partial(subprocess.call, ['xdotool', 'key', 'Up']))
        self._remote.bind(SONY_BD['down'], partial(subprocess.call, ['xdotool', 'key', 'Down']))
        self._remote.bind(SONY_BD['left'], partial(subprocess.call, ['xdotool', 'key', 'Tab']))
        self._remote.bind(SONY_BD['right'], partial(subprocess.call, ['xdotool', 'key', 'shift+Tab']))
        self._remote.bind(SONY_BD['enter'], partial(subprocess.call, ['xdotool', 'key', 'Return']))
        self._remote.bind(SONY_BD['exit'], partial(subprocess.call, ['xdotool', 'key', 'Escape']))
        self._remote.bind(SONY_BD['red'], partial(subprocess.call, ['xdotool', 'key', 'space']))
        
        logging.info('Started up.')
    
    def update(self):
        if not self._arduino.isOpen():
            self._arduino.open()
            time.sleep(1)#Give Arduino some time to setup.
        self._media_player.poll()
        self._weather_clock.poll()
        if self._media_player.playing and self._last_info_time > 0 and time.time() - self._last_info_time > TIME_PERIOD:
            self._update_display()
            self._last_info_time = 0
        command = self._remote.poll()
        if command is not None:
            logging.debug('Arduino says: "{}".'.format(command))
        time.sleep(0.06)


if __name__ == '__main__':
    #logging.basicConfig(filename=os.path.expanduser('~/banshee_client.py.log'), level=logging.DEBUG, format='[%(asctime)s] %(message)s')
    logging.basicConfig(level=logging.DEBUG, format='[%(asctime)s] %(message)s')
    try:
        gizmo = MediaGizmo()
    except:
        logging.exception('Error while starting up, cannot continue.')
        exit()
    while True:
        try:
            gizmo.update()
        except serial.SerialException:
            logging.error('Encountered serial error, will wait and retry.')
            gizmo.recover()
        except subprocess.CalledProcessError as e:
            logging.error('"{}" encountered error: "{}"; will wait and retry.'.format(e.cmd, e.output))
            gizmo.recover()
        except OSError as e:
            logging.error('Encountered an OS error, likely a serial error: "{}"; will wait and retry.'.format(e.strerror))
            gizmo.recover()
        except:
            logging.exception('Unexpected error; will wait and retry.')
            gizmo.recover()
