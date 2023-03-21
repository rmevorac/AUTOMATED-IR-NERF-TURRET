"""!
@file main.py
    This code is for a control system that moves a NERF gun to a specific set of angles using
    two motors: a pitch and yaw motor. The system includes a IR camera (MLX90640), which produces
    an image to obtain the coordinates of the target. The system is activated/paused by pressing
    the user button on the microcontroller.

    This program implements a cooperative multitasking scheduler using the cotask and task_share modules.
    Tasks are defined as functions, and they yield control back to the scheduler using the yield statement.
    The scheduler then runs the next task until it yields or completes. Shared data between tasks is
    managed using shared variables provided by the task_share module. Overall, the code is running several
    tasks concurrently and using shared variables to communicate between them, allowing for cooperative multitasking.

    This program defines four tasks, two of which control the movement of the pitch and yaw motors. The program
    begins once the user button on the microcontroller is pressed. The system then begins its first task, which
    turns the gun around by 180 degrees. The system then waits for 5 seconds and moves to the next task. The next task
    uses the image produced by the IR camera to obtain the coordinates of the target (hottest pixel). These
    coordinates are then converted to ticks using simple geometry and other calculations, and are set as the motors'
    new setpoints. The motors then run until they reach the range of that setpoint. Once both motors are in position,
    the final task is triggered, which fires the NERF gun.


@author Ben Elkayam
@author Roey Mevorach
@author Ermias Yemane

@date   2023-Mar-20
"""
"""!
@package pyb                Contains all micro controller tools we use.
@package gc                 Contains a garbage collector tool.
@package utime              Contains functions for getting the current time and date, measuring
                            time intervals, and for delays.
@package machine            Contains specific functions related to the hardware on a particular board.
@package math               Contains mathematical functions.

@package cotask             Contains the class to run cooperatively scheduled tasks in amultitasking system.
@package task_share         Contains the class that allows tasks to share data without the risk
                            of data corruption by interrupts.
@package encoder_reader     Contains our encoder driver class and data.
@package motor_driver       Contains our motor driver class that interfaces with the encoder.
@package controller         Contains our controller class which combines the motor and encode classes.
@package mlx_cam            Contains a wrapper class for accessing and using the IR camera (MLX90640)
"""
import pyb
import gc
import utime as time
from machine import Pin, I2C
from math import atan, pi

import task.cotask as cotask
import task.task_share as task_share
from motor.encoder_reader import Encoder
from motor.motor_driver import MotorDriver
from motor.controller import Controller
from mlx90640.mlx_cam import MLX_Cam

NUM_PIXELS_COL = 32
NUM_PIXELS_ROW = 24

def button_press(pin):
    """!
    @brief      This is the callback function that is called when the interrupt
                is triggered when the user button is pressed
    @details    This function is called when the user button on the microcontroller
                is pressed. The global variable button_count starts at 0. It is then
                incremented to 1 when the button is pressed for the first time, allowing
                the program to run. When the button is pressed again, button_count is
                then decremented back to zero, which halts the program.
    @param      pin The pin on which to enable the interrupt
    @return     None
    """
    try:
        print("button pressed")
        global button_count

        if button_count:
            button_count -= 1
        else:
            button_count += 1

    except:
        pass

def move_pitch_motor(shares):
    """!
    @brief      This task moves the pitch motor until it reaches its setpoint.
    @details    This task has 2 states: IDLE (S0) and MOVING (S1). When this task is
                in S0, the pitch motor is idle. When this task is in S1, the pitch
                motor continuously runs and checks its position against its setpoint.
                When the position is within 10000 ticks of its setpoint, it checks
                if the yaw motor has reached its position. If my_queue has any items
                in it, then the yaw motor has reached its position and the system 
                transitions to the next task (firing a shot).
    @param      shares A tuple of two shares, one for `my_share` and one for `my_queue`.
    @return     None
    """
    # Get references to the share and queue which have been passed to this task
    my_share, my_queue = shares

    while 1:
        if my_share.get() == 3: # MOVE STATE (S1)
            while 1:
                controller1.run()
#                 print(f"p_p: {controller1.encoder.position}, sp_p: {controller1.setpoint}")

                if controller1.encoder.position in\
                 range(controller1.setpoint - 10000, controller1.setpoint + 10000):
                    print("reached pitch")
                    if my_queue.any():
                        my_share.put(4)
                        break
                yield
            yield
        else: # IDLE STATE (S0)
            yield

