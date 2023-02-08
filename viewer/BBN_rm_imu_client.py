import cv2
import ptgctl
import ptgctl.util
from ptgctl import holoframe
import hl2ss
import hl2ss_BBN

# Settings --------------------------------------------------------------------
url = hl2ss_BBN.url
username = hl2ss_BBN.username
password = hl2ss_BBN.password

# Port
# Options:
# hl2ss.StreamPort.RM_IMU_ACCELEROMETER
# hl2ss.StreamPort.RM_IMU_GYROSCOPE
# hl2ss.StreamPort.RM_IMU_MAGNETOMETER
port = hl2ss.StreamPort.RM_IMU_ACCELEROMETER
stream_name = hl2ss_BBN.stream_names[port]
#------------------------------------------------------------------------------

class exampleApp:
    def __init__(self):
        self.api = ptgctl.API(username=username,
                              password=password,
                              url=url)
    
    @ptgctl.util.async2sync
    async def run(self, prefix=None):
        async with self.api.data_pull_connect(stream_name, batch=False) as ws_pull:
            while True:
                for sid, t, buffer in await ws_pull.recv_data():
                    d = holoframe.load(buffer)
                    print('data: ', d['data'])
                    print('timestamp: ', d['timestamps'])

        
if __name__ == '__main__':
    import fire
    fire.Fire(exampleApp)
