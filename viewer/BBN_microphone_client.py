import ptgctl
import ptgctl.util
from ptgctl import holoframe
import hl2ss
import hl2ss_BBN
import hl2ss_utilities
import pyaudio
import queue
import threading

# Settings --------------------------------------------------------------------
url = hl2ss_BBN.url
username = hl2ss_BBN.username
password = hl2ss_BBN.password

port = hl2ss.StreamPort.MICROPHONE
stream_name = hl2ss_BBN.stream_names[port]
#------------------------------------------------------------------------------

enable = True

def pcmworker(pcmqueue):
    global enable
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paFloat32, channels=hl2ss.Parameters_MICROPHONE.CHANNELS, rate=hl2ss.Parameters_MICROPHONE.SAMPLE_RATE, output=True)
    stream.start_stream()
    while (enable):
        stream.write(pcmqueue.get())
    stream.stop_stream()
    stream.close()

pcmqueue = queue.Queue()
thread = threading.Thread(target=pcmworker, args=(pcmqueue,))
thread.start()

class exampleApp:
    def __init__(self):
        self.api = ptgctl.API(username=username,
                              password=password,
                              url=url)
        self.codec = hl2ss.decode_microphone(hl2ss.AudioProfile.AAC_24000)
        self.codec.create()
    
    @ptgctl.util.async2sync
    async def run(self, prefix=None):
        async with self.api.data_pull_connect(stream_name, batch=False) as ws_pull:
            while True:
                for sid, t, buffer in await ws_pull.recv_data():
                    d = holoframe.load(buffer)
                    audio = hl2ss_utilities.microphone_planar_to_packed(self.codec.decode(d['data']))
                    pcmqueue.put(audio.tobytes())
                
            pcmqueue.put(b'')
            thread.join()


        
if __name__ == '__main__':
    import fire
    fire.Fire(exampleApp)
