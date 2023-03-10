"""
Miscellaneous functions and classes

=====================================================
Copyright 2023, Max van den Boom (Multimodal Neuroimaging Lab, Mayo Clinic, Rochester MN)

This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
You should have received a copy of the GNU General Public License along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
import os
import logging
import numpy as np
import time
import subprocess
from math import ceil
from ieegprep.utils.console import ConsoleColors


def allocate_array(dimensions, fill_value=np.nan, dtype=np.float64):
    """
    Create and immediately allocate the memory for an x-dimensional array

    Before allocating the memory, this function checks if is enough memory is available (this is needed since when a
    numpy array is allocated and there is not enough memory, sometimes python crashes without the chance to catch an error).

    Args:
        dimensions (int or tuple):
        fill_value (any numeric):
        dtype (str):

    Returns:
        data (ndarray):             An initialized x-dimensional array, or None if insufficient memory available

    """
    # initialize a data buffer (channel x trials/epochs x time)
    mem = None
    try:

        # create a ndarray object (no memory is allocated here)
        data = np.empty(dimensions, dtype=dtype)
        data_bytes_needed = data.nbytes

        # import here to decrease the package dependencies for this module
        from psutil import virtual_memory

        # check if there is enough memory available
        mem = virtual_memory()
        if mem.available <= data_bytes_needed:
            raise MemoryError()

        # allocate the memory
        data.fill(fill_value)

        #
        return data

    except MemoryError:
        if mem is None:
            logging.error('Not enough memory available to create array.\n(for docker users: extend the memory resources available to the docker service)')
        else:
            logging.error('Not enough memory available to create array.\nAt least ' + str(int((mem.used + data_bytes_needed) / (1024.0 ** 2))) + ' MB total is needed, most likely more.\n(for docker users: extend the memory resources available to the docker service)')
        raise MemoryError('Not enough memory available to create array.')


def create_figure(width=500, height=500, onScreen=False):
    """
    Create a figure in memory or on-screen, and resize the figure to a specific resolution

    """

    # import here to decrease the package dependencies for this module
    import matplotlib.pyplot as plt
    from matplotlib.figure import Figure

    if onScreen:
        fig = plt.figure()
    else:
        fig = Figure()

    # resize the figure
    DPI = fig.get_dpi()
    fig.set_size_inches(float(width) / float(DPI), float(height) / float(DPI))

    return fig


def is_number(value):
    try:
        float(value)
        return True
    except:
        return False


def is_valid_numeric_range(value):
    """
    Check if the given value is a valid range; a tuple or list with two numeric values

    Args:
        value (tuple or list):  The input value to check

    Returns:
        True is valid range, false if not
    """
    if not isinstance(value, (list, tuple)):
        return False
    if not len(value) == 2:
        return False
    if not is_number(value[0]):
        return False
    if not is_number(value[1]):
        return False
    return True


def number_to_padded_string(value, width=0, pos_space=True):
    """
    Convert a number to a space padded string

    Args:
        value (int or float):   The value to convert to a fixed width string
        width (int):            The total length of the return string; < 0 is pad left; > 0 is pad right
        pos_space (bool):       Flag whether a space-character should be added before positive numbers

    """
    padded_str = ' ' if (pos_space and value >= 0) else ''
    padded_str += str(value)
    if width < 0:
        padded_str = padded_str.rjust(width * -1, ' ')
    elif width > 0:
        padded_str = padded_str.ljust(width, ' ')
    return padded_str


def numbers_to_padded_string(values, width=0, pos_space=True, separator=', '):
    """
    Convert multiple numbers to fixed width string with space padding in the middle

    Args:
        value (tuple or list):  The values that will be converted into a fixed width string
        width (int):            The total length of the return string
        pos_space (bool):       Flag whether a space-character should be added before positive numbers
        separator (string):     Separator string after each value

    """
    if len(values) == 0:
        return ''

    padded_values = []
    total_value_width = 0
    for value in values:
        padded_values.append(number_to_padded_string(value, 0, pos_space))
        total_value_width += len(padded_values[-1])

    padded_str = padded_values[0]

    if len(values) == 1:
        return padded_values[0].ljust(width, ' ')

    sep_width = (width - total_value_width - ((len(values) - 1) * len(separator))) / (len(values) - 1)
    if sep_width < 1:
        sep_width = 1
    else:
        sep_width = ceil(sep_width)

    for iValue in range(1,len(padded_values)):
        padded_str += separator
        if len(padded_str) + sep_width + len(padded_values[iValue]) > width:
            padded_str += ''.ljust(width - len(padded_str) - len(padded_values[iValue]), ' ')
        else:
            padded_str += ''.ljust(sep_width, ' ')
        padded_str += padded_values[iValue]

    return padded_str


def run_cmd(command, env={}):
    merged_env = os.environ
    merged_env.update(env)
    merged_env.pop('DEBUG', None)
    process = subprocess.run(command,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT,
                             shell=True,
                             universal_newlines=True,
                             env=merged_env,
                             encoding='utf-8')
    return process


def time_func(fun, pre_fun = None, loop = 5, *args, **kwargs):
    """
    Time and retrieve statistics on the performance of a given function

    Args:
        fun (function):                 The function to time the performance on
        pre_fun (function):             Function that is called every time prior to calling the function being
                                        timed, but not counted as part of the performance time
        loop (int):                     Number of times the function is called
        args (*args):
        kwargs (**kwargs):

    Returns:
        mean:                       The function's average execution time (in ms)
        std:                        The standard deviation in the function's execution time
        range (tuple):              The range of the function's execution time. The first value is minimum, second is the maximum
        times (nparray):            All result values

    """
    if loop < 1:
        loop = 1
    times = np.zeros(loop)

    # repeatedly call function
    for iLoop in range(0, loop):

        # execute the pre-function if there is one
        if pre_fun :
            pre_fun()

        # execute function and measure
        time1 = time.time()
        fun(*args, **kwargs)
        time2 = time.time()

        # store
        times[iLoop] = (time2 - time1) * 1000.0

    # return statistics
    return times.mean(), times.std(), (times.min(), times.max()), times


def clear_virtual_cache():
    """
    Try to clear the virtual memory (pagefile)
    """

    from sys import platform
    if platform == "win32":
        # Note: Running the RAMMAP executable will usually popup a User Access Control (UAC), warning about changes
        #       being made to the computer. This can be prevented by either temporarily setting the UAC
        #       notification setting to off (don't forget to turn it back on after) or to disable UAC for
        #       only the RAMMap64 executable

        # check whether the executable exits
        if not os.path.exists('RAMMap64.exe'):
            ConsoleColors.print_error('Error: could not find RAMMAP64.exe to clear virtual memory.\nDownload RAMMAP tools from Microsoft Sysinternals, and make sure the RAMMAP64.exe file is into the script directory (or can be found through the environment variable $PATH)')
            exit(1)

        # call clear executable
        os.system('RAMMap64.exe -Et')
        print('Cleared virtual memory')

    elif platform in ("linux", "linux2"):

        os.sync()
        with open('/proc/sys/vm/drop_caches', 'w') as f:
            f.write("1\n")
        print('Cleared virtual memory')

    elif platform == "darwin":
        # Note: Executing the command 'purge' to clear the virtual memory should prompt for a password, but
        #       it is better to edit the 'sudoers' file, so that the 'purge' command can be executed without the
        #       admin password. To achieve this:
        #        1. In a terminal type 'sudo visudo' to edit the 'sudoers' file
        #        2. At the end of that file add a line:
        #           <mac username> ALL = NOPASSWD: /usr/sbin/purge
        #           e.g. john ALL = NOPASSWD: /usr/sbin/purge
        #        3. save and close the file

        # create bash file to GUI prompt for a password
        with open('./mac_prompt_pw.sh', 'w') as f:
            f.write('#!/bin/bash\n')
            f.write('pw="$(osascript -e \'Tell application "System Events" to display dialog "Password to purge virtual memory:" default answer "" with hidden answer\' -e \'text returned of result\' 2>/dev/null)" && echo "$pw"\n')

        # call the purge command while prompting for the password (MacOS for some reason requires high privileges on the Purge command)
        # (with 4 retries in case of mac 'error initializing audit plugin sudoers_audit' error)
        os.environ['SUDO_ASKPASS'] = './mac_prompt_pw.sh'
        os.system('chmod +x ./mac_prompt_pw.sh')
        retry_purge = 0
        while retry_purge < 5:
            if os.system('sudo -A /usr/sbin/purge') == 0:
                break
            else:
                print('Retry purge')
                retry_purge += 1
        if retry_purge == 5:
            ConsoleColors.print_error('Could not purge virtual memory after 5 tries, skipping')
        os.remove('./mac_prompt_pw.sh')

        #
        print('Cleared virtual memory')
