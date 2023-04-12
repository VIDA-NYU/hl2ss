import hl2ss
import numpy as np
from ptgctl import holoframe

# HoloLens address
host = "10.18.172.12"

# Data server login
url = 'https://api.ptg.poly.edu'
username = 'your_username'
password = 'your_username'

stream_names = {
    hl2ss.StreamPort.PERSONAL_VIDEO: 'main',
    hl2ss.StreamPort.RM_VLC_LEFTFRONT: 'glf', 
    hl2ss.StreamPort.RM_VLC_LEFTLEFT: 'gll', 
    hl2ss.StreamPort.RM_VLC_RIGHTFRONT: 'grf', 
    hl2ss.StreamPort.RM_VLC_RIGHTRIGHT: 'grr',
    hl2ss.StreamPort.RM_DEPTH_LONGTHROW: 'depthlt',
    hl2ss.StreamPort.RM_IMU_ACCELEROMETER: 'imuaccel',
    hl2ss.StreamPort.RM_IMU_GYROSCOPE: 'imugyro',
    hl2ss.StreamPort.RM_IMU_MAGNETOMETER: 'imumag',
    hl2ss.StreamPort.MICROPHONE: 'mic0',
    hl2ss.StreamPort.SPATIAL_INPUT: 'si'
}

header_version = 3

port2SensorType = {
    hl2ss.StreamPort.PERSONAL_VIDEO: holoframe.SensorType.PV,
    hl2ss.StreamPort.RM_VLC_LEFTFRONT: holoframe.SensorType.GLF, 
    hl2ss.StreamPort.RM_VLC_LEFTLEFT: holoframe.SensorType.GLL, 
    hl2ss.StreamPort.RM_VLC_RIGHTFRONT: holoframe.SensorType.GRF, 
    hl2ss.StreamPort.RM_VLC_RIGHTRIGHT: holoframe.SensorType.GRR,
    hl2ss.StreamPort.RM_DEPTH_LONGTHROW: holoframe.SensorType.DepthLT,
    hl2ss.StreamPort.RM_IMU_ACCELEROMETER: holoframe.SensorType.Accel,
    hl2ss.StreamPort.RM_IMU_GYROSCOPE: holoframe.SensorType.Gyro,
    hl2ss.StreamPort.RM_IMU_MAGNETOMETER: holoframe.SensorType.Mag,
    hl2ss.StreamPort.MICROPHONE: holoframe.SensorType.Microphone,
    hl2ss.StreamPort.SPATIAL_INPUT: holoframe.SensorType.SpatialInput,
    "calibration": holoframe.SensorType.Calibration,
}

def depthFormat2NYU(uv2xy, extrinsics):
    z = np.ones((uv2xy.shape[0], uv2xy.shape[1], 1), dtype=np.float32)
    uv2xyz = np.concatenate((uv2xy, z), axis = 2)
    uv2xyz /= np.linalg.norm(uv2xyz, axis = 2)[:,:,np.newaxis]
    return uv2xyz.tobytes() + extrinsics.tobytes()
