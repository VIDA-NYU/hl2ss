'''Universal parser for Hololens messages.
This is here for convenience but won't be necessary for too much longer
'''
# from collections import namedtuple
import struct
from collections import defaultdict
import json
import numpy as np
from PIL import Image
import cv2


class SensorType:
    PV = 0
    DepthLT = 1
    DepthAHAT = 2
    GLL = 3
    GLF = 4
    GRF = 5
    GRR = 6
    Accel = 7
    Gyro = 8
    Mag = 9
    numSensor = 10
    Calibration = 11
    Microphone = 12
    SpatialInput = 13
    # !!! these are circumstantial
    Mic = 172
    Hand = 34
    Eye = 34



header_dtype = np.dtype([
    ('version', np.uint8), 
    ('ftype', np.uint8),
    ('time', np.uint64),
])
header2_dtype = np.dtype([
    ('w', np.uint32),
    ('h', np.uint32),
    ('payload_size', np.uint32),
    ('info_size', np.uint32),
])


def load(data, metadata=False, only_header=False):
    '''Parse any frame of data coming from the hololens.'''
    parse = ByteParser(data)
    read = not metadata  # disable reading images

    version, ftype, ts = parse.pop(header_dtype)
    d = dict(frame_type=ftype)

    # special cases

    # json list - no header
    if ftype in {123,93}:
        d['values'] = parse.reset().pop_json()
        return d
    # hand+eye - no header
    if ftype in {34}: 
        if only_header:
            return d
        vals = parse.reset().pop_json()
        for k in ['left', 'right']:
            if k in vals and isinstance(vals[k], str):
                vals[k] = json.loads(vals[k])
        d.update(vals)
        return d
    # microphone
    if ftype == 172:
        d['sr'], channels, d['pos'] = parse.reset().unpack('<iiq')
        if only_header:
            return d
        d['audio'] = parse.pop(np.float32, (-1, channels), read=read)
        return d

    d['time'] = ts

    if only_header:
        return d
    
    if version == 1:
        return load_v1(parse, read, ftype, d)
    elif version == 2:
        return load_v2(parse, read, ftype, d)
    elif version == 3:
        return load_v3(parse, read, ftype, d)
    
    raise ValueError(f"unknown header version: {version}")
    
def load_v1(parse, read, ftype, d):
    w, h, stride, info_size = parse.pop(header2_dtype)
    im_size = w*h*stride

    # image
    if ftype in {SensorType.PV, SensorType.GLF, SensorType.GRR, SensorType.GRF, SensorType.GLL}:
        yuv = ftype in {SensorType.PV}
        rot = -1 if ftype in {SensorType.GLF, SensorType.GRR} else 1 if ftype in {SensorType.GRF, SensorType.GLL} else 0
        d['image'] = parse.pop_image(w, h, stride, yuv=yuv, rot=rot, read=read)
    
        if info_size > 0:
            d['cam2world' if ftype in {SensorType.PV} else 'rig2world'] = parse.pop(np.float32, (4,4), T=True)
            if ftype in {SensorType.PV}:
                d['focalX'], d['focalY'] = parse.pop(np.float32, (2,))
                d['principalX'], d['principalY'] = parse.pop(np.float32, (2,))
        return d

    # depth
    if ftype in {SensorType.DepthLT, SensorType.DepthAHAT}:
        d['image'] = parse.pop(np.uint16, (h, w), read=read)
        if info_size >= im_size:
            info_size -= im_size
            d['infrared'] = parse.pop(np.uint16, (h, w), read=read)
        if info_size > 0:
            d['rig2world'] = parse.pop(np.float32, (4,4), T=True)
        return d

    # sensors
    if ftype in {SensorType.Accel, SensorType.Gyro, SensorType.Mag}:
        d['data'] = parse.pop(np.float32, (h, w), im_size, read=read)
        timestamps = parse.pop(np.uint64, size=info_size)
        d['timestamps'] = (timestamps - timestamps[0]) // 100 + d['time']
        return d

    # calibration
    if ftype in {SensorType.Calibration}:
        d['lut'] = parse.pop(np.float32, (w * h, 3), read=read)
        d['rig2cam'] = parse.pop(np.float32, (4,4), T=True)
        return d

    raise ValueError(f"unknown frame type: {ftype}")
    
def load_v2(parse, read, ftype, d):
    w, h, stride, info_size = parse.pop(header2_dtype)
    im_size = w*h*stride
    
    # main
    if ftype == SensorType.PV:
        d['image'] = parse.pop_jpeg_image(stride, bgr2rgb=True, read=read)
        d['cam2world'] = parse.pop(np.float32, (4,4), T=True)
        d['focalX'], d['focalY'] = parse.pop(np.float32, (2,))
        d['principalX'], d['principalY'] = parse.pop(np.float32, (2,))
        return d

    # grayscale
    if ftype in {SensorType.GLF, SensorType.GRR, SensorType.GRF, SensorType.GLL}:
        rot = -1 if ftype in {SensorType.GLF, SensorType.GRR} else 1
        d['image'] = parse.pop_jpeg_image(stride, rot=rot, read=read)
        d['rig2world'] = parse.pop(np.float32, (4,4), T=True)
        return d

    # depth
    if ftype == SensorType.DepthLT:
        d['image'] = parse.pop(np.uint16, (h, w), read=read)
        d['rig2world'] = parse.pop(np.float32, (4,4), T=True)
        info_size -= np_size(np.float32, shape = (4,4))
        if info_size > 0:
            d['infrared'] = parse.pop_jpeg_image(info_size, read=read)
        return d

    # sensors
    if ftype in {SensorType.Accel, SensorType.Gyro, SensorType.Mag}:
        d['data'] = parse.pop(np.float32, (h, w), im_size, read=read)
        timestamps = parse.pop(np.uint64, size=info_size)
        d['timestamps'] = (timestamps - timestamps[0]) // 100 + d['time']
        return d

    # calibration
    if ftype in {SensorType.Calibration}:
        d['lut'] = parse.pop(np.float32, (w * h, 3), read=read)
        d['rig2cam'] = parse.pop(np.float32, (4,4), T=True)
        return d

