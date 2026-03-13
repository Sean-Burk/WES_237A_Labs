#   Copyright (c) 2016, Xilinx, Inc.
#   SPDX-License-Identifier: BSD-3-Clause


import time
import struct
from pynq.lib.pmod import Pmod
from pynq.lib.pmod import PMOD_NUM_DIGITAL_PINS
import asyncio
from pynq.lib.pmod import MAILBOX_OFFSET
from pynq.lib.pmod import MAILBOX_PY2IOP_CMD_OFFSET



PMOD_IR_PROGRAM = "/home/xilinx/jupyter_notebooks/Project/pmod_ir_transceiver.bin"
CONFIG_IOP_SWITCH = 0x1
GENERATE = 0x3
STOP = 0x5
WRITE = 0x7
READ = 0x9


class Pmod_IRTransceiver(object):
    """This class uses the PWM class as referece to send data over 
    an IR led. 

    Attributes
    ----------
    microblaze : Pmod
        Microblaze processor instance used by this module.

    """
    def __init__(self, mb_info, send_idx, receive_idx):
        """Return a new instance of an Pmod_IRTransceiver object. 
        
        Parameters
        ----------
        mb_info : dict
            A dictionary storing Microblaze information, such as the
            IP name and the reset name.
        index : int
            The specific pin that runs the IR LED.
            
        """
        if send_idx not in range(PMOD_NUM_DIGITAL_PINS):
            raise ValueError("Valid pin indexes are 0 - {}."
                             .format(PMOD_NUM_DIGITAL_PINS-1))
        if receive_idx not in range(PMOD_NUM_DIGITAL_PINS):
            raise ValueError("Valid pin indexes are 0 - {}."
                             .format(PMOD_NUM_DIGITAL_PINS-1))
        

        self.microblaze = Pmod(mb_info, PMOD_IR_PROGRAM)
        
        # Write PWM pin config
        self.microblaze.write_mailbox(0, send_idx)
        self.microblaze.write_mailbox(4, receive_idx)
        
        # Write configuration and wait for ACK
        self.microblaze.write_blocking_command(CONFIG_IOP_SWITCH)
            
    def generate(self, period, duty_cycle):
        """Generate pwm signal with desired period and percent duty cycle.
        
        Parameters
        ----------
        period : int
            The period of the tone (us), between 1 and 65536.
        duty_cycle : int
            The duty cycle in percentage.
        
        Returns
        -------
        None
                
        """
        if period not in range(1, 65536):
            raise ValueError("Valid tone period is between 1 and 65536.")
        if duty_cycle not in range(1, 99):
            raise ValueError("Valid duty cycle is between 1 and 99.")

        self.microblaze.write_mailbox(0, [period, duty_cycle])
        self.microblaze.write_blocking_command(GENERATE)

    def stop(self):
        """Stops PWM generation.

        Returns
        -------
        None

        """
        self.microblaze.write_blocking_command(STOP)

    def write(self, data):
        """Writes data to IR LED. blocking.

        Parameters
        ----------
        data : bytearray
            Data to write over LED.  Max lenght 64 bytearray.

        Returns
        -------
        None
        """
        if len(data)>64:
            raise ValueError("Max write lenth is 64 bytes")
        if len(data)==0:
            raise ValueError("data is empty")
        
        self.microblaze.write_mailbox(0, len(data))
        print(f"sending {len(data)} bytes")
        self.microblaze.write_mailbox(4, data)
        self.microblaze.write_blocking_command(WRITE)

    async def write_async(self, data, sleep_dur=0.05):
        """Writes data to IR LED asyncrounusly

        Parameters
        ----------
        data : bytearray
            Data to write over LED.  Max lenght 64 bytearray.

        Returns
        -------
        None
        """
        if len(data)>16:
            raise ValueError("Max write lenth is 16 bytes")
        if len(data)==0:
            raise ValueError("data is empty")
        
        self.microblaze.write_mailbox(0, len(data))
        print(f"sending {len(data)} bytes")
        for i in range(0, len(data), 4):
            word = 0 
            for j in range(min(4, len(data)-i)):
                word+= data[i+j]<<((3-j)*8)
            self.microblaze.write_mailbox(4+i, word)
        self.microblaze.write_non_blocking_command(WRITE)
        while self.microblaze.read(MAILBOX_OFFSET + MAILBOX_PY2IOP_CMD_OFFSET) != 0:
            await asyncio.sleep(sleep_dur)

    async def read_async(self, read_len, sleep_dur=0.05):
        """Reads data from IR receiver asyncrounusly.
        
        Parameters
        ----------
        read_len : int 
            lenght in bytes of the read.
        
        Returns
        -------
        data : bytes
            Data that was received 
        """

        if read_len <= 0:
            raise ValueError("real len must be positive number")
        if read_len > 16:
            raise ValueError("max read lenght 16 bytes")
        self.microblaze.write_mailbox(0, read_len)
        self.microblaze.write_non_blocking_command(READ)
        while self.microblaze.read(MAILBOX_OFFSET + MAILBOX_PY2IOP_CMD_OFFSET) != 0:
            await asyncio.sleep(sleep_dur)
        # read back the response from the mailbox
        data = bytearray(0)
        actual_read_len = self.microblaze.read_mailbox(0)
        error = self.microblaze.read_mailbox(4)
        for i in range(0, actual_read_len, 4):
            byte_4 = self.microblaze.read_mailbox(i+8)
            for j in range(min(4, actual_read_len-i)):
                data.append((byte_4>>((3-j)*8))&0xFF)
        return (actual_read_len, data, error)
