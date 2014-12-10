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
import logging
import os.path
from functools import partial
import time
import argparse
#nonstandard
import serial
#local
from remote import Remote_Input
import mediaplayer_mpris2 as player

REMOTE_CODES = {
   'play':'SONY_58B47',
   'next':'SONY_6AB47',
   'previous':'SONY_EAB47',
   'pause':'SONY_98B47',
   'stop':'SONY_18B47',
   'fast forward':'SONY_38B47',
   'rewind':'SONY_D8B47',
   'menu':'SONY_42B47',
   'left':'SONY_DCB47',
   'right':'SONY_3CB47',
   'up':'SONY_9CB47',
   'down':'SONY_5CB47',
   'enter':'SONY_BCB47',
   'exit':'SONY_C2B47',
   'power':'SONY_A8B47',
   'guide':'SONY_54B47',
   'yellow':'SONY_96B47',
   'blue':'SONY_66B47',
   'red':'SONY_E6B47',
   'green':'SONY_16B47',
   'options':'SONY_FCB47',
   'top menu':'SONY_34B47',
   'pop up/menu':'SONY_94B47',
   'audio':'SONY_26B47',
   'subtitle':'SONY_C6B47',
   'angle':'SONY_A6B47',
   'display':'SONY_82B47'
}

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=
        'Control Banshee and other applications with a remote via Arduino-powered reciever.')
    parser.add_argument('--port', default='/dev/ttyACM0', help='Serial port that Arduino is attached to')
    args = parser.parse_args()

    logging.basicConfig(filename=os.path.expanduser('~/control_daemon.py.log'), level=logging.DEBUG, format='[%(asctime)s] %(message)s')
    
    arduino = None
    remote = None
    media_player = None

    def recover():
        arduino.close()
        time.sleep(3)
        
    def power():
        logging.info(subprocess.check_output(['dbus-send', '--print-reply', '--system', '--dest=org.freedesktop.UPower', '/org/freedesktop/UPower','org.freedesktop.UPower.Suspend']))
    
    try:
        arduino = serial.Serial()
        arduino.port=args.port
        arduino.baudrate=9600
        remote = Remote_Input(arduino)
        media_player = player.Control()
                                        
        remote.bind(REMOTE_CODES['play'], media_player.play)
        remote.bind(REMOTE_CODES['pause'], media_player.pause)
        remote.bind(REMOTE_CODES['next'], media_player.next_track)
        remote.bind(REMOTE_CODES['previous'], media_player.previous_track)
        remote.bind(REMOTE_CODES['stop'], media_player.stop)
        remote.bind(REMOTE_CODES['display'], media_player.fullscreen)
        remote.bind(REMOTE_CODES['options'], media_player.hide)
        remote.bind(REMOTE_CODES['menu'], media_player.show)
        remote.bind(REMOTE_CODES['power'], power)
        
        remote.bind(REMOTE_CODES['up'], partial(subprocess.call, ['xdotool', 'key', 'Up']))
        remote.bind(REMOTE_CODES['down'], partial(subprocess.call, ['xdotool', 'key', 'Down']))
        remote.bind(REMOTE_CODES['left'], partial(subprocess.call, ['xdotool', 'key', 'Tab']))
        remote.bind(REMOTE_CODES['right'], partial(subprocess.call, ['xdotool', 'key', 'shift+Tab']))
        remote.bind(REMOTE_CODES['enter'], partial(subprocess.call, ['xdotool', 'key', 'Return']))
        remote.bind(REMOTE_CODES['exit'], partial(subprocess.call, ['xdotool', 'key', 'Escape']))
        remote.bind(REMOTE_CODES['red'], partial(subprocess.call, ['xdotool', 'key', 'space']))
        
    except:
        logging.exception('Error while starting up, cannot continue.')
        exit()
        
        
    logging.info('Started up.')
    
    
    while True:
        try:
            if not arduino.isOpen():
                arduino.open()
            time.sleep(1)#Give Arduino some time to setup.
            
            command = remote.poll()
            if command is not None:
                logging.debug('Arduino says: "{}".'.format(command))

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
