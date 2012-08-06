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
import mpd

class Media_Player(object):
    
    def __init__(self, host='localhost', port=6600):
        self.playing = False
        self.artist = ''
        self.title = ''
        self._listener = None
        self._client = mpd.MPDClient()
        self._client.connect(host, port)
        
    def poll(self):
        changed = False
        #ex: currentsong = {'id': '2', 'pos': '2', 'name': 'PopTron: Electro-Pop and Indie Dance Rock [SomaFM]', 'file': 'http://sfstream1.somafm.com:2200', 'title': 'CANT - Believe'}
        artist = ''
        title = ''
        if 'title' in self._client.currentsong():
            songinfo = self._client.currentsong()['title'].split(' - ')
            artist = songinfo[0]
            title = songinfo[1]
            
        if artist != self.artist or title != self.title:
            changed = True
            self.title = title
            self.artist = artist
        state = self._client.status()['state']
        if state == 'play':
            if self.playing is not True:
                changed = True
            self.playing = True
        elif state == 'pause':
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
        self._client.play()
        
    def pause(self):
        self._client.pause(1)
        
    def stop(self):
        self._client.stop()
        
    def next_track(self):
        self._client.next()
        
    def previous_track(self):
        self._client.previous()
        
    def fullscreen(self):
        return
        
    def hide(self):
        return
        
    def show(self):
        return
