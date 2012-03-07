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
//include <LiquidCrystal.h>
#include <SPI_VFD.h>
#include <IRremote.h>
#include <aJSON.h>

/* This function places the current value of the heap and stack pointers in the
 * variables. You can call it from any place in your code and save the data for
 * outputting or displaying later. This allows you to check at different parts of
 * your program flow.
 * The stack pointer starts at the top of RAM and grows downwards. The heap pointer
 * starts just above the static variables etc. and grows upwards. SP should always
 * be larger than HP or you'll be in big trouble! The smaller the gap, the more
 * careful you need to be. Julian Gall 6-Feb-2009.
 */
uint8_t * heapptr, * stackptr;
void check_mem() {
  stackptr = (uint8_t *)malloc(4);          // use stackptr temporarily
  heapptr = stackptr;                     // save value of heap pointer
  free(stackptr);      // free up the memory again (sets stackptr to 0)
  stackptr =  (uint8_t *)(SP);           // save value of stack pointer
}
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

#define PIN_LCD_R 9
#define PIN_LCD_G 10
#define PIN_LCD_B 11

#define PIN_LCD_VO 6
#define PIN_LCD_RS 12
#define PIN_LCD_E 13

#define PIN_LCD_D4 2
#define PIN_LCD_D5 4
#define PIN_LCD_D6 7
#define PIN_LCD_D7 8

#define MAX_STRING_LENGTH 64
#define LCD_WIDTH 20

#define CMD_SET_TITLE 0x80
#define CMD_SET_ARTIST 0x81
#define CMD_SET_COLOR 0x82
#define CMD_SET_MESSAGE 0x83
#define CMD_SET_MESSAGE_COLOR 0x84

#define SCROLL_TICK 200
#define MESSAGE_WAIT 2000

uint8_t repeat = 0;

uint8_t command = 0; //current LCD control command
uint8_t payloadSize = 0;
uint8_t titleLength, artistLength, msgLength;
char title[MAX_STRING_LENGTH];
char artist[MAX_STRING_LENGTH];
char message[MAX_STRING_LENGTH];
uint8_t main_color[3];
uint8_t message_color[3];
uint8_t scrollTop = 0;
uint8_t scrollBottom = 0;
unsigned long last_time = 0;
int16_t scroll_timeout = 0;
int16_t msgTimeout = 0;
uint8_t scrollState = 0;

IRrecv irrecv(5);
decode_results results;
// initialize the library with the numbers of the interface pins
SPI_VFD lcd(8, 9, 10);//LiquidCrystal lcd(PIN_LCD_RS, PIN_LCD_E, PIN_LCD_D4, PIN_LCD_D5, PIN_LCD_D6, PIN_LCD_D7);

void setup(void) {
    Serial.begin(9600);
    Serial.setTimeout(1000);
    // set up the LCD's number of columns and rows: 
    lcd.begin(LCD_WIDTH, 2);
    irrecv.enableIRIn();
    //~ analogWrite(PIN_LCD_R, 255);
    //~ analogWrite(PIN_LCD_G, 255);
    //~ analogWrite(PIN_LCD_B, 255);
    //~ analogWrite(PIN_LCD_VO, 64);
    msgTimeout = 0;
    check_mem();
    if(stackptr > heapptr) {
        Serial.println(stackptr - heapptr);
    } else {
        println_P(Serial, PSTR("Out of memory!"));
    }
}
void loop(void) {
    pollForRemote();
    pollSerial();
    updateLCD();
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
    scroll_timeout = SCROLL_TICK;
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
    lcd.setCursor(0,0);
    for(int i=0; i<LCD_WIDTH; ++i) {
        if(scrollTop+i >= titleLength) {
            lcd.write(0x20);
        } else {
            lcd.write(title[scrollTop+i]);
        }
    }
}
void rewriteBottom(void) {
    lcd.setCursor(0,1);
    if(msgTimeout > 0) {
        for(int i=0; i<LCD_WIDTH; ++i) {
            if(i >= msgLength) {
                lcd.write(0x20);
            } else {
                lcd.write(message[i]);
            }
        }
    } else {
        for(int i=0; i<LCD_WIDTH; ++i) {
            if(scrollBottom+i >= artistLength) {
                lcd.write(0x20);
            } else {
                lcd.write(artist[scrollBottom+i]);
            }
        }
    }
}

void updateLCD(void) {
    unsigned long time_elapsed = millis() - last_time;
    last_time = millis();
    if(msgTimeout > 0) {
        msgTimeout -= time_elapsed;
        if(msgTimeout <= 0) {
            rewriteBottom();
        }
    } else {
        scroll_timeout -= time_elapsed;
        if(scroll_timeout <= 0) {
            switch(scrollState) {
                case 0:
                    //println_P(Serial, PSTR("top forward."));
                    if(scrollTop >= titleLength - LCD_WIDTH) {
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
                        (msgTimeout > 0 && scrollBottom >= msgLength - LCD_WIDTH) ||
                        (msgTimeout <= 0 && scrollBottom >= artistLength - LCD_WIDTH)
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
            scroll_timeout = SCROLL_TICK;
        }
    }
}