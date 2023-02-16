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
port = hl2ss.StreamPort.SPATIAL_INPUT

# Stream name
stream_name = hl2ss_BBN.stream_names[port]

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
        
        client = hl2ss.rx_si(host, port, hl2ss.ChunkSize.SPATIAL_INPUT)
        client.open()
        async with self.api.data_push_connect([stream_name], batch=False) as ws_push:
            while self.enable:
                data = client.get_next_packet()
                nyu_header = struct.pack("<BBQIIII", hl2ss_BBN.header_version, hl2ss_BBN.port2SensorType[port], data.timestamp, 0, 0, len(data.payload), 0)
                frame = nyu_header + data.payload

                await ws_push.send_data([frame], [stream_name])
        
        client.close()
        listener.join()
       
if __name__ == '__main__':
    import fire
    fire.Fire(exampleApp)
