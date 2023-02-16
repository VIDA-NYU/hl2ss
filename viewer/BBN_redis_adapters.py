import os
import hl2ss
import cv2
import time
import asyncio
import struct
import websockets
import numpy as np
from numpy.lib.recfunctions import structured_to_unstructured

import BBN_redis_frame_load as holoframe

# Settings --------------------------------------------------------------------

# HoloLens address
HL_HOST = os.getenv("HOLOLENS_URL") or "192.168.1.164"

# Data server login
API_HOST = os.getenv('API_URL') or 'localhost:8000'
WSURL = f'ws://{API_HOST}'


# stream name and type ID mappers
port2stream_id = {
    hl2ss.StreamPort.PERSONAL_VIDEO: 'main',
    hl2ss.StreamPort.RM_VLC_LEFTLEFT: 'gll',
    hl2ss.StreamPort.RM_VLC_LEFTFRONT: 'glf',
    hl2ss.StreamPort.RM_VLC_RIGHTFRONT: 'grf',
    hl2ss.StreamPort.RM_VLC_RIGHTRIGHT: 'grr',
    hl2ss.StreamPort.RM_DEPTH_LONGTHROW: 'depthlt',
    hl2ss.StreamPort.RM_IMU_ACCELEROMETER: 'imuaccel',
    hl2ss.StreamPort.RM_IMU_GYROSCOPE: 'imugyro',
    hl2ss.StreamPort.RM_IMU_MAGNETOMETER: 'imumag',
}

port2sensor_type = {
    hl2ss.StreamPort.PERSONAL_VIDEO: holoframe.SensorType.PV,
    hl2ss.StreamPort.RM_VLC_LEFTLEFT: holoframe.SensorType.GLL,
    hl2ss.StreamPort.RM_VLC_LEFTFRONT: holoframe.SensorType.GLF,
    hl2ss.StreamPort.RM_VLC_RIGHTFRONT: holoframe.SensorType.GRF,
    hl2ss.StreamPort.RM_VLC_RIGHTRIGHT: holoframe.SensorType.GRR,
    hl2ss.StreamPort.RM_DEPTH_LONGTHROW: holoframe.SensorType.DepthLT,
    hl2ss.StreamPort.RM_IMU_ACCELEROMETER: holoframe.SensorType.Accel,
    hl2ss.StreamPort.RM_IMU_GYROSCOPE: holoframe.SensorType.Gyro,
    hl2ss.StreamPort.RM_IMU_MAGNETOMETER: holoframe.SensorType.Mag,
}


# ----------------------------- Streaming Basics ----------------------------- #

class StreamUpload:
    client=None
    research_mode = False
    # NYU Header Version
    header_version = 3

    port: int

    def __init__(self, host=HL_HOST, api_url=WSURL):
        self.host = host
        self.api_url = api_url
        self.sensor_type = port2sensor_type[self.port]
        self.stream_id = port2stream_id[self.port]

    def create_client(self):
        raise NotImplementedError

    def get_next_packet(self):
        return self.client.get_next_packet()

    def adapt_data(self, data) -> bytes:
        return data

    def __call__(self):
        while True:
            print("Starting...")
            asyncio.run(self.forward_async())
            time.sleep(3)

    async def forward_async(self):
        self.enable = True
        print("Trying to connect to TCP client:", self.host, self.port, '...')
        self.create_client()
        print("Connected!")

        if self.research_mode:
            print("Trying to start research mode subsystem:", self.host, self.port, '...')
            hl2ss.start_subsystem_pv(self.host, self.port)
            print("Started!")
        try:
            print("Opening TCP client...")
            self.client.open()
            print("Opened!")
            try:
                url = f'{self.api_url}/data/{self.stream_id}/push?header=0'
                print("Opening Websocket producer...", url)
                async with websockets.connect(url, close_timeout=10) as ws:
                    print("Opened!")
                    while self.enable:
                        data = self.get_next_packet()
                        await ws.send(self.adapt_data(data))
                        await asyncio.sleep(1e-5)
            finally:
                print("Closing TCP client...")
                self.client.close()
                print("Closed!")
        except Exception as e:
            print("Exception:")
            print(type(e).__name__, e)
        finally:
            if self.research_mode:
                print("Closing research mode subsystem:", self.host, self.port, '...')
                hl2ss.stop_subsystem_pv(self.host, self.port)
                print("Closed!")


# -------------------------------- Main Camera ------------------------------- #

class PVFrameUpload(StreamUpload):
    port = hl2ss.StreamPort.PERSONAL_VIDEO
    # Encoded stream average bits per second
    # Must be > 0
    bitrate = 5*1024*1024
    profile = hl2ss.VideoProfile.H265_MAIN

    def __init__(self, *a, width=760, height=428, fps=15, **kw):
        self.width = width
        self.height = height
        self.fps = fps
        super().__init__(*a, **kw)

    def create_client(self):
        self.client = hl2ss.rx_decoded_pv(
            self.host, self.port, 
            hl2ss.ChunkSize.PERSONAL_VIDEO, 
            hl2ss.StreamMode.MODE_1, 
            self.width, self.height, self.fps, 
            self.profile, self.bitrate, 'bgr24')

    def adapt_data(self, data) -> bytes:
        '''Pack image as JPEG with header.'''
        img_str = cv2.imencode('.jpg', data.payload)[1].tobytes()
        pose_info = (
            data.pose.astype('f').tobytes() + 
            data.focal_length.astype('f').tobytes() + 
            data.principal_point.astype('f').tobytes())
        nyu_header = struct.pack(
            "<BBQIIII", self.header_version, self.sensor_type, 
            data.timestamp, data.payload.shape[1], data.payload.shape[0], 
            len(img_str), len(pose_info))
        return nyu_header + img_str + pose_info


