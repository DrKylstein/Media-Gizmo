/*
 * Copyright (c) 2012 Kyle Delaney
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions
 * are met:
 *
 * Redistributions of source code must retain the above copyright notice,
 * this list of conditions and the following disclaimer.
 *
 * Redistributions in binary form must reproduce the above copyright
 * notice, this list of conditions and the following disclaimer in the
 * documentation and/or other materials provided with the distribution.
 *
 * Neither the name of the project's author nor the names of its
 * contributors may be used to endorse or promote products derived from
 * this software without specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
 * "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
 * LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
 * FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
 * HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
 * SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED
 * TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
 * PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
 * LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
 * NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
 * SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 *
 */

#include <SPI_VFD.h>
#include <IRremote.h>

#define MAX_STRING_LENGTH 80
#define COLUMNS 20

#define CMD_SET_TITLE 'T'
#define CMD_SET_ARTIST 'A'
#define CMD_SET_MESSAGE 'M'
#define CMD_CLEAR 'C'

#define SCROLL_TICK 200
#define MESSAGE_WAIT 2000
//Global Variables
//IR
decode_results results;
uint8_t repeat = 0;
//Command parsing
uint8_t command = 0;
uint8_t payloadSize = 0;
//Display text
uint8_t titleLength, artistLength, msgLength;
char title[MAX_STRING_LENGTH];
char artist[MAX_STRING_LENGTH];
char message[COLUMNS];
//Scrolling and messages
uint8_t scrollTop = 0;
uint8_t scrollBottom = 0;
unsigned long lastDisplayUpdate = 0;
int16_t scrollTimeout = 0;
int16_t msgTimeout = 0;
int8_t scrollDirTop = 1;
int8_t scrollDirBottom = 1;
uint8_t rowToScroll = 0;

boolean blank = false;

//Library Init
IRrecv irrecv(5);
SPI_VFD display(8, 10, 9);

//Main functions
void setup(void) {
    Serial.begin(9600);
    Serial.setTimeout(1000);
    display.begin(COLUMNS, 2);
    irrecv.enableIRIn();
    msgTimeout = 0;
}
void loop(void) {
    pollForRemote();
    pollSerial();
    updateDisplay();
}
void pollForRemote(void) {
    if(irrecv.decode(&results)) {
        if(repeat == 0) {
            if (results.decode_type == NEC) {
              Serial.print("NEC_");
            } 
            else if (results.decode_type == SONY) {
                Serial.print("SONY_");
                repeat = 3;
            } 
            else if (results.decode_type == RC5) {
              Serial.print("RC5_");
            } 
            else if (results.decode_type == RC6) {
              Serial.print("RC6_");
            }
            Serial.println(results.value, HEX);
        } else {
            --repeat;
        }
        irrecv.resume();
    }
}


void pollSerial() {
    while(Serial.available()) {
        //single character command
        if(command == 0) {
            command = Serial.read();
            //If it isn't a valid command, the buffer may be garbage
            if(!(command == CMD_SET_TITLE || command == CMD_SET_ARTIST || command == CMD_SET_MESSAGE || command == CMD_CLEAR)) {
                command = 0;
                Serial.flush();
            }
            //ready to recieve text
            switch(command) {
                case CMD_SET_TITLE:
                    titleLength = 0;
                    break;
                case CMD_SET_ARTIST:
                    artistLength = 0;
                    break;
                case CMD_SET_MESSAGE:
                    msgLength = 0;
                    break;
            }
        //new-line terminated text
        } else {
            char c = Serial.read();
            if(c == '\n') {
                switch(command) {
                    case CMD_SET_TITLE:
                        scrollTop = 0;
                        scrollDirTop = 1;
                        rewriteTop();
                        Serial.print("Recieved top row: ");
                        Serial.write((uint8_t*)title, titleLength);
                        Serial.println();
                        break;
                    case CMD_SET_ARTIST:
                        scrollBottom = 0;
                        scrollDirBottom = 1;
                        rewriteBottom();
                        Serial.print("Recieved bottom row: ");
                        Serial.write((uint8_t*)artist, artistLength);
                        Serial.println();
                        break;
                    case CMD_SET_MESSAGE:
                        msgTimeout = MESSAGE_WAIT;
                        scrollBottom = 0;
                        scrollDirBottom = 1;
                        rewriteBottom();
                        Serial.print("Recieved user message: ");
                        Serial.write((uint8_t*)message, msgLength);
                        Serial.println();
                        break;
                    case CMD_CLEAR:
                        titleLength = 0;
                        artistLength = 0;
                        msgTimeout = 0;
                        scrollTop = 0;
                        scrollDirTop = 1;
                        scrollBottom = 0;
                        scrollDirBottom = 1;
                        Serial.print("Screen cleared.");
                        break;
                }
                command = 0;
            } else {
                switch(command) {
                    case CMD_SET_TITLE:
                        if(titleLength < MAX_STRING_LENGTH) {
                            title[titleLength++] = c;
                        }
                        break;
                    case CMD_SET_ARTIST:
                        if(artistLength < MAX_STRING_LENGTH) {
                            artist[artistLength++] = c;
                        }
                        break;
                    case CMD_SET_MESSAGE:
                        if(msgLength < COLUMNS) {
                            message[msgLength++] = c;
                        }
                        break;
                }
            }
        }
    }
}

void rewriteTop(void) {
    display.setCursor(0,0);
    for(int i=0; i<COLUMNS; ++i) {
        if(scrollTop+i >= titleLength) {
            display.write(0x20);
        } else {
            display.write(title[scrollTop+i]);
        }
    }
}
void rewriteBottom(void) {
    display.setCursor(0,1);
    if(msgTimeout > 0) {
        for(int i=0; i<COLUMNS; ++i) {
            if(i >= msgLength) {
                display.write(0x20);
            } else {
                display.write(message[i]);
            }
        }
    } else {
        for(int i=0; i<COLUMNS; ++i) {
            if(scrollBottom+i >= artistLength) {
                display.write(0x20);
            } else {
                display.write(artist[scrollBottom+i]);
            }
        }
    }
}

void updateDisplay(void) {
    if(titleLength != 0 || artistLength != 0 || msgTimeout > 0) {
        if(blank) {
            display.display();
            blank = false;
        }
    } else {
        if(!blank) {
            display.noDisplay();
            blank = true;
        }
    }
    unsigned long time_elapsed = millis() - lastDisplayUpdate;
    lastDisplayUpdate = millis();
    if(msgTimeout > 0) {
        msgTimeout -= time_elapsed;
    }
    scrollTimeout -= time_elapsed;
    if(scrollTimeout <= 0) {
        scrollTimeout = SCROLL_TICK;
        if(rowToScroll == 0) {
            if(titleLength > COLUMNS) {
                scrollTop += scrollDirTop;
            }
            if(scrollTop >= titleLength - COLUMNS || scrollTop == 0) {
                scrollDirTop *= -1;
                if(scrollTop == 0) {
                    rowToScroll = 1;
                }
                scrollTimeout = SCROLL_TICK*8;
            }
        } else {
            if(artistLength > COLUMNS) {
                scrollBottom += scrollDirBottom;
            }
            if(scrollBottom >= artistLength - COLUMNS || scrollBottom == 0) {
                scrollDirBottom *= -1;
                if(scrollBottom == 0) {
                    rowToScroll = 0;
                }
                scrollTimeout = SCROLL_TICK*8;
           }
        }
        rewriteTop();
        rewriteBottom();
    }
}