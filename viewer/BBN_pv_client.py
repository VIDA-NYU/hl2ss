import cv2
import ptgctl
import ptgctl.util
from ptgctl import holoframe

# Settings --------------------------------------------------------------------
url = 'your_server_address'
username = 'your_username'
password = 'your_password'

#------------------------------------------------------------------------------

class exampleApp:
    def __init__(self):
        self.api = ptgctl.API(username=username,
                              password=password,
                              url=url)
    
    @ptgctl.util.async2sync
    async def run(self, prefix=None):
        async with self.api.data_pull_connect('main', batch=False) as ws_pull:
            while True:
                for sid, t, buffer in await ws_pull.recv_data():
                    d = holoframe.load(buffer)
                    print('timestamp: ', d['time'])
                    print('pose matrix: ', d['cam2world'])
                    cv2.imshow('image', d['image'])
                    cv2.waitKey(1)
                    
        
if __name__ == '__main__':
    import fire
    fire.Fire(exampleApp)