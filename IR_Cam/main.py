import utime as time
from machine import Pin, I2C
from mlx90640.mlx_cam import MLX_Cam

# The test code sets up the sensor, then grabs and shows an image in a terminal
# every ten and a half seconds or so.
## @cond NO_DOXY don't document the test code in the driver documentation
if __name__ == "__main__":

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

    print("MXL90640 Easy(ish) Driver Test")

    # Select MLX90640 camera I2C address, normally 0x33, and check the bus
    i2c_address = 0x33
    scanhex = [f"0x{addr:X}" for addr in i2c_bus.scan()]
    print(f"I2C Scan: {scanhex}")

    # Create the camera object and set it up in default mode
    camera = MLX_Cam(i2c_bus)

    while True:
        try:
            input1 = input("Enter 1 to take a picture: ")
            if input1 == '1':
                # Get and image and see how long it takes to grab that image
                print("Click.", end='')
                begintime = time.ticks_ms()
                image = camera.get_image()
                print(f" {time.ticks_diff(time.ticks_ms(), begintime)} ms")

                # Can show image.v_ir, image.alpha, or image.buf; image.v_ir best?
                # Display pixellated grayscale or numbers in CSV format; the CSV
                # could also be written to a file. Spreadsheets, Matlab(tm), or
                # CPython can read CSV and make a decent false-color heat plot.
                show_image = True
                show_csv = False
                if show_image:
                    camera.ascii_image(image.pix)
                elif show_csv:
                    for line in camera.get_csv(image.pix, limits=(0, 99)):
                        print(line)
                else:
                    camera.ascii_art(image.pix)
                time.sleep_ms(10000)

        except KeyboardInterrupt:
            break

    print ("Done.")
