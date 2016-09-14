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
import time
from functools import partial
import logging
import os.path
import argparse
import subprocess
#nonstandard
import serial
#local
from text_display import LCD
import mediaplayer_mpris2 as player
from weather_clock import WeatherClock

TIME_PERIOD = 5
TIME_INTERVAL = 30
UPDATE_INTERVAL = 0.06

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=
        'Displays Banshee status, time, date, and weather on the Arduino-controlled display.')
    parser.add_argument('city', help='City portion of Weather Underground URL')
    parser.add_argument('state', help='Two-letter state code part of Weather Underground URL')
    parser.add_argument('--port', default='/dev/ttyACM0', help='Serial port that Arduino is attached to')
    args = parser.parse_args()
        
    logging.basicConfig(filename=os.path.expanduser('~/display_daemon.py.log'), level=logging.DEBUG, format='[%(asctime)s] %(message)s')
    
    arduino = None
    lcd = None
    weather_clock = None
    media_player = None
    
    try:
        arduino = serial.Serial()
        arduino.port=args.port
        arduino.baudrate=9600
        arduino.timeout=1
        lcd = LCD(arduino)
        
        
        def info_changed(current_time, temperature, conditions):
            lcd.change_artist('{} {}&deg;F {}'.format(time.strftime('%I:%M%p %a %d', time.localtime(current_time)), temperature, conditions))
            
        weather_clock = WeatherClock('http://rss.wunderground.com/auto/rss_full/{}/{}.xml?units=english'.format(args.state, args.city))
        weather_clock.interval = TIME_INTERVAL
        weather_clock.handler = info_changed
        
        
        def player_changed(state, title, artist, album):
            if media_player.playing:
                lcd.change_title('{} - {}'.format(title,artist))
            else:
                lcd.change_title('')
                
        media_player = player.Status()
        media_player.attach_listener(player_changed)
        

        def recover():
            arduino.close()
            time.sleep(3)
    except:
        logging.exception('Error while starting up, cannot continue.')
        exit()

    logging.info('Started up.')
    
    
    while True:
        logging.getLogger().handlers[0].flush()
        try:
            if not arduino.isOpen():
                arduino.open()
                time.sleep(1)#Give Arduino some time to setup.
            media_player.poll()
            
            try:
                weather_clock.poll()
            except:
                logging.exception("Error getting weather/time data, possibly malformed rss. ({})".format(weather_clock._weather._url))
                
        except serial.SerialException:
            logging.error('Encountered serial error, will wait and retry.')
            recover()
        except subprocess.CalledProcessError as e:
            logging.error('"{}" encountered error: "{}"; will wait and retry.'.format(e.cmd, e.output))
            recover()
        except OSError as e:
            logging.error('Encountered an OS error, likely a serial error: "{}"; will wait and retry.'.format(e.strerror))
            recover()
        except:
            logging.exception('Unexpected error; will wait and retry.')
            recover()
        time.sleep(UPDATE_INTERVAL)