# ------------------------------- Side Cameras ------------------------------- #

class VLCFrameUpload(StreamUpload):
    port = hl2ss.StreamPort.PERSONAL_VIDEO
    # Encoded stream average bits per second
    # Must be > 0
    bitrate = 1 * 1024 * 1024
    profile = hl2ss.VideoProfile.H265_MAIN

    ports = [
        hl2ss.StreamPort.RM_VLC_LEFTLEFT,
        hl2ss.StreamPort.RM_VLC_LEFTFRONT,
        hl2ss.StreamPort.RM_VLC_RIGHTFRONT,
        hl2ss.StreamPort.RM_VLC_RIGHTRIGHT,
    ]

    def __init__(self, host=HL_HOST, cam_idx=0, **kw):
        self.port = self.ports[cam_idx]
        super().__init__(host, **kw)

    def create_client(self):
        self.client = hl2ss.rx_decoded_rm_vlc(
            self.host, self.port, 
            hl2ss.ChunkSize.RM_VLC, 
            hl2ss.StreamMode.MODE_1, 
            self.profile, self.bitrate)

    def adapt_data(self, data) -> bytes:
        '''Pack image as JPEG with header.'''
        img_str = cv2.imencode('.jpg', data.payload, [int(cv2.IMWRITE_JPEG_QUALITY), 70])[1].tobytes()
        pose_info = data.pose.astype('f').tobytes()
        nyu_header = struct.pack(
            "<BBQIIII", self.header_version, self.sensor_type, 
            data.timestamp, data.payload.shape[1], data.payload.shape[0], 
            len(img_str), len(pose_info))
        return nyu_header + img_str + pose_info


# ----------------------------------- Depth ---------------------------------- #

class DepthFrameUpload(StreamUpload):
    port = hl2ss.StreamPort.RM_DEPTH_LONGTHROW
    # Encoded stream average bits per second
    # Must be > 0
    bitrate = 1 * 1024 * 1024

    def create_client(self):
        self.client = hl2ss.rx_decoded_rm_depth_longthrow(
            self.host, self.port, 
            hl2ss.ChunkSize.RM_DEPTH_LONGTHROW, 
            hl2ss.StreamMode.MODE_1, 
            hl2ss.PngFilterMode.Paeth)

    def adapt_data(self, data) -> bytes:
        depth_img_str = data.payload.depth.tobytes()
        ab_img_str = cv2.imencode('.jpg', data.payload.ab, [int(cv2.IMWRITE_JPEG_QUALITY), 70])[1].tobytes()
        pose_info = data.pose.astype('f').tobytes()
        nyu_header = struct.pack(
            "<BBQIIII", self.header_version, self.sensor_type, data.timestamp, 
            data.payload.depth.shape[1], data.payload.depth.shape[0], 
            len(depth_img_str), len(pose_info)+len(ab_img_str))
        return nyu_header + depth_img_str + pose_info + ab_img_str


# ------------------------------------ IMU ----------------------------------- #

class ImuUpload(StreamUpload):
    port: int
    chunk_size: int
    mode: int = hl2ss.StreamMode.MODE_0
    def create_client(self):
        self.client = hl2ss.rx_rm_imu(self.host, self.port, self.chunk_size, self.mode)

    def adapt_data(self, data) -> bytes:
        imu_array = np.frombuffer(data.payload, dtype = ("u8,u8,f4,f4,f4"))
        imu_data = structured_to_unstructured(imu_array[['f2', 'f3', 'f4']]).tobytes()
        imu_timestamps = imu_array['f0'].tobytes()
        nyu_header = struct.pack(
            "<BBQIIII", self.header_version, self.sensor_type, 
            data.timestamp, 3, imu_array.shape[0], 4 * 3 * imu_array.shape[0], len(imu_timestamps))
        return nyu_header + imu_data + imu_timestamps


class ImuAccelUpload(ImuUpload):
    port = hl2ss.StreamPort.RM_IMU_ACCELEROMETER
    chunk_size = hl2ss.ChunkSize.RM_IMU_ACCELEROMETER

class ImuGyroUpload(ImuUpload):
    port = hl2ss.StreamPort.RM_IMU_GYROSCOPE
    chunk_size = hl2ss.ChunkSize.RM_IMU_GYROSCOPE

class ImuMagUpload(ImuUpload):
    port = hl2ss.StreamPort.RM_IMU_MAGNETOMETER
    chunk_size = hl2ss.ChunkSize.RM_IMU_MAGNETOMETER


if __name__ == '__main__':
    import fire
    fire.Fire({
        'pv': PVFrameUpload,
        'vlc': VLCFrameUpload,
        'depth': DepthFrameUpload,
        'accel': ImuAccelUpload,
        'gyro': ImuGyroUpload,
        'mag': ImuMagUpload,
    })
