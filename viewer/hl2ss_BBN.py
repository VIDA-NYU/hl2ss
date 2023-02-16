import hl2ss
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
    hl2ss.StreamPort.RM_IMU_MAGNETOMETER: 'imumag'
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
    hl2ss.StreamPort.RM_IMU_MAGNETOMETER: holoframe.SensorType.Mag
}
