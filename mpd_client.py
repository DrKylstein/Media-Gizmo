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
import time
#nonstandard
import serial
#local modules
from ir_recieve import LCD, Remote_Input
from mediaplayer_mpd import Media_Player
import weather

ARDUINO_PORT = '/dev/ttyACM0'
WEATHER_URL = "http://www.wunderground.com/auto/rss_full/NY/New_York.xml"

if __name__ == '__main__':
    arduino = serial.Serial()
    arduino.port=ARDUINO_PORT
    arduino.baudrate=9600
    arduino.timeout=1
        
    remote = Remote_Input(arduino)
    lcd = LCD(arduino)
    media_player = Media_Player()
    weather_ = weather.Weather(WEATHER_URL, 5)
    
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
    def show_time():
        lcd.display_message(''.format(time.strftime('%I:%M %p, %a')))
    def show_weather():
        lcd.display_message('{} {}'.format(weather_.current_conditions()["Temperature"], weather_.current_conditions()["Conditions"]))
        
    remote.bind('play', play)
    remote.bind('pause', pause)
    remote.bind('next', next)
    remote.bind('previous', previous)
    remote.bind('stop', stop)
    remote.bind('yellow', show_time)
    remote.bind('red', show_weather)
    while True:
        try:
            if not arduino.isOpen():
                arduino.open()
                time.sleep(1)#Give Arduino some time to setup.
            media_player.poll()
            command = remote.poll()
            if command is not None:
                print(command)
            weather_.poll()
            time.sleep(0.06)
        except serial.SerialException:
            print("[{}] Encountered serial error, will wait and retry.".format(time.strftime('%Y-%m-%d %H:%M:%S')))
            time.sleep(5)
        