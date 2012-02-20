/*
 * Copyright (c) 2011 Kyle Delaney
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
#include <LiquidCrystal.h>
#include "ircodes.h"

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
    device.print(pgm_read_byte_near(s + i));
  }
}

void println_P(Print& device, const PROGMEM char* s)
{
  print_P(device, s);
  device.println();
}

// We need to use the 'raw' pin reading methods
// because timing is very important here and the digitalRead()
// procedure is slower!
//uint8_t IRpin = 2;
// Digital pin #2 is the same as Pin D2 see
// http://arduino.cc/en/Hacking/PinMapping168 for the 'raw' pin mapping
#define IRpin_PIN PIND
#define IRpin 5

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


// the maximum pulse we'll listen for - 65 milliseconds is a long time
#define MAXPULSE 3000

//const uint8_t MAX_LENGTH PROGMEM = SONY_BLURAY_LENGTH;
#define MAX_LENGTH SONY_BLURAY_LENGTH

// what our timing resolution should be, larger is better
// as its more 'precise' - but too large and you wont get
// accurate timing
#define RESOLUTION 20

// What percent we will allow in variation to match the same code
#define FUZZINESS 20

// we will store up to 100 pulse pairs (this is -a lot-)
uint16_t pulses[MAX_LENGTH][2]; // pair is high and low pulse
uint8_t currentpulse = 0; // index for pulses we're storing

#define MAX_STRING_LENGTH 64
#define LCD_WIDTH 16

#define CMD_SET_TITLE 0x80
#define CMD_SET_ARTIST 0x81
#define CMD_SET_COLOR 0x82
#define CMD_SET_MESSAGE 0x83
#define CMD_SET_MESSAGE_COLOR 0x84

#define SCROLL_TICK 200
#define MESSAGE_WAIT 2000

uint8_t command = 0; //current LCD control command
uint8_t parameters_left = 0;
uint8_t title_length, artist_length, message_length;
char title[MAX_STRING_LENGTH];
char artist[MAX_STRING_LENGTH];
char message[MAX_STRING_LENGTH];
uint8_t main_color[3];
uint8_t message_color[3];
uint8_t scrollTop = 0;
uint8_t scrollBottom = 0;
unsigned long last_time = 0;
int16_t scroll_timeout = 0;
int16_t message_timeout = 0;
uint8_t scrollState = 0;

// initialize the library with the numbers of the interface pins
LiquidCrystal lcd(PIN_LCD_RS, PIN_LCD_E, PIN_LCD_D4, PIN_LCD_D5, PIN_LCD_D6, PIN_LCD_D7);

void setup(void) {
    Serial.begin(9600);
    //println_P(Serial, PSTR("IR COMMANDER"));
    // set up the LCD's number of columns and rows: 
    lcd.begin(LCD_WIDTH, 2);
    analogWrite(PIN_LCD_R, 255);
    analogWrite(PIN_LCD_G, 255);
    analogWrite(PIN_LCD_B, 255);
    analogWrite(PIN_LCD_VO, 64);
    message_timeout = 0;
    /*check_mem();
    if(stackptr > heapptr) {
        Serial.println(stackptr - heapptr);
    } else {
        println_P(Serial, PSTR("Out of memory!"));
    }*/
}
void loop(void) {
    pollForRemote();
    pollSerial();
    updateLCD();
}
void pollForRemote(void) {
  uint8_t numberpulses = listenForIR();
  if (IRcompare(numberpulses, SONY_BLURAY_LENGTH, SonyBlurayPlaySignal)) {
    println_P(Serial, PSTR("play"));
  } else if (IRcompare(numberpulses, SONY_BLURAY_LENGTH, SonyBlurayNextSignal)) {
    println_P(Serial, PSTR("next"));
  } else if (IRcompare(numberpulses, SONY_BLURAY_LENGTH, SonyBlurayPreviousSignal)) {
    println_P(Serial, PSTR("previous"));
  } else if(IRcompare(numberpulses, SONY_BLURAY_LENGTH, SonyBlurayPauseSignal)) {
    println_P(Serial, PSTR("pause"));
  } else if(IRcompare(numberpulses, SONY_BLURAY_LENGTH, SonyBlurayStopSignal)) {
    println_P(Serial, PSTR("stop"));
  } else if(IRcompare(numberpulses, SONY_BLURAY_LENGTH, SonyBlurayFastForwardSignal)) {
    println_P(Serial, PSTR("fast forward"));
  } else if(IRcompare(numberpulses, SONY_BLURAY_LENGTH, SonyBlurayRewindSignal)) {
    println_P(Serial, PSTR("rewind"));
  } else if(IRcompare(numberpulses, SONY_BLURAY_LENGTH, SonyBlurayMenuSignal)) {
    println_P(Serial, PSTR("menu"));
  } else if(IRcompare(numberpulses, SONY_BLURAY_LENGTH, SonyBlurayLeftSignal)) {
    println_P(Serial, PSTR("left"));
  } else if(IRcompare(numberpulses, SONY_BLURAY_LENGTH, SonyBlurayRightSignal)) {
    println_P(Serial, PSTR("right"));
  } else if(IRcompare(numberpulses, SONY_BLURAY_LENGTH, SonyBlurayUpSignal)) {
    println_P(Serial, PSTR("up"));
  } else if(IRcompare(numberpulses, SONY_BLURAY_LENGTH, SonyBlurayDownSignal)) {
    println_P(Serial, PSTR("down"));
  } else if(IRcompare(numberpulses, SONY_BLURAY_LENGTH, SonyBlurayEnterSignal)) {
    println_P(Serial, PSTR("enter"));
  } else if(IRcompare(numberpulses, SONY_BLURAY_LENGTH, SonyBlurayExitSignal)) {
    println_P(Serial, PSTR("exit"));
  } else if(IRcompare(numberpulses, SONY_BLURAY_LENGTH, SonyBlurayPowerSignal)) {
    println_P(Serial, PSTR("power"));
  } else if(IRcompare(numberpulses, SONY_BLURAY_LENGTH, SonyBlurayGuideSignal)) {
    println_P(Serial, PSTR("guide"));
  } else if(IRcompare(numberpulses, SONY_BLURAY_LENGTH, SonyBlurayYellowSignal)) {
    println_P(Serial, PSTR("yellow"));
  } else if(IRcompare(numberpulses, SONY_BLURAY_LENGTH, SonyBlurayBlueSignal)) {
    println_P(Serial, PSTR("blue"));
  } else if(IRcompare(numberpulses, SONY_BLURAY_LENGTH, SonyBlurayRedSignal)) {
    println_P(Serial, PSTR("red"));
  } else if(IRcompare(numberpulses, SONY_BLURAY_LENGTH, SonyBlurayGreenSignal)) {
    println_P(Serial, PSTR("green"));
  } else if(IRcompare(numberpulses, SONY_BLURAY_LENGTH, SonyBlurayOptionsSignal)) {
    println_P(Serial, PSTR("options"));
  } else if(IRcompare(numberpulses, SONY_BLURAY_LENGTH, SonyBlurayTopMenuSignal)) {
    println_P(Serial, PSTR("top menu"));
  } else if(IRcompare(numberpulses, SONY_BLURAY_LENGTH, SonyBlurayPopupMenuSignal)) {
    println_P(Serial, PSTR("dvd menu"));
  } else if(IRcompare(numberpulses, SONY_BLURAY_LENGTH, SonyBlurayAudioSignal)) {
    println_P(Serial, PSTR("audio"));
  } else if(IRcompare(numberpulses, SONY_BLURAY_LENGTH, SonyBluraySubtitleSignal)) {
    println_P(Serial, PSTR("subtitle"));
  } else if(IRcompare(numberpulses, SONY_BLURAY_LENGTH, SonyBlurayAngleSignal)) {
    println_P(Serial, PSTR("angle"));
  } else if(IRcompare(numberpulses, SONY_BLURAY_LENGTH, SonyBlurayDisplaySignal)) {
    println_P(Serial, PSTR("display"));
  }
}

