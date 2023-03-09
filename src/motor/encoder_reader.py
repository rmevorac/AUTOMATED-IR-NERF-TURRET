"""!
@file encoder_reader.py
    This file contains an Encoder class which is used to read and provide the position of an encoder.

@author Ben Elkayam
@author Roey Mevorach
@author Ermias Yemane

@date   2023-Feb-10
"""
"""!
@package pyb                Contains all micro controller tools we use.
"""
import pyb
from pyb import Pin as Pin

class Encoder:
    '''!
    @brief      Reads and provides the position of an encoder.
    @details    The Encoder class reads the position of an encoder connected to the system and provides
                it to the user. The class is constructed by passing the channel A pin, channel B pin, and
                timer number of the encoder. The class provides methods to read the position of the encoder
                and reset it to 0. The readings of the encoder are processed to handle underflow and overflow
                situations.
    '''

    def __init__(self, Apin, Bpin, timer):
        '''!
        @brief      Create an Encoder object.
        @details    The constructor method initializes an Encoder object with the given channel A pin (Apin),
                    channel B pin (Bpin), and timer number (timer). It sets the specified pins as outputs,
                    creates two timer channels using the given timer, and initializes the position, prev_position,
                    and old_delta attributes.
        @param      self The object itself
        @param      Apin Pin number for channel A of the encoder
        @param      Bpin Pin number for channel B of the encoder
        @param      timer Timer number for reading encoder values
        @return     None
        '''
        self.enc_chA = Pin(Apin, Pin.OUT_PP)
        self.enc_chB = Pin(Bpin, Pin.OUT_PP)
        self.tim = pyb.Timer(timer, prescaler=0, period=0xFFFF)
        self.ch1 = self.tim.channel(1, pyb.Timer.ENC_AB, pin=self.enc_chA)
        self.ch2 = self.tim.channel(2, pyb.Timer.ENC_AB, pin=self.enc_chB)
        self.position = 0
        self.prev_position = 1000
        self.old_delta = 0
        print ("Creating Encoder")

    def read(self):
        '''!
        @brief      Reads and updates the encoder's position.
        @details    The read method retrieves the delta between the current and previous reading from the timer's counter,
                    checks for overflow or underflow in the readings, updates the old_delta and prev_position, and
                    calculates the encoder's current position. The method then prints the updated position.
        @param      self The object itself
        @return     None
        '''
        ## The current encoder position
        new_delta = self.tim.counter()
        ## Difference in previous and current position
        delta_1 = new_delta - self.old_delta
        if delta_1 <= -32768:
            delta_1 += 65536
            if new_delta > self.old_delta: #big drop
                delta_1 = new_delta - 65536 - self.old_delta
        #Checking for Underflow in the encoder readings and then sub-checking if the direction changed to forwards
        if delta_1 >= 32768:
            delta_1 -= 65536
            if new_delta < self.old_delta: #jump
                delta_1 = new_delta + 65536 - self.old_delta
                
        self.old_delta = new_delta
        self.prev_position = self.position
        self.position -= delta_1
        print(self.position)

    def zero(self):
        '''!
        @brief      Zero the encoder position.
        @details    The zero method sets the position attribute of the Encoder object to 0. This method can be used
                    to reset the encoder's position reading.
        @param      self The object itself
        @return     None
        '''
        self.position = 0