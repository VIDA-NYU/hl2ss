from pynput import keyboard

import hl2ss
import cv2

import struct
import ptgctl
import ptgctl.util
import hl2ss_BBN
import timeit

# Settings --------------------------------------------------------------------

# HoloLens address
host = hl2ss_BBN.host

# Data server login
url = hl2ss_BBN.url
username = hl2ss_BBN.username
password = hl2ss_BBN.password

# Camera parameters
width     = 760
height    = 428
framerate = 15

# Video encoding profile
profile = hl2ss.VideoProfile.H265_MAIN

# Encoded stream average bits per second
# Must be > 0
bitrate = 5*1024*1024

# Port
port = hl2ss.StreamPort.PERSONAL_VIDEO

# PV Stream name
stream_name = hl2ss_BBN.stream_names[port]

# DON'T change these variables unless if necessary ----------------------------

# Operating mode
mode = hl2ss.StreamMode.MODE_1

# Decoded format
decoded_format = 'bgr24'

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
        
        client = hl2ss.rx_decoded_pv(host, port, hl2ss.ChunkSize.PERSONAL_VIDEO, mode, width, height, framerate, profile, bitrate, decoded_format)
        client.open()
        async with self.api.data_push_connect([stream_name], batch=False) as ws_push:
            while self.enable:
                data = client.get_next_packet()
                

                img_str = cv2.imencode('.jpg', data.payload, [int(cv2.IMWRITE_JPEG_QUALITY), 70])[1].tobytes()
                pose_info = data.pose.astype('f').tobytes() + data.focal_length.astype('f').tobytes() + data.principal_point.astype('f').tobytes()
                nyu_header = struct.pack("<BBQIIII", hl2ss_BBN.header_version, hl2ss_BBN.port2SensorType[port], data.timestamp, width, height, len(img_str), len(pose_info))
                frame = nyu_header + img_str + pose_info
                
                await ws_push.send_data([frame], [stream_name])
        
        client.close()
        listener.join()
        
        hl2ss.stop_subsystem_pv(host, port)
       
if __name__ == '__main__':
    import fire
    fire.Fire(exampleApp)