static void commandComplete(void) {
    command = 0;
    //println_P(Serial, PSTR("Ok."));
}

void resetScroll(void) {
    scrollTop = scrollBottom = scrollState = 0;
    scroll_timeout = SCROLL_TICK;
    rewriteTop();
    rewriteBottom();
}

void pollSerial() {
    while(Serial.available()) {
        // command byte recieved
        if(Serial.peek() & 0x80) {
            command = Serial.read();
            if(command == CMD_SET_TITLE || command == CMD_SET_ARTIST || command == CMD_SET_MESSAGE) {
                //println_P(Serial, PSTR("Text command."));
                parameters_left = 0xFF;
            } else if(command == CMD_SET_COLOR || command == CMD_SET_MESSAGE_COLOR) {
                //println_P(Serial, PSTR("Color command."));
                parameters_left = 3;
            }
        } else {
        // parameter byte recieved
            if(command == CMD_SET_TITLE || command == CMD_SET_ARTIST || command == CMD_SET_MESSAGE) {
                if(parameters_left == 0xFF) {
                    uint8_t length = Serial.read();
                    if(length > MAX_STRING_LENGTH) {
                        length = MAX_STRING_LENGTH;
                        println_P(Serial, PSTR("Text truncated."));
                    }
                    parameters_left = length;
                    if(command == CMD_SET_TITLE) {
                        title_length = length;
                    } else if(command == CMD_SET_ARTIST) {
                        artist_length = length;
                    } else if(command == CMD_SET_MESSAGE) {
                        message_length = length;
                    }
                } else { 
                    if(command == CMD_SET_TITLE) {
                        title[title_length - parameters_left] = Serial.read();
                        if(parameters_left == 1) {
                            resetScroll();
                            //rewriteTop();
                        }
                    } else if(command == CMD_SET_ARTIST) {
                        artist[artist_length - parameters_left] = Serial.read();
                        if(parameters_left == 1 && message_timeout <= 0) {
                            resetScroll();
                            //rewriteBottom();
                        }
                    } else if(command == CMD_SET_MESSAGE) {
                        message[message_length - parameters_left] = Serial.read();
                        if(parameters_left == 1) {
                            message_timeout = MESSAGE_WAIT;
                            rewriteBottom();
                            //resetScroll();
                            updateColor();
                        }
                    }
                    --parameters_left;
                    if(parameters_left == 0) {
                        commandComplete();
                    }
                }
            } else if(command == CMD_SET_COLOR) {
                //println_P(Serial, PSTR("Color recieved."));
                main_color[3-parameters_left] = Serial.read() << 1;
                --parameters_left;
                if(parameters_left == 0) {
                    commandComplete();
                    updateColor();
                }
            } else if(command == CMD_SET_MESSAGE_COLOR) { //should preceed SET_MESSAGE command
                message_color[3-parameters_left] = Serial.read() << 1;
                --parameters_left;
                if(parameters_left == 0) {
                    commandComplete();
                    //updateColor();
                }
            } else {
                Serial.read(); //discard garbage data
            }
        }
    }
}

