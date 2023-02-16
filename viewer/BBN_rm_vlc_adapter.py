from pynput import keyboard

import hl2ss
import cv2

import struct
import ptgctl
import ptgctl.util
import hl2ss_BBN

# Settings --------------------------------------------------------------------

# HoloLens address
host = hl2ss_BBN.host

# Data server login
url = hl2ss_BBN.url
username = hl2ss_BBN.username
password = hl2ss_BBN.password

# Port
# Options:
# hl2ss.StreamPort.RM_VLC_LEFTFRONT
# hl2ss.StreamPort.RM_VLC_LEFTLEFT
# hl2ss.StreamPort.RM_VLC_RIGHTFRONT
# hl2ss.StreamPort.RM_VLC_RIGHTRIGHT
port = hl2ss.StreamPort.RM_VLC_LEFTFRONT

# Video encoding profile
profile = hl2ss.VideoProfile.H265_MAIN

# Encoded stream average bits per second
# Must be > 0
bitrate = 1*1024*1024

# VLC Stream name
stream_name = hl2ss_BBN.stream_names[port]

# DON'T change these variables unless if necessary ----------------------------

# Operating mode
mode = hl2ss.StreamMode.MODE_1

#------------------------------------------------------------------------------

class exampleApp:
    def __init__(self):
        self.api = ptgctl.API(username=username,
                              password=password,
                              url=url)
    
    @ptgctl.util.async2sync
    async def run(self, prefix=None):
        self.enable = True
        
        def on_press(key):
            self.enable = key != keyboard.Key.esc
            return self.enable
        
        listener = keyboard.Listener(on_press=on_press)
        listener.start()
        
        client = hl2ss.rx_decoded_rm_vlc(host, port, hl2ss.ChunkSize.RM_VLC, mode, profile, bitrate)
        client.open()
        async with self.api.data_push_connect([stream_name], batch=False) as ws_push:
            while self.enable:
                data = client.get_next_packet()
                
                img_str = cv2.imencode('.jpg', data.payload, [int(cv2.IMWRITE_JPEG_QUALITY), 70])[1].tobytes()
                pose_info = data.pose.astype('f').tobytes()
                nyu_header = struct.pack("<BBQIIII", hl2ss_BBN.header_version, hl2ss_BBN.port2SensorType[port], data.timestamp, data.payload.shape[1], data.payload.shape[0], len(img_str), len(pose_info))
                frame = nyu_header + img_str + pose_info
                
                await ws_push.send_data([frame], [stream_name])
        
        client.close()
        listener.join()
       
if __name__ == '__main__':
    import fire
    fire.Fire(exampleApp)
