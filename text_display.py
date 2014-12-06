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
 
from unidecode import unidecode

class LCD(object):
    
    _table = [
        ('&deg;F',0x1B),
        ('&deg;C',0x1A),
        ('&deg;',0xDF),
        ('&sun;',0x94),
        ('&rain;',0xDE),
        ('&cloud;',0x8E),
        ('&storm;',0x8F),
        ('&amp;',0x26),
        ('~',0x8E)
        ]
    
    def __init__(self, tty):
        self._serial = tty
    
    def _translate_text(self, text):
        text = unidecode(text).encode('ascii', errors='ignore')
        for pair in self._table:
            text = text.replace(pair[0], chr(pair[1]))
        return text
    
    def change_track(self, title, artist):
        self.change_title(title)
        self.change_artist(artist)
        
    def change_title(self, title):
        self._serial.write('T{}\n'.format(self._translate_text(title)))
        
    def change_artist(self, artist):
        self._serial.write('A{}\n'.format(self._translate_text(artist)))
            
    def clear(self):
        self._serial.write('C\n')
 