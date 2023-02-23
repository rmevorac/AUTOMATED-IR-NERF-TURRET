"""!
@file motor_driver.py
    This file contains an MotorDriver class which is used to control a motor using the Pyboard and its pins.

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

# Yellow (channel A) leads for clockwise
# Blue (channel B) leads for clockwise

class MotorDriver:
    '''!
    @brief      This class is used to control a motor using the Pyboard and its pins.
    @details    The class initializes the pins for the enable, input 1, and input 2 pins of the motor.
                It also initializes a timer for PWM control of the motor. The class provides a function
                to set the duty cycle of the PWM signal applied to the motor to control its speed.
    '''

    def __init__ (self, en_pin, in1pin, in2pin, timer_num):
        '''!
        @brief      Constructor method for MotorDriver class
        @details    The constructor method initializes a MotorDriver object with the given enable pin (en_pin), 
                    input 1 pin (in1pin), input 2 pin (in2pin), and timer number (timer_num). It sets the specified 
                    pins as outputs, creates a timer using the given timer number, and initializes the pin_en, 
                    ch1, and ch2 attributes.
        @param      self The object itself
        @param      en_pin Pin number for the enable pin
        @param      in1pin Pin number for the input 1 pin
        @param      in2pin Pin number for the input 2 pin
        @param      timer_num Timer number
        @return     None
        '''
        ## Sets up the in1pin for the motor to be push-pull
        pin1 = Pin(in1pin, Pin.OUT_PP)
        ## Sets up the in2pin for the motor to be push-pull
        pin2 = Pin(in2pin, Pin.OUT_PP)
        ## Creates the timer which will run the motor
        timer = pyb.Timer(timer_num, freq=0x4E20)
        self.pin_en = Pin(en_pin, Pin.OUT_OD, Pin.PULL_UP)
        self.ch1 = timer.channel(1, pyb.Timer.PWM, pin=pin1)
        self.ch2 = timer.channel(2, pyb.Timer.PWM, pin=pin2)
        print("Creating a motor driver")

    def set_duty_cycle (self, level):
        '''!
        @brief      This method sets the duty cycle of the PWM signal that drives the motor.
        @details    The duty cycle is set based on the level parameter. If the level is negative, the duty cycle of
                    the PWM signal to channel 1 of the motor is set to -1 times the level, and the duty cycle of the
                    PWM signal to channel 2 of the motor is set to 0. If the level is positive, the duty cycle of the
                    PWM signal to channel 1 of the motor is set to 0, and the duty cycle of the PWM signal to channel
                    2 of the motor is set to the level. If the level is 0, the duty cycle of both channels is set to 0.
        @param      self The object itself
        @param      level The duty cycle of the PWM signal as a percentage (-100 to 100).
        @return     None
        '''
        self.pin_en.value(1)

        if level < 0:
            self.ch1.pulse_width_percent(-1 * level)
            self.ch2.pulse_width_percent(0)
        elif level > 0:
            self.ch1.pulse_width_percent(0)
            self.ch2.pulse_width_percent(level)
        else:
            self.ch1.pulse_width_percent(0)
            self.ch2.pulse_width_percent(0)
            
#         print (f"Setting duty cycle to {level}")