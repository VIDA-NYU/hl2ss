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
port = hl2ss.StreamPort.RM_DEPTH_LONGTHROW

# VLC Stream name
stream_name = hl2ss_BBN.stream_names[port]

# DON'T change these variables unless if necessary ----------------------------

# Operating mode
mode = hl2ss.StreamMode.MODE_1

# PNG filter
png_filter = hl2ss.PngFilterMode.Paeth

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
        
        client = hl2ss.rx_decoded_rm_depth_longthrow(host, port, hl2ss.ChunkSize.RM_DEPTH_LONGTHROW, mode, png_filter)
        client.open()
        async with self.api.data_push_connect([stream_name], batch=False) as ws_push:
            while self.enable:
                data = client.get_next_packet()
                
                depth_img_str = data.payload.depth.tobytes()
                ab_img_str = cv2.imencode('.jpg', data.payload.ab, [int(cv2.IMWRITE_JPEG_QUALITY), 70])[1].tobytes()
                pose_info = data.pose.astype('f').tobytes()
                nyu_header = struct.pack("<BBQIIII", hl2ss_BBN.header_version, hl2ss_BBN.port2SensorType[port], data.timestamp, data.payload.depth.shape[1], data.payload.depth.shape[0], len(depth_img_str), len(pose_info)+len(ab_img_str))
                frame = nyu_header + depth_img_str + pose_info + ab_img_str
                
                await ws_push.send_data([frame], [stream_name])
        
        client.close()
        listener.join()
       
if __name__ == '__main__':
    import fire
    fire.Fire(exampleApp)
