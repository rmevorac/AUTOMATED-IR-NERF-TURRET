import pyb
import gc
import utime as time
from pyb import Pin as Pin
#from machine import Pin, I2C

from mlx90640 import MLX90640
from mlx90640.calibration import NUM_ROWS, NUM_COLS, IMAGE_SIZE, TEMP_K
from mlx90640.image import ChessPattern, InterleavedPattern
from mma8451.mma845x import MMA845x

import task.cotask as cotask
import task.task_share as task_share
from motor.encoder_reader import Encoder
from motor.motor_driver import MotorDriver
from motor.controller import Controller

def get_params():
    '''!
    @brief      Prompts the user to enter KP and setpoint values.
    @details    This function prompts the user for two values, the KP and setpoint,
                which are used to control the motor. It repeatedly prompts the user
                until valid input is entered.
    @param      None
    @return     Tuple of strings, containing the KP and setpoint values.
    '''
    while True:
        try:
            ## Stores the KP value send from the decoder PC
            kp = float(input("Enter a KP: "))
            ## Stores the setpoint value send from the decoder PC
            setpoint = int(input("Enter a setpoint: "))
            return (kp, setpoint)
        except ValueError:
            print("Please enter a valid input")

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
        controller1.run()
        
        ticks_left = controller1.motor_data[1] - params1[1] # change to sp1
        
        if abs(ticks_left) < 50:
            while 1:
                motor1.set_duty_cycle(70)
                print("fire")
                yield
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

    while 1:
        controller2.run()       
        yield

def do_calculations(shares):
    """!
    Task that gets x, y, and z acceleration from the accelerometer
    @param shares A list holding the share and queue used by this task
    """
    # Get references to the share and queue which have been passed to this task
    my_share, my_queue = shares


def fire_round(shares):
    """!
    Task that gets x, y, and z acceleration from the accelerometer
    @param shares A list holding the share and queue used by this task
    """
    # Get references to the share and queue which have been passed to this task
    my_share, my_queue = shares




if __name__ == "__main__":
    ## Set kp and setpoints for controller
    # kp1, sp1, kp2, sp2 = 5, 16000, 1.5, 27000

    ## Prompting user for KP and setpoint for controller1
    params1 = get_params()
    
    ## Prompting user for KP and setpoint for controller2
    #params2 = get_params()

    ## Create a share and a queue to test function and diagnostic printouts
    share0 = task_share.Share('h', thread_protect=False, name="Share 0")
    q0 = task_share.Queue('h', 16, thread_protect=False, overwrite=False,
                          name="Queue 0")

    ## Create accelerometer object with 
    #mma = MMA845x(pyb.I2C(1, pyb.I2C.MASTER, baudrate = 100000), 29)

    ## The creation of the motor 1 object
    motor1 = MotorDriver(Pin.board.PC1, Pin.board.PA0, Pin.board.PA1, 5)

    ## The creation of the motor 2 object
    motor2 = MotorDriver(Pin.board.PA10, Pin.board.PB4, Pin.board.PB5, 3)

    ## The creation of the encoder 1 object
    encoder1 = Encoder(Pin.board.PC6, Pin.board.PC7, 8)
    
    ## The creation of the encoder 2 object
    encoder2 = Encoder(Pin.board.PB6, Pin.board.PB7, 4)

    ## Once motor, encoder and params are collected they are used to create this controller 1 object
    controller1 = Controller(params1[0], params1[1], motor1, encoder1)

    ## Once motor, encoder and params are collected they are used to create this controller 2 object
    #controller2 = Controller(params2[0], params2[1], motor2, encoder2)

    # Create the tasks. If trace is enabled for any task, memory will be
    # allocated for state transition tracing, and the application will run out
    # of memory after a while and quit. Therefore, use tracing only for 
    # debugging and set trace to False when it's not needed
    task1 = cotask.Task(move_pitch_motor, name="Task_1", priority=1, period=50,
                        profile=True, trace=False, shares=(share0, q0))
    task2 = cotask.Task(move_yaw_motor, name="Task_2", priority=2, period=50,
                        profile=True, trace=False, shares=(share0, q0))
    cotask.task_list.append(task1)
    #cotask.task_list.append(task2)

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





#     # The following import is only used to check if we have an STM32 board such
#     # as a Pyboard or Nucleo; if not, use a different library
#     try:
#         from pyb import info
# 
#     # Oops, it's not an STM32; assume generic machine.I2C for ESP32 and others
#     except ImportError:
#         # For ESP32 38-pin cheapo board from NodeMCU, KeeYees, etc.
#         i2c_bus = I2C(1, scl=Pin(22), sda=Pin(21))
# 
#     # OK, we do have an STM32, so just use the default pin assignments for I2C1
#     else:
#         i2c_bus = I2C(1)
# 
#     # Select MLX90640 camera I2C address, normally 0x33, and check the bus
#     i2c_address = 0x33
#     scanhex = [f"0x{addr:X}" for addr in i2c_bus.scan()]
#     print(f"I2C Scan: {scanhex}")
# 
#     ## Create the camera object and set it up in default mode
#     camera = MLX_Cam(i2c_bus)