def move_yaw_motor(shares):
    """!
    @brief      This task moves the yaw motor until it reaches its setpoint.
    @details    This task has 3 states: IDLE (S0), MOVING (S1), and 180 TURN (S2).
                When this task is in S0, the yaw motor is idle. When this task is
                in S1, the yaw motor continuously runs and checks its position
                against its setpoint. When the position is within 100 ticks of its
                setpoint, it puts 1 in my_queue, which lets the pitch motor know that
                it has reached its position. When this task is in S2, a timer
                starts and then the yaw motor runs until it has completed a 180 deg
                turn. Once 5 seconds have past, the system transitions to the next task
                (getting the coordinates for the hotspot from the IR Cam input)
    @param      shares A tuple of two shares, one for `my_share` and one for `my_queue`.
    @return     None
    """
    # Get references to the share and queue which have been passed to this task
    my_share, my_queue = shares

    while 1:
        if my_share.get() == 3: # MOVE STATE (S1)
            while 1:
                controller2.run()
#                 print(f"p_y: {controller2.encoder.position}, sp_y: {controller2.setpoint}")

                if controller2.encoder.position in\
                 range(controller2.setpoint - 100, controller2.setpoint + 100):
                    print("reached yaw")
                    if not my_queue.any():
                        my_queue.put(1)
                    break
                yield
            yield
        elif my_share.get() == 1: # 180 TURN STATE (S2)
            ## Start timer
            timer = time.ticks_ms()
            while 1:
                controller2.run()
                # Completes 180 deg turn
                if controller2.encoder.position in range(29650, 30350):
#                     print(f"timer = {timer}, {time.ticks_ms()}")
                    if time.ticks_diff(time.ticks_ms(), timer) >= 5000:
                        print("done with delay")
                        controller2.encoder.zero()
                        motor2.set_duty_cycle(0)
                        my_share.put(2)
                        break
                yield
            yield
        else: # IDLE STATE (S0)
            yield

def get_coordinates(shares):
    """!
    @brief      Get the coordinates of the maximum value in the camera image.
    @details    This task has 2 states: IDLE (S0) and GET COORDINATES (S1).
                When this task is in S0, the task does nothing. When this task
                is in S1, this task retrieves the camera image, processes it, and calculates
                the coordinates of the pixel with the maximum value. It then converts
                these coordinates to distance and ticks, and sends them to the pitch and yaw
                motor controllers. Once those values are sent, the transitions to the
                next task (move motors).
    @param      shares A tuple of two shares, one for `my_share` and one for `my_queue`.
    @return     None
    """
    # Get references to the share and queue which have been passed to this task
    my_share, my_queue = shares

    while 1:
        if my_share.get() == 2: # GET COORDINATES STATE (S1)
            max_val, max_row, max_col = 0, 0, 0
            row, col = 1, 1

            image = camera.get_image()
#             camera.ascii_image(image.pix)
            pix = camera.get_csv(image.pix, limits=(0, 99))
            next(pix)
        #     print(f"MAX: {max_val}")

            while row < (NUM_PIXELS_ROW - 2):
        #         print(f"MAX: {max_val}") 
                line = next(pix).split(",")
        #         print(line)
                while col < (NUM_PIXELS_COL - 1):
                    if int(line[col]) > max_val:
                        avg = (int(line[col - 1]) + int(line[col]) + int(line[col + 1])) / 3
                        if avg > max_val:
#                             print(f"updated at {row}, {col} to value {avg}")
                            max_val = avg
                            max_row = row
                            max_col = col
                    col += 1
                row += 1
                col = 1
#             print(f"val: {max_val}, row: {max_row}, col: {max_col}")

            x_dist = (16 - max_col) * 2.8
            y_dist = (12 - max_row) * 3.7
