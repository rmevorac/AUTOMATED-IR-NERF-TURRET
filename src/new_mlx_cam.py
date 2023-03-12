"""!
@file mlx_cam.py

RAW VERSION
This version uses a stripped down MLX90640 driver which produces only raw data,
not calibrated data, in order to save memory.

This file contains a wrapper that facilitates the use of a Melexis MLX90640
thermal infrared camera for general use. The wrapper contains a class MLX_Cam
whose use is greatly simplified in comparison to that of the base class,
@c class @c MLX90640, by mwerezak, who has a cool fox avatar, at
@c https://github.com/mwerezak/micropython-mlx90640

To use this code, upload the directory @c mlx90640 from mwerezak with all its
contents to the root directory of your MicroPython device, then copy this file
to the root directory of the MicroPython device.

There's some test code at the bottom of this file which serves as a beginning
example.

@author mwerezak Original files, Summer 2022
@author JR Ridgely Added simplified wrapper class @c MLX_Cam, January 2023
@copyright (c) 2022 by the authors and released under the GNU Public License,
    version 3.
"""

import utime as time
from machine import Pin, I2C
from mlx90640 import MLX90640
from mlx90640.calibration import NUM_ROWS, NUM_COLS, IMAGE_SIZE, TEMP_K
from mlx90640.image import ChessPattern, InterleavedPattern
from array import array

