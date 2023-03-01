import pyb
import gc
import utime as time
from pyb import Pin as Pin
#from machine import Pin, I2C

from mlx90640 import MLX90640
from mlx90640.calibration import NUM_ROWS, NUM_COLS, IMAGE_SIZE, TEMP_K
from mlx90640.image import ChessPattern, InterleavedPattern
from mma8451.mma845x import *

from task.cotask import cotask
from task.task_share import task_share
from motor_driver.encoder_reader import Encoder
from motor_driver.motor_driver import MotorDriver
from motor_driver.controller import Controller

def get_accel(shares):
    """!
    Task that gets x, y, and z acceleration from the accelerometer
    @param shares A list holding the share and queue used by this task
    """
    # Get references to the share and queue which have been passed to this task
    my_share, my_queue = shares

    mma.active()
    while True:
        x,y,z= mma.get_accels()
        my_queue.put(x)
        my_queue.put(y)
        my_queue.put(z)

        yield 0

if __name__ == "__main__":
    ## Set kp and setpoints for controller
    kp1, kp2, sp1, sp2 = .01, .01, 1000, 1000

    ## Create a share and a queue to test function and diagnostic printouts
    share0 = task_share.Share('h', thread_protect=False, name="Share 0")
    q0 = task_share.Queue('h', 16, thread_protect=False, overwrite=False,
                          name="Queue 0")

    ## Create accelerometer object with 
    mma = MMA845x(pyb.I2C(1, pyb.I2C.MASTER, baudrate = 100000), 29)

    ## The creation of the motor 1 object
    motor1 = MotorDriver(Pin.board.PC1, Pin.board.PA0, Pin.board.PA1, 5)

    ## The creation of the motor 2 object
    motor2 = MotorDriver(Pin.board.PA10, Pin.board.PB4, Pin.board.PB5, 3)

    ## The creation of the encoder 1 object
    encoder1 = Encoder(Pin.board.PB6, Pin.board.PB7, 4)

    ## The creation of the encoder 2 object
    encoder2 = Encoder(Pin.board.PC6, Pin.board.PC7, 8)

    ## Once motor, encoder and params are collected they are used to create this controller 1 object
    controller1 = Controller(kp1, sp1, motor1, encoder1)

    ## Once motor, encoder and params are collected they are used to create this controller 2 object
    controller2 = Controller(kp2, sp2, motor2, encoder2)

    # Create the tasks. If trace is enabled for any task, memory will be
    # allocated for state transition tracing, and the application will run out
    # of memory after a while and quit. Therefore, use tracing only for 
    # debugging and set trace to False when it's not needed
    task1 = cotask.Task(get_accel, name="Task_1", priority=2, period=500,
                        profile=True, trace=False, shares=(share0, q0))
    task2 = cotask.Task(task2_fun, name="Task_2", priority=1, period=500,
                        profile=True, trace=False, shares=(share0, q0))
    cotask.task_list.append(task1)
    cotask.task_list.append(task2)

    # Run the memory garbage collector to ensure memory is as defragmented as
    # possible before the real-time scheduler is started
    gc.collect()

    # Run the scheduler with the chosen scheduling algorithm. Quit if ^C pressed
    while True:
        try:
            cotask.task_list.pri_sched()
        except KeyboardInterrupt:
            break

    # Print a table of task data and a table of shared information data
    print('\n' + str (cotask.task_list))
    print(task_share.show_all())
    print(task1.get_trace())
    print('')





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

    # Select MLX90640 camera I2C address, normally 0x33, and check the bus
    i2c_address = 0x33
    scanhex = [f"0x{addr:X}" for addr in i2c_bus.scan()]
    print(f"I2C Scan: {scanhex}")

    ## Create the camera object and set it up in default mode
    camera = MLX_Cam(i2c_bus)