#             print(f"x_dist: {x_dist}, y_dist: {y_dist}")
            
            x_ticks = int((atan(x_dist/180) * 60000) // (2 * pi)) + 320
            y_ticks = int((atan(y_dist/180) * 528000) // (2 * pi))
            
#             print(f"x: {x_ticks}, y: {y_ticks}")
            controller1.encoder.zero()
            controller2.encoder.zero()
            controller1.set_setpoint(y_ticks)
            controller2.set_setpoint(x_ticks)
            my_share.put(3)
            yield
        else: # IDLE STATE (S0)
            yield

def fire_round(shares):
    """!
    @brief      Get the coordinates of the maximum value in the camera image.
    @details    This task has 2 states: IDLE (S0) and GET COORDINATES (S1).
                When this task is in S0, the task does nothing. When this task
                is in S1, this task initiates the shooting procedure by setting
                the logic level of the trig_pin to high for 500 ms. This is the
                time it takes for the gun to fire one shot. This task then turns
                off the motors and transitions the system to the an idle state.
    @param      shares A tuple of two shares, one for `my_share` and one for `my_queue`.
    @return     None
    """
    # Get references to the share and queue which have been passed to this task
    my_share, my_queue = shares

    while 1:
        if my_share.get() == 4: # SHOOT STATE (S1)
            trig_pin.value(1)
            pyb.delay(500)
            trig_pin.value(0)
            print("bang")
            motor1.set_duty_cycle(0)
#             print("motor 1 shut off")
            motor2.set_duty_cycle(0)
#             print("motor 2 shut off")
            my_queue.clear()
            my_share.put(0)
            yield
        else: # IDLE STATE (S0)
            yield


if __name__ == "__main__":
    ## Set kp and setpoints for controllers 1 (pitch) where kp = 1 and setpoint = 0
    kp1, sp1 = 1, 0

    ## Set kp and setpoints for controllers 2 (yaw) where kp = 1 and setpoint = 32000 (180 deg turn)
    kp2, sp2 = 1.5, 30000
    
    ## Create pin for trigger fire
    trig_pin = Pin(Pin.board.PA4, Pin.OUT_PP)

    ## Create a share to test function and diagnostic printouts
    share0 = task_share.Share('h', thread_protect=False, name="Share 0")

    ## Create a queue to test function and diagnostic printouts
    q0 = task_share.Queue('h', 16, thread_protect=False, overwrite=False,
                          name="Queue 0")

    # The following import is only used to check if we have an STM32 board such
    # as a Pyboard or Nucleo; if not, use a different library
    try:
        from pyb import info

    # Oops, it's not an STM32; assume generic machine.I2C for ESP32 and others
    except ImportError:
        # For ESP32 38-pin cheapo board from NodeMCU, KeeYees, etc.
        i2c_bus = I2C(1, scl=Pin(22), sda=Pin(21))

    # OK, we do have an STM32, so just use the default pin assignments for I2C1
    else:
        i2c_bus = I2C(1)

    ## Select MLX90640 camera I2C address, normally 0x33, and check the bus
    i2c_address = 0x33
    scanhex = [f"0x{addr:X}" for addr in i2c_bus.scan()]
#     print(f"I2C Scan: {scanhex}")

    ## Create the camera object and set it up in default mode
    camera = MLX_Cam(i2c_bus)

    ## Create motor 1 object (pitch)
    motor1 = MotorDriver(Pin.board.PC1, Pin.board.PA0, Pin.board.PA1, 5)
    motor1.set_duty_cycle(0)

    ## Create motor 2 object (yaw)
    motor2 = MotorDriver(Pin.board.PA10, Pin.board.PB4, Pin.board.PB5, 3)
    motor2.set_duty_cycle(0)

    ## Create encoder 1 object (pitch)
    encoder1 = Encoder(Pin.board.PC6, Pin.board.PC7, 8)
    
    ## Create encoder 2 object (yaw)
    encoder2 = Encoder(Pin.board.PB6, Pin.board.PB7, 4)

    ## Once motor, encoder and params are collected they are used to create this controller 1 object (pitch)
    controller1 = Controller(kp1, sp1, motor1, encoder1)

    ## Once motor, encoder and params are collected they are used to create this controller 2 object (yaw)
    controller2 = Controller(kp2, sp2, motor2, encoder2)

    ## Initialize button_count to turn microcontroller on/off
    global button_count

    ## Set button_count to 0 (off)
    button_count = 0

    ## Set up the interrupt pin for when a button is pressed. Pressing the button starts/stops the system
    button_pin = pyb.ExtInt(Pin.board.PC13, pyb.ExtInt.IRQ_FALLING, Pin.PULL_UP, button_press)


    # Create the tasks. If trace is enabled for any task, memory will be
    # allocated for state transition tracing, and the application will run out
    # of memory after a while and quit. Therefore, use tracing only for 
    # debugging and set trace to False when it's not needed
    task1 = cotask.Task(move_pitch_motor, name="Task_1", priority=3, period=50,
                        profile=True, trace=False, shares=(share0, q0))
    task2 = cotask.Task(move_yaw_motor, name="Task_2", priority=4, period=50,
                        profile=True, trace=False, shares=(share0, q0))
    task3 = cotask.Task(get_coordinates, name="Task_3", priority=2, period=50,
                        profile=True, trace=False, shares=(share0, q0))
    task4 = cotask.Task(fire_round, name="Task_4", priority=1, period=50,
                        profile=True, trace=False, shares=(share0, q0))
    cotask.task_list.append(task1)
    cotask.task_list.append(task2)
    cotask.task_list.append(task3)
    cotask.task_list.append(task4)
    
    # Put state number into shares. Initialized to state 1
    share0.put(1)

    # Run the memory garbage collector to ensure memory is as defragmented as
    # possible before the real-time scheduler is started
    gc.collect()

    # Run the scheduler with the chosen scheduling algorithm. Quit if ^C pressed
    while True:
        if button_count:
            try:
                cotask.task_list.pri_sched()
            except KeyboardInterrupt:
                motor1.set_duty_cycle(0)
#                 print("motor 1 shut off")
                motor2.set_duty_cycle(0)
#                 print("motor 2 shut off")
                break

    # Print a table of task data and a table of shared information data
    print('\n' + str (cotask.task_list))
    print(task_share.show_all())
    print(task1.get_trace())
    print('')
