import os
import cv2
import websockets
import BBN_redis_frame_load as holoframe

URL=os.getenv("API_URL") or 'localhost:8000'

class async2sync:
    '''Helper to have a method be both sync and async.'''
    def __init__(self, func_async):
        import functools
        functools.update_wrapper(self, func_async)
        self.asyncio = func_async

    def __get__(self, inst, own):
        return self.__class__(self.asyncio.__get__(inst, own))

    def __call__(self, *a, **kw):
        import asyncio
        return asyncio.run(self.asyncio(*a, **kw))


@async2sync
async def receive_image(sid: str, norm=False):
    async with websockets.connect(f'ws://{URL}/data/{sid}/pull?header=0&latest=1', max_size=None) as ws:
        while True:
            # read the data
            data = await ws.recv()
            if not data:
                print("No data yet :(")
                continue
            d = holoframe.load(data)
            print('timestamp: ', d['time'])
            if 'cam2world' in d:
                print('cam2world: ', d['cam2world'])
            im = cv2.cvtColor(d['image'], cv2.COLOR_BGR2RGB)
            if norm:
                im = ((im - im.min()) / (im.max() - im.min()) * 255).astype('uint8')
            cv2.imshow(sid, im)
            cv2.waitKey(1)



@async2sync
async def receive_imu(sid: str):
    async with websockets.connect(f'ws://{URL}/data/{sid}/pull?header=0&latest=1', max_size=None) as ws:
        while True:
            # read the data
            data = await ws.recv()
            if not data:
                print("No data yet :(")
                continue
            d = holoframe.load(data)
            print('data', d['data'].shape, 'timestamps', d['timestamps'].shape)



if __name__ == '__main__':
    import fire
    fire.Fire({
        'image': receive_image,
        'imu': receive_imu,
    })