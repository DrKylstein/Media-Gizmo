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

#include <avr/pgmspace.h>
#include <SPI_VFD.h>
#include <IRremote.h>

#define MAX_STRING_LENGTH 64
#define COLUMNS 20

#define CMD_SET_TITLE 0x80
#define CMD_SET_ARTIST 0x81
#define CMD_SET_MESSAGE 0x83

#define SCROLL_TICK 200
#define MESSAGE_WAIT 2000

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
char message[MAX_STRING_LENGTH];
//Scrolling and messages
uint8_t scrollTop = 0;
uint8_t scrollBottom = 0;
unsigned long lastDisplayUpdate = 0;
int16_t scrollTimeout = 0;
int16_t msgTimeout = 0;
uint8_t scrollState = 0;

void print_P(Print& device, const PROGMEM char* s)
{
  for (size_t i = 0; i < strlen_P(s); ++i)
  {
    device.print(char(pgm_read_byte_near(s + i)));
  }
}
void println_P(Print& device, const PROGMEM char* s)
{
  print_P(device, s);
  device.println();
}

IRrecv irrecv(5);
SPI_VFD display(8, 9, 10);

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
            if(results.decode_type == SONY) {
                switch(results.value) {
                    case 0x58B47:
                        println_P(Serial, PSTR("play"));
                        break;
                     case 0x6AB47:
                        println_P(Serial, PSTR("next"));
                         break;
                    case 0xEAB47:
                        println_P(Serial, PSTR("previous"));
                        break;
                     case 0x98B47:
                        println_P(Serial, PSTR("pause"));
                        break;
                     case 0x18B47:
                        println_P(Serial, PSTR("stop"));
                        break;
                     case 0x38B47:
                        println_P(Serial, PSTR("fast forward"));
                        break;
                     case 0xD8B47:
                        println_P(Serial, PSTR("rewind"));
                        break;
                     case 0x42B47:
                        println_P(Serial, PSTR("menu"));
                        break;
                     case 0xDCB47:
                        println_P(Serial, PSTR("left"));
                        break;
                     case 0x3CB47:
                        println_P(Serial, PSTR("right"));
                        break;
                     case 0x9CB47:
                        println_P(Serial, PSTR("up"));
                        break;
                     case 0x5CB47:
                        println_P(Serial, PSTR("down"));
                        break;
                     case 0xBCB47:
                        println_P(Serial, PSTR("enter"));
                        break;
                     case 0xC2B47:
                        println_P(Serial, PSTR("exit"));
                        break;
                     case 0xA8B47:
                        println_P(Serial, PSTR("power"));
                        break;
                     case 0x54B47:
                        println_P(Serial, PSTR("guide"));
                        break;
                     case 0x96B47:
                        println_P(Serial, PSTR("yellow"));
                        break;
                     case 0x66B47:
                        println_P(Serial, PSTR("blue"));
                        break;
                     case 0xE6B47:
                        println_P(Serial, PSTR("red"));
                        break;
                     case 0x16B47:
                        println_P(Serial, PSTR("green"));
                        break;
                     case 0xFCB47:
                        println_P(Serial, PSTR("options"));
                        break;
                     case 0x34B47:
                        println_P(Serial, PSTR("top menu"));
                        break;
                     case 0x94B47:
                        println_P(Serial, PSTR("pop up/menu"));
                        break;
                     case 0x26B47:
                        println_P(Serial, PSTR("audio"));
                        break;
                     case 0xC6B47:
                        println_P(Serial, PSTR("subtitle"));
                        break;
                     case 0xA6B47:
                        println_P(Serial, PSTR("angle"));
                        break;
                     case 0x82B47:
                        println_P(Serial, PSTR("display"));
                        break;
                    default:
                        Serial.print(results.value, HEX);
                }
                repeat = 3;
            } else {
                //report unrecognized code and continue
                if (results.decode_type == NEC) {
                  Serial.print("Decoded NEC: ");
                } 
                else if (results.decode_type == SONY) {
                  Serial.print("Decoded SONY: ");
                } 
                else if (results.decode_type == RC5) {
                  Serial.print("Decoded RC5: ");
                } 
                else if (results.decode_type == RC6) {
                  Serial.print("Decoded RC6: ");
                }
                Serial.print(results.value, HEX);
            }
        } else {
            --repeat;
        }
        irrecv.resume();
    }
}

void resetScroll(void) {
    scrollTop = scrollBottom = scrollState = 0;
    scrollTimeout = SCROLL_TICK;
    rewriteTop();
    rewriteBottom();
}

void pollSerial() {
    if(command == 0) {
        if(Serial.available() >= 2) {
            command = Serial.read();
            payloadSize = Serial.read();
            switch(command) {
                case CMD_SET_TITLE:
                    titleLength = payloadSize;
                    break;
                case CMD_SET_ARTIST:
                    artistLength = payloadSize;
                    break;
                case CMD_SET_MESSAGE:
                    msgLength = payloadSize;
                    break;
                default:
                    command = 0;
                    payloadSize = 0;
                    Serial.flush();
            }
        }
    }
    while(Serial.available()) {
        switch(command) {
            case CMD_SET_TITLE:
                title[titleLength - payloadSize] = Serial.read();
                break;
            case CMD_SET_ARTIST:
                artist[artistLength - payloadSize] = Serial.read();
                break;
            case CMD_SET_MESSAGE:
                message[msgLength - payloadSize] = Serial.read();
                break;
        }
        --payloadSize;
        if(payloadSize == 0) {
            resetScroll();
            command = 0;
            break;
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
    unsigned long time_elapsed = millis() - lastDisplayUpdate;
    lastDisplayUpdate = millis();
    if(msgTimeout > 0) {
        msgTimeout -= time_elapsed;
        if(msgTimeout <= 0) {
            rewriteBottom();
        }
    } else {
        scrollTimeout -= time_elapsed;
        if(scrollTimeout <= 0) {
            switch(scrollState) {
                case 0:
                    //println_P(Serial, PSTR("top forward."));
                    if(scrollTop >= titleLength - COLUMNS) {
                        //println_P(Serial, PSTR("to 1."));
                        ++scrollState;
                    } else {
                        ++scrollTop;
                        rewriteTop();
                    }
                    break;
                case 1:
                    //println_P(Serial, PSTR("top back."));
                    if(scrollTop == 0) {
                        //println_P(Serial, PSTR("to 2."));
                       ++scrollState;
                    } else {
                        --scrollTop;
                        rewriteTop();
                    }
                    break;
                case 2:
                    //println_P(Serial, PSTR("bottom forward."));
                    if(
                        (msgTimeout > 0 && scrollBottom >= msgLength - COLUMNS) ||
                        (msgTimeout <= 0 && scrollBottom >= artistLength - COLUMNS)
                    ) {
                        ++scrollState;
                         //println_P(Serial, PSTR("to 3."));
                   } else {
                        ++scrollBottom;
                        rewriteBottom();
                    }
                    break;
                case 3:
                    //println_P(Serial, PSTR("bottom back."));
                    if(scrollBottom == 0) {
                        //println_P(Serial, PSTR("to 0."));
                        scrollState = 0;
                    } else {
                        --scrollBottom;
                        rewriteBottom();
                    }
                    break;
            }
            scrollTimeout = SCROLL_TICK;
        }
    }
}