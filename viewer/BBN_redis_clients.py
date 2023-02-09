import os
import cv2
import websockets
import BBN_redis_frame_load as holoframe

URL=os.getenv("API_URL") or 'localhost:8000'

class async2sync:
    '''Helper to have a method be both sync and async.'''
    def __init__(self, func_async):
        self.func_async = func_async
        import functools
        functools.update_wrapper(self.__call__, func_async)
        functools.update_wrapper(self.asyncio, func_async)

    def __get__(self, inst, own):
        return self.__class__(self.func_async.__get__(inst, own))

    def __call__(self, *a, **kw):
        import asyncio
        return asyncio.run(self.func_async(*a, **kw))

    async def asyncio(self, *a, **kw):
        return await self.func_async(*a, **kw)


@async2sync
async def receive_image(sid: str):
    async with websockets.connect(f'ws://{URL}/data/{sid}/pull?header=0', max_size=None) as ws:
        while True:
            # read the data
            data = await ws.recv()
            d = holoframe.load(data)
            print('timestamp: ', d['time'])
            print('cam2world: ', d['cam2world'])
            cv2.imshow('image', d['image'])
            cv2.waitKey(1)



if __name__ == '__main__':
    import fire
    fire.Fire({
        'image': receive_image
    })