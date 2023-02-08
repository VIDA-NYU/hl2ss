import hl2ss

import json
import asyncio
import functools
import requests
import websockets
from concurrent.futures import ProcessPoolExecutor

HOST = 'localhost:8000'
URL = 'http://{HOST}'
WSURL = 'ws://{HOST}'



class async2sync:
    '''Helper to have a method be both sync and async.'''
    def __init__(self, func_async):
        self.func_async = func_async
        functools.update_wrapper(self.__call__, func_async)
        functools.update_wrapper(self.asyncio, func_async)

    def __get__(self, inst, own):
        return self.__class__(self.func_async.__get__(inst, own))

    def __call__(self, *a, **kw):
        return asyncio.run(self.func_async(*a, **kw))

    async def asyncio(self, *a, **kw):
        return await self.func_async(*a, **kw)


def write_data_to_redis(data, stream_id):
    r = requests.post(f'{URL}/data/{stream_id}', files=[('entries', (stream_id, data))])
    if r.status_code >= 500:
        raise requests.HTTPError(r.content)
    r.raise_for_status()

async def write_client_to_redis(client, stream_id):
    while True:
        try:
            client.open()
            async with websockets.connect(f'{WSURL}/data/{stream_id}/push?header=0') as ws:
                while True:
                    data = client.get_next_packet()
                    await ws.send(data)
        except Exception as e:
            import traceback
            traceback.print_exc()
            await asyncio.sleep(1)
        finally:
            client.close()


async def listen_for_settings(client, stream_id):
    while True:
        try:
            client.open()
            async with websockets.connect(f'{WSURL}/data/{stream_id}/pull?header=0', max_size=None) as ws:
                while True:
                    config = json.loads(await ws.recv())
                    getattr(client, config['command'])(*config['args'])
                    # client.set_pv_focus(focus_mode, auto_focus_range, manual_focus_distance, focus_value, driver_fallback)
                    # client.set_pv_video_temporal_denoising(video_temporal_denoising)
                    # client.set_pv_white_balance_preset(white_balance_preset)
                    # client.set_pv_white_balance_value(white_balance_value)
                    # client.set_pv_exposure(exposure_mode, exposure_value)
                    # client.set_pv_exposure_priority_video(exposure_priority_video)
                    # client.set_pv_iso_speed(iso_speed_mode, iso_speed_value)
                    # client.set_pv_scene_mode(scene_mode)
                    # client.set_hs_marker_state(marker_state)
        except Exception as e:
            import traceback
            traceback.print_exc()
            await asyncio.sleep(1)
        finally:
            client.close()




def start():
    #------------------------------------------------------------------------------
    client = hl2ss.tx_rc(host, hl2ss.IPCPort.REMOTE_CONFIGURATION)
    version = client.get_application_version()
    print('Installed version {v0}.{v1}.{v2}.{v3}'.format(v0=version[0], v1=version[1], v2=version[2], v3=version[3]))
    utc_offset = client.get_utc_offset(32)
    print('QPC timestamp to UTC offset is {offset} hundreds of nanoseconds'.format(offset=utc_offset))
    client.set_hs_marker_state(marker_state)
    pv_status = client.get_pv_subsystem_status()
    print('PV subsystem is {status}'.format(status=('On' if pv_status else 'Off')))






data = hl2ss.download_calibration_pv(host, port, width, height, framerate)

client = hl2ss.rx_pv(host, port, hl2ss.ChunkSize.PERSONAL_VIDEO, mode, width, height, framerate, profile, bitrate)
client = hl2ss.rx_microphone(host, port, hl2ss.ChunkSize.MICROPHONE, profile)
client = hl2ss.rx_rm_depth_ahat(host, port, hl2ss.ChunkSize.RM_DEPTH_AHAT, mode, profile, bitrate)


#------------------------------------------------------------------------------

client = hl2ss.tx_rc(host, hl2ss.IPCPort.REMOTE_CONFIGURATION)

version = client.get_application_version()
print('Installed version {v0}.{v1}.{v2}.{v3}'.format(v0=version[0], v1=version[1], v2=version[2], v3=version[3]))

utc_offset = client.get_utc_offset(32)
print('QPC timestamp to UTC offset is {offset} hundreds of nanoseconds'.format(offset=utc_offset))

client.set_hs_marker_state(marker_state)

# PV camera configuration
pv_status = client.get_pv_subsystem_status()
print('PV subsystem is {status}'.format(status=('On' if pv_status else 'Off')))



