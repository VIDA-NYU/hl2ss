import ptgctl
import ptgctl.util
from ptgctl import holoframe
import hl2ss
import hl2ss_BBN


# Settings --------------------------------------------------------------------
url = hl2ss_BBN.url
username = hl2ss_BBN.username
password = hl2ss_BBN.password

port = hl2ss.StreamPort.SPATIAL_INPUT
stream_name = hl2ss_BBN.stream_names[port]
#------------------------------------------------------------------------------


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
                    si = hl2ss.unpack_si(d['data'])
                    
                    print('Tracking status at time {ts}'.format(ts=d['time']))

                    if (si.is_valid_head_pose()):
                        head_pose = si.get_head_pose()
                        print('Head pose')
                        print(head_pose.position)
                        print(head_pose.forward)
                        print(head_pose.up)
                        # right = cross(up, -forward)
                        # up => y, forward => -z, right => x
                    else:
                        print('No head pose data')
                    
                    if (si.is_valid_eye_ray()):
                        eye_ray = si.get_eye_ray()
                        print('Eye ray')
                        print(eye_ray.origin)
                        print(eye_ray.direction)
                    else:
                        print('No eye tracking data')
                    
                    if (si.is_valid_hand_left()):
                        hand_left = si.get_hand_left()
                        pose = hand_left.get_joint_pose(hl2ss.SI_HandJointKind.Wrist)
                        print('Left wrist pose')
                        print(pose.orientation)
                        print(pose.position)
                        print(pose.radius)
                        print(pose.accuracy)
                    else:
                        print('No left hand data')
                    
                    if (si.is_valid_hand_right()):
                        hand_right = si.get_hand_right()
                        pose = hand_right.get_joint_pose(hl2ss.SI_HandJointKind.Wrist)
                        print('Right wrist pose')
                        print(pose.orientation)
                        print(pose.position)
                        print(pose.radius)
                        print(pose.accuracy)
                    else:
                        print('No right hand data')


        
if __name__ == '__main__':
    import fire
    fire.Fire(exampleApp)
