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

def move_pitch_motor(shares):
    """!
    @brief      This function executes task1 by continuously checking if the controller1 has new data and,
                if so, writing it to the u2 share.
    @details    The function takes in a tuple of two shares, one for the `my_share` and one for the `my_queue`.
                It then enters a while loop that runs indefinitely, checking if the `controller1.run()` method
                returns `True` and, if so, writing the first and second elements of `controller1.motor_data`
                to the `u2` share. If a KeyboardInterrupt is raised, the motor is shut off and the loop is broken.
                The function yields control after each iteration of the loop.
    @param      shares A tuple of two shares, one for `my_share` and one for `my_queue`.
    @return     None
    """
    # Get references to the share and queue which have been passed to this task
    my_share, my_queue = shares

    while 1:
        if my_share.get() == 3: # MOVE STATE (S1)
            while 1:
                controller1.run()

                if controller1.encoder.position in\
                 range(controller1.setpoint - 250, controller1.setpoint + 250):
                    motor1_flag = 1
                    if motor2_flag:
                        my_share.put(4)
                yield
            yield
        else: # IDLE STATE (S0)
            yield

def move_yaw_motor(shares):
    """!
    @brief      This function executes task2 by continuously checking if the controller2 has new data and,
                if so, writing it to the u2 share.
    @details    The function takes in a tuple of two shares, one for the `my_share` and one for the `my_queue`.
                It then enters a while loop that runs indefinitely, checking if the `controller2.run()` method
                returns `True` and, if so, writing the first and second elements of `controller2.motor_data`
                to the `u2` share. If a KeyboardInterrupt is raised, the motor is shut off and the loop is broken.
                The function yields control after each iteration of the loop.
    @param      shares A tuple of two shares, one for `my_share` and one for `my_queue`.
    @return     None
    """
    # Get references to the share and queue which have been passed to this task
    my_share, my_queue = shares
    turn_flag = 1

    while 1:
        if my_share.get() == 3: # MOVE STATE (S1)
            while 1:
                controller2.run()

                if controller1.encoder.position in\
                 range(controller1.setpoint - 250, controller1.setpoint + 250):        
                    motor2_flag = 1
                    if motor1_flag:
                        my_share.put(4)
                        
                yield
            yield
        elif my_share.get() == 1: # 180 TURN STATE (S2)
            while 1:
                controller2.run()
                # Completes 180 deg turn
                if controller2.encoder.position in range(27500, 28500):
                    if turn_flag:
                        timer = time.ticks_ms()
                        turn_flag = 0
                    print(f"timer = {timer}, {time.ticks_ms()}")
                    if time.ticks_diff(time.ticks_ms(), timer) >= 5000:
                        print("done with delay")
                        controller2.encoder.zero()
                        motor2.set_duty_cycle(0)
                        my_share.put(2)
                yield
            yield
        else: # IDLE STATE (S0)
            yield

def get_coordinates(shares):
    """!
    Task that gets x, y, and z acceleration from the accelerometer
    @param shares A list holding the share and queue used by this task
    """
    # Get references to the share and queue which have been passed to this task
    my_share, my_queue = shares

    while 1:
        if my_share.get() == 2: # GET COORDINATES STATE (S1)
            max_val, max_row, max_col = 0, 0, 0
            row, col = 1, 1

            image = camera.get_image()
            camera.ascii_image(image.pix)
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
                            print(f"updated at {row}, {col} to value {avg}")
                            max_val = avg
                            max_row = row
                            max_col = col
                    col += 1
                row += 1
                col = 1
            print(f"val: {max_val}, row: {max_row}, col: {max_col}")

            x_dist = (max_row - 16) * 3
            y_dist = (max_col - 12) * 3.7
            
            x_ticks = int((atan(x_dist/180) * 60000) // (2 * pi))
            y_ticks = int((atan(y_dist/180) * 528000) // (2 * pi))
            
            print(f"x: {x_ticks}, y: {y_ticks}")
            controller1.set_setpoint(y_ticks)
            controller2.set_setpoint(x_ticks)
            my_share.put(3)
            yield
        else: # IDLE STATE (S0)
            yield

def fire_round(shares):
    """!
    Task that gets x, y, and z acceleration from the accelerometer
    @param shares A list holding the share and queue used by this task
    """
    # Get references to the share and queue which have been passed to this task
    my_share, my_queue = shares

    while 1:
        if my_share.get() == 4: # SHOOT STATE (S1)
            trig_Pin.value(1)
            pyb.delay(500)
            trig_Pin.value(0)

            ## Reset motor flags to 0
            motor1_flag, motor2_flag = 0, 0
            yield
        else: # IDLE STATE (S0)
            yield


if __name__ == "__main__":
    ## Set kp and setpoints for controllers 1 (pitch) where kp = 1 and setpoint = 0
    kp1, sp1 = .8, 100000

    ## Set kp and setpoints for controllers 2 (yaw) where kp = 1 and setpoint = 32000 (180 deg turn)
    kp2, sp2 = .8, 28000

    ## Set motor flags to check if motors have reached positions. Both set to 0
    motor1_flag, motor2_flag = 0, 0

    ## Create a share and a queue to test function and diagnostic printouts
    share0 = task_share.Share('h', thread_protect=False, name="Share 0")
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
    print(f"I2C Scan: {scanhex}")

    ## Create the camera object and set it up in default mode
    camera = MLX_Cam(i2c_bus)

    ## Create pin for trigger fire
    trig_Pin = Pin(Pin.board.PA4, Pin.OUT_PP)

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
        try:
            cotask.task_list.pri_sched()
        except KeyboardInterrupt:
            motor1.set_duty_cycle(0)
            print("motor 1 shut off")
            motor2.set_duty_cycle(0)
            print("motor 2 shut off")
            break

    # Print a table of task data and a table of shared information data
    print('\n' + str (cotask.task_list))
    print(task_share.show_all())
    print(task1.get_trace())
    print('')
