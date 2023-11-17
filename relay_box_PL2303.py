import time
import io
import struct
import logging
import serial


_log = logging.getLogger(__name__)
_log.setLevel(logging.DEBUG)


class RelayBoxUSB():
    """
    USB to VCP via PL2303 4ch. relay box class.
    """

    def __init__(self, com_port_settings:dict, relay_type_settings:dict):
        assert com_port_settings is not None
        assert relay_type_settings is not None

        self._port:            str = com_port_settings["port_num"]
        self._baudrate:        int = com_port_settings["baudrate"]
        self._data_bits:       int = com_port_settings["data_bits"]
        self._parity:          str = com_port_settings["parity"]
        self._stopbits:        int = com_port_settings["stop_bits"]
        self._timeout:         int = com_port_settings["timeout"]

        self._model:           str = relay_type_settings["model"]
        self._nr_channels:      int = relay_type_settings["nr_channels"]
        self._wake_up_command: str = relay_type_settings["wake_up_command"]
        self._wake_up_respose: str = relay_type_settings["wake_up_respose"]
        self._start_control:   str = relay_type_settings["start_control"]

        self.ser            = None
        self.channel        = None
        self.last_state_val = None
        self.init_module()

    def init_module(self):
        """
        Initialisation of the USB relay box.

        Args:
            None

        Returns:
            None
        """
        with serial.Serial(port=self._port, baudrate=self._baudrate, \
                bytesize=self._data_bits , parity=self._parity, \
                    stopbits=self._stopbits, timeout=self._timeout ) as ser:

            sio = io.TextIOWrapper(io.BufferedRWPair(ser, ser))
            self.ser = ser
            #self.ser.write(self._wake_up_command)
            #sio.flush()
            #bitPattern_all_off = 255 # always start with all off
            #bitPattern = b''
            #bitPattern += struct.pack('!B',bitPattern_all_off)
            #self.ser.write(bitPattern)
            #self.last_state_val = bitPattern_all_off
            sio.flush()
            self.wait_for_init()

    def wait_for_init(self):
        """
        Waiting for a correct response from the used relay box
        """
        read_data = None
        start_time = time.time()
        while read_data != self._wake_up_respose:
            time.sleep(0.1)
            _log.warning("Relay Module: %s, are you there?", self._model)
            read_data = self.ser.readline()
            if read_data == self._wake_up_respose:
                _log.warning("YES! Received response from %s: %s", self._model, read_data)
                self.ser.write(self._start_control)
                bitPattern_all_off = 255 # all off
                self.last_state_val = bitPattern_all_off
                if self.last_state_val != bitPattern_all_off:
                    bitPattern = b''
                    bitPattern += struct.pack('!B',bitPattern_all_off)
                    self.ser.write(bitPattern)
                    time.sleep(0.2)
                break
            else:
                mid_tme = time.time()
                if abs(mid_tme-start_time) <= 3:
                    self.ser.write(self._wake_up_command)
                else:
                    _log.warning("Skipping initialization of: %s. \
                        Device hasn't been unplugged from USB", self._model)
                    break

    def switch_single_channel(self, channel:int, state:bool, debounce_time:float):
        """
        Method for controlling a desired relay NO contact state.

        Args:
            channel (int): Represents a relay channel from 1 to 4
            state (bool): Relay state True=On / False=Off

        Returns:
            None
        """
        with serial.Serial(port=self._port, baudrate=self._baudrate, \
                   bytesize=self._data_bits , parity=self._parity, \
                    stopbits=self._stopbits, timeout=self._timeout ) as ser:

            sio = io.TextIOWrapper(io.BufferedRWPair(ser, ser))
            self.ser = ser
            self.channel = channel
            sio.flush()
            bit = channel - 1
            start_val = str(self.last_state_val)
            if state is False:
                new_val = RelayBoxUSB.set_bit(value=int(start_val, 0), bit_index=bit)
            else:
                new_val = RelayBoxUSB.clear_bit(value=int(start_val, 0), bit_index=bit)
            self.last_state_val = str(new_val)
            new_val_as_bytes = b''
            new_val_as_bytes += struct.pack('!B',new_val)
            self.ser.write(new_val_as_bytes)
            time.sleep(debounce_time)
            _log.warning("Relay ch.: %s is set to state: %s", channel, state)

    def reset(self):
        """
        Method for resetting all relays (All NO relay contacts opened).

        Args:
            None

        Returns:
            None
        """
        with serial.Serial(port=self._port, baudrate=self._baudrate, \
                   bytesize=self._data_bits , parity=self._parity, \
                    stopbits=self._stopbits, timeout=self._timeout ) as ser:

            sio = io.TextIOWrapper(io.BufferedRWPair(ser, ser))
            self.ser = ser
            sio.flush()

            bitPattern = b'\xFF' # all off
            self.ser.write(bitPattern)
            self.last_state_val = 255
            time.sleep(0.2)
            listed_channels = []
            for item in range(0, self._nr_channels):
                listed_channels.append(str(item+1))
            _log.warning("All relay ch.: %s are set to state: False", listed_channels)

    def on(self):
        """
        Method for setting all relays to enabled state (NO contact closed)

        Args:
            None

        Returns:
            None
        """
        with serial.Serial(port=self._port, baudrate=self._baudrate, \
                bytesize=self._data_bits , parity=self._parity, \
                stopbits=self._stopbits, timeout=self._timeout ) as ser:

            sio = io.TextIOWrapper(io.BufferedRWPair(ser, ser))
            self.ser = ser
            sio.flush()
            bitPattern_all_on = 0 # all on
            if self.last_state_val != bitPattern_all_on:
                new_val_as_bytes = b''
                new_val_as_bytes += struct.pack('!B',bitPattern_all_on)
                self.ser.write(new_val_as_bytes)
                time.sleep(0.2)
            self.last_state_val = bitPattern_all_on

    def off(self):
        """
        Method for setting all relays to disabled state (NO contact opened)

        Args:
            None

        Returns:
            None
        """
        with serial.Serial(port=self._port, baudrate=self._baudrate, \
                bytesize=self._data_bits , parity=self._parity, \
                stopbits=self._stopbits, timeout=self._timeout ) as ser:

            sio = io.TextIOWrapper(io.BufferedRWPair(ser, ser))
            self.ser = ser
            sio.flush()
            bitPattern_all_off = 255 # all off
            if self.last_state_val != bitPattern_all_off:
                new_val_as_bytes = b''
                new_val_as_bytes += struct.pack('!B',bitPattern_all_off)
                self.ser.write(new_val_as_bytes)
                time.sleep(0.2)
            self.last_state_val = bitPattern_all_off

    def off_on(self, min_duration=500):
        """
        Switch off power, wait for at least min_duration milliseconds
        and turn power back on.

        Args:
            min_duration (int): Time in milliseconds for power outage

        Returns:
           None
        """
        self.off()
        time.sleep(min_duration * 1e-3)
        self.on()

    def on_off(self, min_duration=500):
        """
        Switch on power, wait for at least min_duration milliseconds
        and turn power back off.

        Args:
            min_duration (int): Time in milliseconds for power enabled duration

        Returns:
           None
        """
        self.on()
        time.sleep(min_duration * 1e-3)
        self.off()

    @staticmethod
    def set_bit(value, bit_index):
        return value | (1<<bit_index)

    @staticmethod
    def clear_bit(value, bit_index):
        return value & ~(1<<bit_index)

    @staticmethod
    def toggle_bit(value, bit_index):
        return value ^ (1 << bit_index)
