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

class Control(object):
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

class Status(object):
    
    def __init__(self):
        self.playing = False
        self.artist = u''
        self.title = u''
        self.album = u''
        self._listener = None
        
    def poll(self):
        changed = False
        artist = unicode(subprocess.check_output(['banshee', '--query-artist', '--no-present'])[8:].rstrip(), 'utf_8')
        title = unicode(subprocess.check_output(['banshee', '--query-title', '--no-present'])[7:].rstrip(), 'utf_8')
        album = unicode(subprocess.check_output(['banshee', '--query-album', '--no-present'])[7:].rstrip(), 'utf_8')
        if artist != self.artist or title != self.title or album != self.album:
            changed = True
            self.title = title
            self.artist = artist
            self.album = album

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
            self._listener(self.playing, self.title, self.artist, self.album)
            
        return self.playing, self.title, self.artist
        
    def attach_listener(self, listener):
        self._listener = listener