def load_v3(parse, read, ftype, d):
    w, h, payload_size, info_size = parse.pop(header2_dtype)
    
    # main
    if ftype == SensorType.PV:
        d['image'] = parse.pop_jpeg_image(payload_size, bgr2rgb=False, read=read)
        d['cam2world'] = parse.pop(np.float32, (4,4), T=True)
        d['focalX'], d['focalY'] = parse.pop(np.float32, (2,))
        d['principalX'], d['principalY'] = parse.pop(np.float32, (2,))
        return d

    # grayscale
    if ftype in {SensorType.GLF, SensorType.GRR, SensorType.GRF, SensorType.GLL}:
        rot = -1 if ftype in {SensorType.GLF, SensorType.GRR} else 1
        d['image'] = parse.pop_jpeg_image(payload_size, rot=rot, read=read)
        d['rig2world'] = parse.pop(np.float32, (4,4), T=True)
        return d

    # depth
    if ftype == SensorType.DepthLT:
        d['image'] = parse.pop(np.uint16, (h, w), read=read)
        d['rig2world'] = parse.pop(np.float32, (4,4), T=True)
        info_size -= np_size(np.float32, shape = (4,4))
        if info_size > 0:
            d['infrared'] = parse.pop_jpeg_image(info_size, read=read)
        return d

    # sensors
    if ftype in {SensorType.Accel, SensorType.Gyro, SensorType.Mag}:
        d['data'] = parse.pop(np.float32, (h, w), payload_size, read=read)
        d['timestamps'] = parse.pop(np.uint64, size=info_size)
        return d

    # calibration
    if ftype == SensorType.Calibration:
        d['lut'] = parse.pop(np.float32, (w * h, 3), read=read)
        d['rig2cam'] = parse.pop(np.float32, (4,4), T=True)
        return d
    
    if ftype == SensorType.Microphone:
        d['channels'] = w
        d['sample_rate'] = h
        d['data'] = parse.pop(size=payload_size, read=False)
        return d
    
    if ftype == SensorType.SpatialInput:
        d['data'] = parse.pop(size=payload_size, read=False)
        return d

    raise ValueError(f"unknown frame type: {ftype}")    
    


class ByteParser:
    def __init__(self, data):
        self.data = memoryview(data)
        self.offset = 0

    @property
    def remaining(self) -> int:
        return len(self.data) - self.offset

    @property
    def total(self) -> int:
        return len(self.data)

    def _pop_bytes(self, size: int) -> memoryview:
        if size is None:  # if None, go to the end
            size = len(self.data) - self.offset
        i, j = self.offset, self.offset + size
        self.offset = j
        return self.data[i:j]

    def _read_np(self, x: memoryview, dtype, shape=None, T=False) -> np.ndarray:
        x = np.frombuffer(x, dtype)
        if shape:
            x = x.reshape(shape)
        elif x.size == 1:
            x = x.item()
        if T:
            x = x.T
        return x

    def _read_image(self, im: memoryview, w, h, rot=0, yuv=False) -> np.ndarray:
        im = np.array(Image.frombytes('L', (w, h), bytes(im)))
        if yuv:
            im = cv2.cvtColor(im[:,:-8], cv2.COLOR_YUV2RGB_NV12)
        if rot:
            im = np.rot90(im, rot)
        return im
    
    def _read_jpeg_image(self, im: memoryview, rot=0, bgr2rgb=False) -> np.ndarray:
        im = cv2.imdecode(np.frombuffer(im, dtype=np.uint8), cv2.IMREAD_UNCHANGED)
        if bgr2rgb:
            im = cv2.cvtColor(im, cv2.COLOR_BGR2RGB)
        if rot:
            im = np.rot90(im, rot)
        return im

    def _read_json(self, x: memoryview):
        return json.loads(str(x, 'ascii'))

    def pop(self, dtype=None, shape=None, size=None, read=True, **kw):
        x = self._pop_bytes(size or np_size(dtype, shape))
        if read:
            x = self._read_np(x, dtype, shape, **kw)
        return x

    def pop_image(self, w: int, h: int, stride: int, read=True, **kw):
        x = self._pop_bytes(w * h * stride)
        if read:
            x = self._read_image(x, w, h, **kw)
        return x
    
    def pop_jpeg_image(self, imsize: int, read=True, **kw):
        x = self._pop_bytes(imsize)
        if read:
            x = self._read_jpeg_image(x, **kw)
        return x

    def pop_json(self, size=None, read=True):
        x = self._pop_bytes(size)
        if read:
            x = self._read_json(x)
        return x

    def unpack(self, format) -> tuple:
        data = self._pop_bytes(struct.calcsize(format))
        return struct.unpack(format, data)

    def reset(self):
        self.offset = 0
        return self


def np_size(dtype, shape=None):
    '''Get the size of an array with data type and shape.'''
    mult = 1
    for s in shape or ():
        if s < 0:
            return None
        mult *= s
    return np.dtype(dtype).itemsize * mult