void rewriteTop(void) {
    lcd.setCursor(0,0);
    for(int i=0; i<LCD_WIDTH; ++i) {
        if(scrollTop+i >= title_length) {
            lcd.write(0x20);
        } else {
            lcd.write(title[scrollTop+i]);
        }
    }
}
void rewriteBottom(void) {
    lcd.setCursor(0,1);
    if(message_timeout > 0) {
        for(int i=0; i<LCD_WIDTH; ++i) {
            if(i >= message_length) {
                lcd.write(0x20);
            } else {
                lcd.write(message[i]);
            }
        }
    } else {
        for(int i=0; i<LCD_WIDTH; ++i) {
            if(scrollBottom+i >= artist_length) {
                lcd.write(0x20);
            } else {
                lcd.write(artist[scrollBottom+i]);
            }
        }
    }
}

void updateColor(void) {
    uint8_t r,g,b;
    if(message_timeout > 0) {
        r = message_color[0];
        g = message_color[1];
        b = message_color[2];
    } else {
        r = main_color[0];
        g = main_color[1];
        b = main_color[2];
    }
    r = 255 - (r >> 1);
    g = 255 - g;
    b = 255 - b;
    analogWrite(PIN_LCD_R, r);
    analogWrite(PIN_LCD_G, g);
    analogWrite(PIN_LCD_B, b);
}

