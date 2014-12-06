#! /usr/bin/python

 # Copyright (c) 2014 Kyle Delaney
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
from sys import argv
#nonstandard
import serial
#local
from text_display import LCD
import mediaplayer_banshee as banshee
from weather import Weather

ARDUINO_PORT = argv[1] #'/dev/serial/by-id/usb-Arduino__www.arduino.cc__Arduino_Uno_64932343938351F03281-if00'
WEATHER_URL = 'http://rss.wunderground.com/auto/rss_full/{}/{}.xml?units=english'.format(argv[3], argv[2])
TIME_PERIOD = 5
TIME_INTERVAL = 30
UPDATE_INTERVAL = 0.06

class WeatherClock(object):
    
    any_handler = None
    interval = 60
    
    def __init__(self, url):
        self._weather = Weather(WEATHER_URL, 10)
        self.time = time.time()
        self._prev_time = time.time()
        self.temperature = 0
        self._prev_temperature = 0
        self.conditions = ''
        self._prev_conditions = ''

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
        
    def _player_changed(self, state, title, artist, album):
        if self._media_player.playing:
            self._lcd.change_title('{} - {}'.format(title,artist))
        else:
            self._lcd.change_title('Idle')
    
    def _info_changed(self, current_time, temperature, conditions):
        self._lcd.change_artist('{} {}&deg;F {}'.format(time.strftime('%I:%M%p %a %d', time.localtime(current_time)), temperature, conditions))

    def recover(self):
        self._arduino.close()
        time.sleep(3)

    def __init__(self, player_ns):
        self._arduino = serial.Serial()
        self._arduino.port=ARDUINO_PORT
        self._arduino.baudrate=9600
        self._arduino.timeout=1
        self._lcd = LCD(self._arduino)
        self._weather_clock = WeatherClock(WEATHER_URL)
        self._weather_clock.interval = TIME_INTERVAL
        self._media_player = player_ns.Status()
        self._media_player.attach_listener(self._player_changed)
        self._weather_clock.handler = self._info_changed
    
    def update(self):
        if not self._arduino.isOpen():
            self._arduino.open()
            time.sleep(1)#Give Arduino some time to setup.
        self._media_player.poll()
        try:
            self._weather_clock.poll()
        except:
            logging.exception("Error getting weather/time data, possibly malformed rss.")


if __name__ == '__main__':
    logging.basicConfig(filename=os.path.expanduser('~/banshee_display.py.log'), level=logging.DEBUG, format='[%(asctime)s] %(message)s')
    try:
        gizmo = MediaGizmo(banshee)
    except:
        logging.exception('Error while starting up, cannot continue.')
        exit()
    logging.info('Started up.')
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
        time.sleep(UPDATE_INTERVAL)
