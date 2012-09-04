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

import time
import re
#nonstandard
import feedparser

class Weather(object):
    def __init__(self, url, minutes):
        self._url = url
        self._last_time = 0
        self._interval = minutes

    def refresh(self):
        '''Forcibly update the data.'''
        rss = feedparser.parse(self._url)
        self._data = {
            'current':dict(map(lambda a: a.split(': '), re.sub('<.+?>','', rss.entries[0].description).replace('&deg;F', '').replace('&deg;C', '').replace(' / ', '/').split(' | '))),
            'today':rss.entries[1].description,
            'tonight':rss.entries[1].description,
            'tomorrow':rss.entries[1].description         
        }
        self._last_time = time.time()

    def poll(self):
        '''Update the data only if it is old.'''
        if time.time() > self._last_time + (self._interval * 60):
            self.refresh()

    def forecast_today(self):
        return self._data['today']
        
    def forecast_tonight(self):
        return self._data['tonight']
        
    def forecast_tomorrow(self):
        return self._data['tomorrow']
        
    def current_conditions(self):
        return self._data['current']