void updateLCD(void) {
    unsigned long time_elapsed = millis() - last_time;
    last_time = millis();
    if(message_timeout > 0) {
        message_timeout -= time_elapsed;
        if(message_timeout <= 0) {
            rewriteBottom();
            updateColor();
        }
    } else {
        scroll_timeout -= time_elapsed;
        if(scroll_timeout <= 0) {
            switch(scrollState) {
                case 0:
                    //println_P(Serial, PSTR("top forward."));
                    if(scrollTop >= title_length - LCD_WIDTH) {
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
                        (message_timeout > 0 && scrollBottom >= message_length - LCD_WIDTH) ||
                        (message_timeout <= 0 && scrollBottom >= artist_length - LCD_WIDTH)
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

boolean IRcompare(uint8_t numpulses, uint8_t signalLength, const int16_t Signal[]) {
  if(numpulses < signalLength) return false;
  for (uint8_t i=0; i< numpulses-1 && i < signalLength-1; i++) {
    int16_t oncode = pulses[i][1] * RESOLUTION / 10;
    int16_t offcode = pulses[i+1][0] * RESOLUTION / 10;
    // check to make sure the error is less than FUZZINESS percent
    int16_t stored_code = pgm_read_word(&(Signal[i*2 + 0]));
    if ( abs(oncode - stored_code) <= (stored_code * FUZZINESS / 100)) {
        //println_P(Serial, PSTR("ok"));
    } else {
        // we didn't match perfectly, return a false match
        //println_P(Serial, PSTR("no"));
        return false;
    }
    stored_code = pgm_read_word(&(Signal[i*2 + 1]));
    if ( abs(offcode - stored_code) <= (stored_code * FUZZINESS / 100)) {
        //println_P(Serial, PSTR("ok"));
    } else {
        // we didn't match perfectly, return a false match
        //println_P(Serial, PSTR("ok"));
        return false;
    }
  }
  // Everything matched!
  return true;
}

uint8_t listenForIR(void) {
  currentpulse = 0;
  
  while (1) {
    uint16_t highpulse, lowpulse; // temporary storage timing
    highpulse = lowpulse = 0; // start out with no pulse length
  
// while (digitalRead(IRpin)) { // this is too slow!
    while (IRpin_PIN & (1 << IRpin)) {
       // pin is still HIGH

       // count off another few microseconds
       highpulse++;
       delayMicroseconds(RESOLUTION);

       // If the pulse is too long, we 'timed out' - either nothing
       // was received or the code is finished, so print what
       // we've grabbed so far, and then reset
       if ((highpulse >= MAXPULSE) /*&& (currentpulse != 0)*/) {
         return currentpulse;
       }
    }
    // we didn't time out so lets stash the reading
    if(currentpulse < MAX_LENGTH) {
	pulses[currentpulse][0] = highpulse;
    }
  
    // same as above
    while (! (IRpin_PIN & _BV(IRpin))) {
       // pin is still LOW
       lowpulse++;
       delayMicroseconds(RESOLUTION);
       if ((lowpulse >= MAXPULSE) && (currentpulse != 0)) {
         return currentpulse;
       }
    }
    if(currentpulse < MAX_LENGTH) {
	pulses[currentpulse][1] = lowpulse;
    }

    // we read one high-low pulse successfully, continue!
    currentpulse++;
  }
  return currentpulse;
}