ZEROD_MATRIX = array('h',
    [23, 29, 20, 14, 22, 26, 23, 12, 13, 22, 16, 10, 3, 15, 13, 6, 12, 34, 9, 18, 19, 32, 18, 22, 11, 44, 23, 31, 14, 38, 23, 32,
    52, 32, 39, 33, 50, 29, 37, 16, 43, 21, 28, 24, 28, 17, 28, 17, 35, 34, 25, 32, 46, 32, 31, 22, 39, 42, 35, 42, 39, 39, 37, 47,
    20, 31, 24, 13, 22, 21, 25, 9, 14, 9, 15, 6, 2, 9, 28, 13, 8, 30, 12, 18, 16, 28, 18, 18, 11, 31, 21, 27, 10, 32, 21, 26,
    47, 32, 41, 33, 54, 26, 38, 29, 44, 25, 36, 30, 32, 20, 44, 33, 15, 14, 10, 19, 27, 13, 12, 20, 19, 28, 20, 30, 23, 24, 19, 29,
    27, 33, 28, 18, 26, 25, 29, 14, 23, 23, 25, 19, 11, 14, 25, 15, -7, 17, -2, 14, 4, 15, 5, 9, 0, 28, 10, 21, -4, 23, 10, 23,
    53, 39, 45, 36, 53, 32, 44, 33, 51, 25, 40, 32, 42, 14, 40, 25, 22, 20, 11, 26, 29, 17, 17, 23, 24, 24, 23, 28, 19, 18, 20, 29,
    35, 42, 34, 26, 37, 35, 37, 23, 25, 29, 33, 26, 23, 28, 33, 15, 13, 34, 17, 23, 23, 33, 24, 25, 16, 44, 23, 36, 18, 40, 26, 33,
    48, 32, 40, 28, 51, 26, 40, 23, 43, 19, 36, 32, 34, 19, 37, 23, 24, 20, 16, 15, 32, 20, 20, 20, 25, 26, 23, 36, 27, 22, 24, 38,
    42, 46, 43, 32, 44, 40, 46, 28, 41, 39, 46, 35, 32, 37, 43, 29, 21, 38, 24, 32, 27, 35, 28, 28, 26, 49, 35, 42, 23, 47, 36, 36,
    42, 22, 33, 27, 45, 20, 35, 18, 41, 15, 33, 28, 32, 12, 33, 22, 18, 8, 6, 16, 21, 8, 10, 11, 19, 23, 14, 29, 17, 18, 19, 27,
    26, 28, 32, 18, 28, 29, 34, 18, 29, 24, 31, 26, 22, 27, 34, 27, 17, 32, 18, 28, 23, 32, 27, 32, 21, 44, 32, 47, 20, 48, 34, 52,
    43, 25, 40, 23, 42, 22, 37, 21, 42, 14, 40, 28, 37, 17, 40, 28, 33, 23, 20, 25, 30, 15, 21, 26, 31, 24, 32, 42, 28, 29, 27, 46,
    39, 40, 42, 26, 39, 35, 41, 21, 35, 30, 45, 31, 35, 34, 46, 32, 31, 45, 27, 28, 28, 37, 30, 26, 28, 45, 39, 43, 27, 47, 40, 50,
    57, 36, 52, 35, 56, 30, 48, 30, 55, 24, 51, 38, 48, 27, 51, 36, 45, 35, 32, 34, 45, 29, 33, 30, 42, 36, 41, 46, 40, 35, 39, 54,
    38, 38, 42, 23, 39, 32, 40, 23, 34, 27, 43, 28, 29, 31, 41, 31, 28, 41, 26, 26, 25, 33, 26, 20, 23, 43, 40, 42, 28, 45, 39, 41,
    53, 35, 44, 34, 49, 29, 34, 34, 40, 17, 27, 25, 32, 14, 25, 26, 69, 49, 1, 40, 4, 64, 41, 18, 39, 33, 17, 13, 77, 48, 37, -18,
    36, 37, 34, 26, 27, 31, 31, 20, 23, 25, 25, 20, 16, 23, 25, 21, 17, 20, 20, 15, 20, 20, 24, 16, 17, 31, 27, 23, 23, 32, 36, 34,
    52, 34, 40, 32, 43, 25, 33, 27, 38, 17, 27, 24, 29, 12, 25, 24, 27, 10, 20, 16, 31, 10, 21, 18, 26, 16, 25, 22, 30, 16, 28, 34,
    49, 50, 46, 39, 42, 46, 40, 30, 33, 36, 36, 29, 29, 35, 38, 33, 30, 34, 32, 23, 34, 34, 36, 25, 33, 41, 39, 33, 36, 41, 45, 39,
    64, 44, 50, 43, 57, 34, 41, 33, 46, 25, 35, 31, 42, 20, 35, 32, 40, 20, 30, 23, 44, 19, 32, 24, 36, 24, 34, 30, 40, 25, 34, 37,
    49, 46, 49, 35, 42, 41, 39, 30, 33, 33, 33, 26, 25, 30, 36, 24, 27, 30, 31, 21, 29, 29, 33, 20, 28, 37, 36, 25, 33, 37, 44, 30,
    76, 51, 63, 52, 68, 44, 52, 42, 56, 33, 45, 38, 49, 28, 46, 37, 50, 28, 42, 33, 50, 26, 39, 29, 45, 31, 42, 35, 48, 32, 46, 39,
    50, 37, 47, 27, 38, 35, 38, 27, 33, 32, 35, 25, 28, 29, 33, 24, 27, 24, 29, 22, 26, 22, 31, 18, 27, 34, 36, 27, 31, 35, 42, 30,
    70, 46, 58, 45, 60, 39, 46, 41, 54, 27, 44, 35, 47, 25, 40, 35, 43, 21, 34, 29, 41, 18, 35, 26, 41, 24, 39, 31, 42, 26, 40, 34])

