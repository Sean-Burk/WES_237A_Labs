from enum import IntEnum
import asyncio
from OLEDDisplay import OLEDDisplay
from pmod_ir_transceiver import Pmod_IRTransceiver
import struct
from PIL import Image

class IRCastMode(IntEnum):
    STRING_MODE = 1
    SENSE_MODE = 2
    BITMAP_MODE = 3
    ERROR_MODE = 4

class SensorID(IntEnum):
    TEMP_SENSOR = 1
    LIGHT_SENSOR = 2
    HEART_SENSOR = 3

mode_title = {
    IRCastMode.SENSE_MODE  : " IR-Cast Sense ",
    IRCastMode.STRING_MODE : "IR-Cast String ",
    IRCastMode.BITMAP_MODE : "IR-Cast Bitmap ",
    IRCastMode.ERROR_MODE :  "ERROR INVALID  "
}

class IRCast:
    def __init__(self, pmod_screen, pmod_ir):
        self.mode = IRCastMode.STRING_MODE
        self.string_list = ["                "]*8
        self.string_list[0] = mode_title[IRCastMode.STRING_MODE]
        self.new_mode = 0
        self.msg_data = 0
        # connect to screen
        self.disp = OLEDDisplay(pmod_screen)
        self.disp.connect()
        self.disp.clear()
        # self.disp.write_basic_str("    IR-Cast     ")
        self.disp.display_jpg(Image.open("IRCast_logo.jpg"))
        # connect to IR tranceiver
        self.ir_tran = Pmod_IRTransceiver(pmod_ir, 1, 0)

        # dict of modes
        self.mode_dict = {
            IRCastMode.SENSE_MODE: self.mode_sense,
            IRCastMode.STRING_MODE: self.mode_string,
            IRCastMode.BITMAP_MODE: self.mode_bitmap,
            IRCastMode.ERROR_MODE: self.mode_error,
        }
    
    async def run(self):
        loop = asyncio.get_event_loop()
        loop.create_task(self.read_task())
        while True:
            if self.new_mode == 0:
                await asyncio.sleep(0.01)
                continue
            if self.new_mode!=self.mode:
                self.disp.clear()
            msg_data = self.msg_data
            self.msg_data=0
            self.mode = self.new_mode
            self.new_mode=0

            self.disp.write_basic_str(mode_title[self.mode])
            self.mode_dict[self.mode](msg_data)
            # add extra sleep so run rate isn't too high 
            # maybe remove later
            # await asyncio.sleep(0.1) 
    
    def mode_string(self, msg_data):
        # print(f"mode string {msg_data}")
        line_num, line_str = msg_data
        if line_num>7 or line_num<0:
            print(f"Error invalid line number: {line_num}")
            return
        if len(line_str)!=16:
            print(f"Error line string must be 16 got: {line_str}")
            return
        self.string_list[line_num] = line_str
        for i, line in enumerate(self.string_list):
            self.disp.write_basic_str(line, y=i)
        self.disp.flush()
    
    def mode_sense(self, msg_data):
        sensor_id, sensor_value = msg_data
        try:
            sensor_id = SensorID(sensor_id)
            sensor_value = float(sensor_value)
        except ValueError:
            print(f"Error invalid sensor message {sensor_id}, {sensor_value}")
            return
        match sensor_id:
            case SensorID.TEMP_SENSOR:
                self.disp.write_basic_str(f"Temp: {sensor_value:8.2f}F", y=1)
            case SensorID.LIGHT_SENSOR:
                if sensor_value>1:
                    self.disp.write_basic_str(f"Light:   Dark   ", y=2)
                else:
                    self.disp.write_basic_str(f"Light:   Light  ", y=2)
                # self.disp.write_basic_str(f"Light: {sensor_value:6.2f}", y=2)

            case SensorID.HEART_SENSOR:
                self.disp.write_basic_str(f"Heart: {sensor_value:5.1f}bpm", y=3)
        self.disp.flush()
        pass

    def mode_bitmap(self, msg_data):
        pass

    def mode_error(self, msg_data):
        pass

    async def read_msg(self):
        read_len, data, debug = await self.ir_tran.read_async(20)
        if read_len!=20:
            print(f"Error bad read {read_len} data: {data}")
            return (0, 0)
        print(f"Read: {data}")
        try:
            mode = IRCastMode(data[0])
        except ValueError:
            print(f"Error invalid mode: {data[0]}")
            return (0, 0)

        match mode:
            case IRCastMode.STRING_MODE:
                line_num, line_str = struct.unpack("<B16s", data[1:18])
                try:
                    line_str.replace(b'\x00', b' ')
                    line_str = line_str.decode('utf-8')
                except UnicodeDecodeError:
                    print(f"Error invalid unicode in string")
                    return (0, 0)
                return (mode,  (line_num, line_str))
            case IRCastMode.SENSE_MODE:
                sensor_id, value = struct.unpack("<Bf", data[1:6])
                return (mode, (sensor_id, value))
            case _:
                return (0, 0)

    async def read_task(self):
        while True:
            if self.new_mode == 0:
                self.new_mode, self.msg_data = await self.read_msg()
            else:
                await asyncio.sleep(0.01)