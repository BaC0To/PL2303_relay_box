import time
from relay_box_PL2303 import RelayBoxUSB


COM_PORT_SETTINGS = {
 "port_num"     : "COM10",
 "baudrate"     : 9600,
 "data_bits"    : 8,
 "parity"       : "N",
 "stop_bits"    : 1,
 "timeout"      : 1
}

RELAY_TYPE_SETTINGS = {
 "model"            : "ICSE012A",
 "nr_channels"      : 4,
 "wake_up_command"  : b'\x50',
 "wake_up_respose"  : b'\xab',
 "start_control"    : b'\x51'
}


relay_module1=RelayBoxUSB(COM_PORT_SETTINGS, RELAY_TYPE_SETTINGS)
relay_module1.reset()
relay_module1.switch_single_channel(channel=4, state=True, debounce_time=0.2)
time.sleep(3)
relay_module1.switch_single_channel(channel=4, state=False, debounce_time=0.2)
# relay_module1.off()
time.sleep(3)
relay_module1.reset()
