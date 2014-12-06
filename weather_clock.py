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

from weather import Weather
import time

class WeatherClock(object):
    
    any_handler = None
    interval = 60
    
    def __init__(self, url):
        self._weather = Weather(url, 10)
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