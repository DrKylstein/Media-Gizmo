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
    
if __name__ == '__main__':
    logging.basicConfig(filename=os.path.expanduser('~/banshee_client.py.log'), level=logging.DEBUG, format='[%(asctime)s] %(message)s')
    #logging.basicConfig(level=logging.DEBUG, format='[%(asctime)s] %(message)s')
    try:
        arduino = serial.Serial()
        arduino.port=ARDUINO_PORT
        arduino.baudrate=9600
        arduino.timeout=1
        remote = Remote_Input(arduino)
        lcd = LCD(arduino)
        weather = Weather(WEATHER_URL, 10)
        media_player = Media_Player()
        
        mouse_mode = False
        temperature = 0
        conditions = ''
        current_time = ''

        def player_changed(state, title, artist, album):
            if not state:
                lcd.change_artist('--');
            else:
                if album == '':
                    lcd.change_artist(u'{} - {}'.format(title, artist))
                else:
                    lcd.change_artist(u'{} by {} on {}'.format(title, artist, album))

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
            lcd.display_message('[Ping!]')
        def switch_mode():
            global mouse_mode
            if mouse_mode:
                remote.bind('SONY_9CB47', partial(subprocess.call, ['xdotool', 'key', 'Up']))
                remote.bind('SONY_5CB47', partial(subprocess.call, ['xdotool', 'key', 'Down']))
                remote.bind('SONY_DCB47', partial(subprocess.call, ['xdotool', 'key', 'Tab'])) #left button
                remote.bind('SONY_3CB47', partial(subprocess.call, ['xdotool', 'key', 'shift+Tab'])) #right button
                remote.bind('SONY_BCB47', partial(subprocess.call, ['xdotool', 'key', 'Return']))
                remote.bind('SONY_C2B47', partial(subprocess.call, ['xdotool', 'key', 'Escape']))
                remote.bind('SONY_E6B47', partial(subprocess.call, ['xdotool', 'key', 'space'])) #red button
                lcd.display_message('[Keyboard Mode]')
            else:
                remote.bind('SONY_9CB47', partial(subprocess.call, ['xdotool', 'mousemove_relative', '--', '0', '-100']))
                remote.bind('SONY_5CB47', partial(subprocess.call, ['xdotool', 'mousemove_relative', '0', '100']))
                remote.bind('SONY_DCB47', partial(subprocess.call, ['xdotool', 'mousemove_relative', '--', '-100', '0'])) #left button
                remote.bind('SONY_3CB47', partial(subprocess.call, ['xdotool', 'mousemove_relative', '100', '0'])) #right button
                remote.bind('SONY_BCB47', partial(subprocess.call, ['xdotool', 'click', '1']))
                remote.bind('SONY_C2B47', partial(subprocess.call, ['xdotool', 'click', '2']))
                remote.bind('SONY_E6B47', partial(subprocess.call, ['xdotool', 'click', '3']))
                lcd.display_message('[Mouse Mode]')
            mouse_mode = not mouse_mode
        '''       
                        case 0x58B47:
                            println_P(Serial, PSTR('play'));
                            break;
                         case 0x6AB47:
                            println_P(Serial, PSTR('next'));
                             break;
                        case 0xEAB47:
                            println_P(Serial, PSTR('previous'));
                            break;
                         case 0x98B47:
                            println_P(Serial, PSTR('pause'));
                            break;
                         case 0x18B47:
                            println_P(Serial, PSTR('stop'));
                            break;
                         case 0x38B47:
                            println_P(Serial, PSTR('fast forward'));
                            break;
                         case 0xD8B47:
                            println_P(Serial, PSTR('rewind'));
                            break;
                         case 0x42B47:
                            println_P(Serial, PSTR('menu'));
                            break;
                         case 0xDCB47:
                            println_P(Serial, PSTR('left'));
                            break;
                         case 0x3CB47:
                            println_P(Serial, PSTR('right'));
                            break;
                         case 0x9CB47:
                            println_P(Serial, PSTR('up'));
                            break;
                         case 0x5CB47:
                            println_P(Serial, PSTR('down'));
                            break;
                         case 0xBCB47:
                            println_P(Serial, PSTR('enter'));
                            break;
                         case 0xC2B47:
                            println_P(Serial, PSTR('exit'));
                            break;
                         case 0xA8B47:
                            println_P(Serial, PSTR('power'));
                            break;
                         case 0x54B47:
                            println_P(Serial, PSTR('guide'));
                            break;
                         case 0x96B47:
                            println_P(Serial, PSTR('yellow'));
                            break;
                         case 0x66B47:
                            println_P(Serial, PSTR('blue'));
                            break;
                         case 0xE6B47:
                            println_P(Serial, PSTR('red'));
                            break;
                         case 0x16B47:
                            println_P(Serial, PSTR('green'));
                            break;
                         case 0xFCB47:
                            println_P(Serial, PSTR('options'));
                            break;
                         case 0x34B47:
                            println_P(Serial, PSTR('top menu'));
                            break;
                         case 0x94B47:
                            println_P(Serial, PSTR('pop up/menu'));
                            break;
                         case 0x26B47:
                            println_P(Serial, PSTR('audio'));
                            break;
                         case 0xC6B47:
                            println_P(Serial, PSTR('subtitle'));
                            break;
                         case 0xA6B47:
                            println_P(Serial, PSTR('angle'));
                            break;
                         case 0x82B47:
                            println_P(Serial, PSTR('display'));
                            break;
        '''
            
        remote.bind('SONY_58B47', play)
        remote.bind('SONY_98B47', pause)
        remote.bind('SONY_6AB47', next)
        remote.bind('SONY_EAB47', previous)
        remote.bind('SONY_18B47', stop)
        remote.bind('SONY_82B47', display)
        remote.bind('SONY_FCB47', options)
        remote.bind('SONY_42B47', menu)
        remote.bind('SONY_A8B47', power)
        remote.bind('SONY_96B47', show_time) #yellow button
        remote.bind('SONY_66B47', switch_mode) #yellow button
        
        remote.bind('SONY_9CB47', partial(subprocess.call, ['xdotool', 'key', 'Up']))
        remote.bind('SONY_5CB47', partial(subprocess.call, ['xdotool', 'key', 'Down']))
        remote.bind('SONY_DCB47', partial(subprocess.call, ['xdotool', 'key', 'Tab'])) #left button
        remote.bind('SONY_3CB47', partial(subprocess.call, ['xdotool', 'key', 'shift+Tab'])) #right button
        remote.bind('SONY_BCB47', partial(subprocess.call, ['xdotool', 'key', 'Return']))
        remote.bind('SONY_C2B47', partial(subprocess.call, ['xdotool', 'key', 'Escape']))
        remote.bind('SONY_E6B47', partial(subprocess.call, ['xdotool', 'key', 'space'])) #red button

        condition_icons = [
            ('clear','&sun;'), 
            ('sun','&sun;'), 
            ('overcast','&cloud;'), 
            ('cloud','&cloud;'), 
            ('rain','&rain;'), 
            ('shower','&rain;'), 
            ('storm','&storm;'), 
            ('thunder','&storm;'), 
            ]
        def condition_to_icon(text):
            for pair in condition_icons:
                if text.lower().count(pair[0]):
                    return pair[1]
            logging.warning('No icon for {}'.format(text))
            return '?'
            
        crashed = False
        def recover():
            crashed = True
            arduino.close()
            sleep(3)
        logging.info('Started up.')
    except:
        logging.exception('Error while starting up, cannot continue.')
        exit()
    while True:
        try:
            if not arduino.isOpen():
                arduino.open()
                time.sleep(1)#Give Arduino some time to setup.
            media_player.poll()
            weather.poll()
            data_changed = False
            temp_temperature = int(float(weather.current_conditions()['Temperature']))
            if temp_temperature != temperature:
                data_changed = True
                temperature = temp_temperature
            temp_condition = condition_to_icon(weather.current_conditions()['Conditions'])
            if temp_condition  != conditions:
                data_changed = True
                conditions = temp_condition
            temp_time = time.strftime('%a %d %I:%M%p')
            if temp_time  != current_time:
                data_changed = True
                current_time = temp_time
            if data_changed or crashed:
                lcd.change_title('{} {}&deg;F{}'.format(current_time, temperature, conditions))
                crashed = False
            command = remote.poll()
            if command is not None:
                logging.debug('Arduino says: "{}".'.format(command))
            time.sleep(0.06)
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
