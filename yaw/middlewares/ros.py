import logging
import atexit

import rospy
import std_msgs.msg
import sensor_msgs.msg


from yaw.utils import SingletonOptimized
from yaw.connect.wrapper import MiddlewareCommunicator


class ROSMiddleware(metaclass=SingletonOptimized):

    @staticmethod
    def activate(**kwargs):
        ROSMiddleware(**kwargs)

    def __init__(self, node_name="yaw", anonymous=True, disable_signals=True, *args, **kwargs):
        logging.info("Initialising ROS middleware")
        rospy.init_node(node_name, anonymous=anonymous, disable_signals=disable_signals)
        atexit.register(MiddlewareCommunicator.close_all_instances)
        atexit.register(self.deinit)

    @staticmethod
    def deinit():
        logging.info("Deinitialising ROS middleware")
        rospy.signal_shutdown('Deinit')


class ROSNativeObjectService(object):
  _type           = 'yaw_services/ROSNativeObject'
  _md5sum         = '46a550fd1ca640b396e26ebf988aed7b'  # AddTwoInts '6a2e34150c00229791cc89ff309fff21'
  _request_class  = std_msgs.msg.String
  _response_class = std_msgs.msg.String


class ROSImageService(object):
  _type           = 'yaw_services/ROSImage'
  _md5sum         = 'f720f2021b4bbbe86b0f93b08906381c'  # AddTwoInts '6a2e34150c00229791cc89ff309fff21'
  _request_class  = std_msgs.msg.String
  _response_class = sensor_msgs.msg.Image
