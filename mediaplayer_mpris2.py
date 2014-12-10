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
import subprocess
import dbus
import re

org_mpris_re = re.compile('^org\.mpris\.MediaPlayer2\.([^.]+)$')

def getPlayer():
        bus =  dbus.SessionBus()
        players = [ name for name in bus.list_names() if org_mpris_re.match(name) ]

        if players:
            player_name = org_mpris_re.match(players[0]).group(1)
            root_obj = bus.get_object('org.mpris.MediaPlayer2.%s' % player_name, '/org/mpris/MediaPlayer2')
            root      = dbus.Interface(root_obj,      dbus_interface='org.mpris.MediaPlayer2')
            player    = dbus.Interface(root_obj,    dbus_interface='org.mpris.MediaPlayer2.Player')
            return player
        return None
        
def getRoot():
        bus =  dbus.SessionBus()
        players = [ name for name in bus.list_names() if org_mpris_re.match(name) ]

        if players:
            player_name = org_mpris_re.match(players[0]).group(1)
            root_obj = bus.get_object('org.mpris.MediaPlayer2.%s' % player_name, '/org/mpris/MediaPlayer2')
            root      = dbus.Interface(root_obj,      dbus_interface='org.mpris.MediaPlayer2')
            return root
        return None

def getProps():
    if players:
        player_name = org_mpris_re.match(players[0]).group(1)
        root_obj = bus.get_object('org.mpris.MediaPlayer2.%s' % player_name, '/org/mpris/MediaPlayer2')
        root      = dbus.Interface(root_obj,      dbus_interface='org.mpris.MediaPlayer2')
        player    = dbus.Interface(root_obj,    dbus_interface='org.mpris.MediaPlayer2.Player')
        player_props = dbus.Interface(root_obj, 'org.freedesktop.DBus.Properties')
        return player_props
    return None



class Control(object):
    def play(self):
        player = getPlayer()
        if player is not None:
            player.get_dbus_method('Play')()
        
    def pause(self):
        player = getPlayer()
        if player is not None:
            try:
                player.get_dbus_method('Pause')()
            except:
                self.play_pause()
            
    def play_pause(self):
        player = getPlayer()
        if player is not None:
            player.get_dbus_method('PlayPause')()
        
    def stop(self):
        player = getPlayer()
        if player is not None:
            player.get_dbus_method('Stop')()
        
    def next_track(self):
        player = getPlayer()
        if player is not None:
            player.get_dbus_method('Next')()
        
    def previous_track(self):
        player = getPlayer()
        if player is not None:
            player.get_dbus_method('Previous')()
        
    def fullscreen(self):
        props = getProps()
        if props is not None:
            props.set('org.mpris.MediaPlayer2', 'Fullscreen', not props.get('org.mpris.MediaPlayer2', 'Fullscreen'))
        
    def hide(self):
        root = getPlayer()
        if root is not None:
            root.get_dbus_method('Quit')()
        
    def show(self):
        root = getPlayer()
        if root is not None:
            root.get_dbus_method('Raise')()

class Status(object):
    
    def __init__(self):
        self.playing = False
        self.artist = u''
        self.title = u''
        self.album = u''
        self._listener = None
        
    def poll(self):
        changed = False
        artist = ''
        album = ''
        title = ''
        status = None


        bus =  dbus.SessionBus()
        players = [ name for name in bus.list_names() if org_mpris_re.match(name) ]

        if players:
            player_name = org_mpris_re.match(players[0]).group(1)
            root_obj = bus.get_object('org.mpris.MediaPlayer2.%s' % player_name, '/org/mpris/MediaPlayer2')
            root      = dbus.Interface(root_obj,      dbus_interface='org.mpris.MediaPlayer2')
            player    = dbus.Interface(root_obj,    dbus_interface='org.mpris.MediaPlayer2.Player')
            player_props = dbus.Interface(root_obj, 'org.freedesktop.DBus.Properties')
            metadata =  player_props.Get('org.mpris.MediaPlayer2.Player', 'Metadata')
            if 'xesam:artist' in metadata:
                artist = metadata['xesam:artist'][0]
            if 'xesam:title' in metadata:
                title = metadata['xesam:title']
            if 'xesam:album' in metadata:
                album = metadata['xesam:album']
            status = player_props.Get('org.mpris.MediaPlayer2.Player', 'PlaybackStatus')
            
        
        if artist != self.artist or title != self.title or album != self.album:
            changed = True
            self.title = title
            self.artist = artist
            self.album = album

        if 'Playing' == status:
            if self.playing is not True:
                changed = True
            self.playing = True
        elif 'Paused' == status:
            if self.playing is not False:
                changed = True
            self.playing = False
        else:
            if self.playing is not None:
                changed = True
            self.playing = None
            
        if changed  and self._listener is not None:
            self._listener(self.playing, self.title, self.artist, self.album)
            
        return self.playing, self.title, self.artist, self.album
        
    def attach_listener(self, listener):
        self._listener = listener

if __name__ == '__main__':
    status = Status()
    print status.poll()