class MLX_Cam:
    """!
    @brief   Class which wraps an MLX90640 thermal infrared camera driver to
             make it easier to grab and use an image.
    """

    def __init__(self, i2c, address=0x33, pattern=ChessPattern,
                 width=NUM_COLS, height=NUM_ROWS):
        """!
        @brief   Set up an MLX90640 camera.
        @param   i2c An I2C bus which has been set up to talk to the camera;
                 this must be a bus object which has already been set up
        @param   address The address of the camera on the I2C bus (default 0x33)
        @param   pattern The way frames are interleaved, as we read only half
                 the pixels at a time (default ChessPattern)
        @param   width The width of the image in pixels; leave it at default
        @param   height The height of the image in pixels; leave it at default
        """
        ## The I2C bus to which the camera is attached
        self._i2c = i2c
        ## The address of the camera on the I2C bus
        self._addr = address
        ## The pattern for reading the camera, usually ChessPattern
        self._pattern = pattern
        ## The width of the image in pixels, which should be 32
        self._width = width
        ## The height of the image in pixels, which should be 24
        self._height = height

        # The MLX90640 object that does the work
        self._camera = MLX90640(i2c, address)
        self._camera.set_pattern(pattern)
        self._camera.setup()

        ## A local reference to the image object within the camera driver
        self._image = self._camera.raw


    def ascii_image(self, array, pixel="██", textcolor="0;180;0"):
        """!
        @brief   Show low-resolution camera data as shaded pixels on a text
                 screen.
        @details The data is printed as a set of characters in columns for the
                 number of rows in the camera's image size. This function is
                 intended for testing an MLX90640 thermal infrared sensor.

                 A pair of extended ACSII filled rectangles is used by default
                 to show each pixel so that the aspect ratio of the display on
                 screens isn't too smushed. Each pixel is colored using ANSI
                 terminal escape codes which work in only some programs such as
                 PuTTY.  If shown in simpler terminal programs such as the one
                 used in Thonny, the display just shows a bunch of pixel
                 symbols with no difference in shading (boring).

                 A simple auto-brightness scaling is done, setting the lowest
                 brightness of a filled block to 0 and the highest to 255. If
                 there are bad pixels, this can reduce contrast in the rest of
                 the image.

                 After the printing is done, character color is reset to a
                 default of medium-brightness green, or something else if
                 chosen.
        @param   array An array of (self._width * self._height) pixel values
        @param   pixel Text which is shown for each pixel, default being a pair
                 of extended-ASCII blocks (code 219)
        @param   textcolor The color to which printed text is reset when the
                 image has been finished, as a string "<r>;<g>;<b>" with each
                 letter representing the intensity of red, green, and blue from
                 0 to 255
        """
        minny = min(array)
        scale = 255.0 / (max(array) - minny)
        for row in range(self._height):
            for col in range(self._width):
                pix = int((array[row * self._width + (self._width - col - 1)]
                           - minny) * scale)
                print(f"\033[38;2;{pix};{pix};{pix}m{pixel}", end='')
            print(f"\033[38;2;{textcolor}m")


    ## A "standard" set of characters of different densities to make ASCII art
    asc = " -.:=+*#%@"


    def ascii_art(self, array):
        """!
        @brief   Show a data array from the IR image as ASCII art.
        @details Each character is repeated twice so the image isn't squished
                 laterally. A code of "><" indicates an error, probably caused
                 by a bad pixel in the camera. 
        @param   array The array to be shown, probably @c image.v_ir
        """
        scale = len(MLX_Cam.asc) / (max(array) - min(array))
        offset = -min(array)
        for row in range(self._height):
            line = ""
            for col in range(self._width):
                pix = int((array[row * self._width + (self._width - col - 1)]
                           + offset) * scale)
                try:
                    the_char = MLX_Cam.asc[pix]
                    print(f"{the_char}{the_char}", end='')
                except IndexError:
                    print("><", end='')
            print('')
        return


    def get_csv(self, array, limits=None):
        """!
        @brief   Generate a string containing image data in CSV format.
        @details This function generates a set of lines, each having one row of
                 image data in Comma Separated Variable format. The lines can
                 be printed or saved to a file using a @c for loop.
        @param   array The array of data to be presented
        @param   limits A 2-iterable containing the maximum and minimum values
                 to which the data should be scaled, or @c None for no scaling
        """
        if limits and len(limits) == 2:
            scale = (limits[1] - limits[0]) / (max(array) - min(array))
            offset = limits[0] - min(array)
        else:
            offset = 0.0
            scale = 1.0
        for row in range(self._height):
            line = ""
            for col in range(self._width):
                pix = int((array[row * self._width + (self._width - col - 1)]
                          + offset) * scale)
                if col:
                    line += ","
                line += f"{pix}"
            yield line
        return


    def get_image(self):
        """!
        @brief   Get one image from a MLX90640 camera.
        @details Grab one image from the given camera and return it. Both
                 subframes (the odd checkerboard portions of the image) are
                 grabbed and combined (maybe; this is the raw version, so the
                 combination is sketchy and not fully tested). It is assumed
                 that the camera is in the ChessPattern (default) mode as it
                 probably should be.
        @returns A reference to the image object we've just filled with data
        """
        for subpage in (0, 1):
            while not self._camera.has_data:
                time.sleep_ms(50)
                print('.', end='')
            image = self._camera.read_image(subpage)
            print(image)

        return image