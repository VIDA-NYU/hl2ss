import hl2ss
from ptgctl import holoframe

# HoloLens address
host = "192.168.1.164"

# Data server login
url = 'your_server_url'
username = 'your_username'
password = 'your_password'

stream_names = {
    hl2ss.StreamPort.PERSONAL_VIDEO: 'main',
    hl2ss.StreamPort.RM_VLC_LEFTFRONT: 'glf', 
    hl2ss.StreamPort.RM_VLC_LEFTLEFT: 'gll', 
    hl2ss.StreamPort.RM_VLC_RIGHTFRONT: 'grf', 
    hl2ss.StreamPort.RM_VLC_RIGHTRIGHT: 'grr',
    hl2ss.StreamPort.RM_DEPTH_LONGTHROW: 'depthlt'
}

header_version = 2

port2SensorType = {
    hl2ss.StreamPort.PERSONAL_VIDEO: holoframe.SensorType.PV,
    hl2ss.StreamPort.RM_VLC_LEFTFRONT: holoframe.SensorType.GLF, 
    hl2ss.StreamPort.RM_VLC_LEFTLEFT: holoframe.SensorType.GLL, 
    hl2ss.StreamPort.RM_VLC_RIGHTFRONT: holoframe.SensorType.GRF, 
    hl2ss.StreamPort.RM_VLC_RIGHTRIGHT: holoframe.SensorType.GRR,
    hl2ss.StreamPort.RM_DEPTH_LONGTHROW: holoframe.SensorType.DepthLT
}
