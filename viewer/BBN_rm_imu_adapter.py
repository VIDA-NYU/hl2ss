from pynput import keyboard

import hl2ss
import cv2

import struct
import ptgctl
import ptgctl.util
import hl2ss_BBN
import numpy as np
from numpy.lib.recfunctions import structured_to_unstructured

# Settings --------------------------------------------------------------------

# HoloLens address
host = hl2ss_BBN.host

# Data server login
url = hl2ss_BBN.url
username = hl2ss_BBN.username
password = hl2ss_BBN.password

# Port
# Options:
# hl2ss.StreamPort.RM_IMU_ACCELEROMETER
# hl2ss.StreamPort.RM_IMU_GYROSCOPE
# hl2ss.StreamPort.RM_IMU_MAGNETOMETER
port = hl2ss.StreamPort.RM_IMU_ACCELEROMETER

# Maximum bytes to receive per step
# Options:
# hl2ss.ChunkSize.RM_IMU_ACCELEROMETER
# hl2ss.ChunkSize.RM_IMU_GYROSCOPE
# hl2ss.ChunkSize.RM_IMU_MAGNETOMETER
chunk_size = hl2ss.ChunkSize.RM_IMU_ACCELEROMETER

# IMU Stream name
stream_name = hl2ss_BBN.stream_names[port]

# DON'T change these variables unless if necessary ----------------------------

# Operating mode
mode = hl2ss.StreamMode.MODE_0

#------------------------------------------------------------------------------

class exampleApp:
    def __init__(self):
        self.api = ptgctl.API(username=username,
                              password=password,
                              url=url)
    
    @ptgctl.util.async2sync
    async def run(self, prefix=None):
        hl2ss.start_subsystem_pv(host, port)

        self.enable = True
        
        def on_press(key):
            self.enable = key != keyboard.Key.esc
            return self.enable
        
        listener = keyboard.Listener(on_press=on_press)
        listener.start()
        
        client = hl2ss.rx_rm_imu(host, port, chunk_size, mode)
        client.open()
        async with self.api.data_push_connect([stream_name], batch=False) as ws_push:
            while self.enable:
                data = client.get_next_packet()
                imu_array = np.frombuffer(data.payload, dtype = ("u8,u8,f4,f4,f4"))
                imu_data = structured_to_unstructured(imu_array[['f2', 'f3', 'f4']]).tobytes()
                imu_timestamps = imu_array['f0'].tobytes()
                nyu_header = struct.pack("<BBQIIII", hl2ss_BBN.header_version, hl2ss_BBN.port2SensorType[port], data.timestamp, 3, imu_array.shape[0], 4, len(imu_timestamps))
                frame = nyu_header + imu_data + imu_timestamps
                
                await ws_push.send_data([frame], [stream_name])
        
        client.close()
        listener.join()
        
        hl2ss.stop_subsystem_pv(host, port)
       
if __name__ == '__main__':
    import fire
    fire.Fire(exampleApp)
