import logging
import sys
import json
import time
import threading
import os
import importlib.util
import queue

import numpy as np
import rclpy
from rclpy.node import Node
import std_msgs.msg
import sensor_msgs.msg

from yaw.connect.servers import Server, Servers
from yaw.middlewares.ros2 import ROS2Middleware
from yaw.encoders import JsonEncoder, JsonDecodeHook


class ROS2Server(Server, Node):

    def __init__(self, name, out_port, carrier="", out_port_connect=None, ros2_kwargs=None, **kwargs):
        ROS2Middleware.activate(**ros2_kwargs or {})
        Server.__init__(self, name, out_port, carrier=carrier, out_port_connect=out_port_connect, **kwargs)
        Node.__init__(self, name + str(hex(id(self))))

    def close(self):

        if hasattr(self, "_server") and self._server:
            if self._server is not None:
                self.destroy_node()
        if hasattr(self, "_background_callback") and self._background_callback:
            if self._background_callback is not None:
                self._background_callback.join()

    def __del__(self):
        self.close()


@Servers.register("NativeObject", "ros2")
class ROS2NativeObjectServer(ROS2Server):
    SEND_QUEUE = queue.Queue(maxsize=1)
    RECEIVE_QUEUE = queue.Queue(maxsize=1)

    def __init__(self, name, out_port, carrier="", out_port_connect=None, serializer_kwargs=None, deserializer_kwargs=None, **kwargs):
        super().__init__(name, out_port, carrier=carrier, out_port_connect=out_port_connect, **kwargs)

        self._plugin_encoder = JsonEncoder
        self._plugin_kwargs = kwargs
        self._serializer_kwargs = serializer_kwargs or {}
        self._plugin_decoder_hook = JsonDecodeHook(**kwargs).object_hook
        self._deserializer_kwargs = deserializer_kwargs or {}

        self._server = None

    def establish(self):
        try:
            from yaw_ros2_interfaces.srv import ROS2NativeObjectService
        except ImportError:
            import yaw
            logging.error("Could not import ROS2NativeObjectService. "
                          "Make sure the ros2 services in yaw_extensions/yaw_ros2_interfaces are compiled. "
                          "Refer to the documentation for more information: \n" +
                          yaw.__url__ + "yaw_extensions/yaw_ros2_interfaces/README.md")
            sys.exit(1)

        self._server = self.create_service(ROS2NativeObjectService, self.out_port, self._service_callback)

        self._req_msg = ROS2NativeObjectService.Request()
        self._rep_msg = ROS2NativeObjectService.Response()
        self.established = True

    def await_request(self, *args, **kwargs):
        if not self.established:
            self.establish()
        try:
            self._background_callback = threading.Thread(name='ros2_server', target=rclpy.spin_once,
                                                         args=(self,), kwargs={})
            self._background_callback.setDaemon(True)
            self._background_callback.start()

            request = ROS2NativeObjectServer.RECEIVE_QUEUE.get(block=True)
            [args, kwargs] = json.loads(request.request, object_hook=self._plugin_decoder_hook, **self._deserializer_kwargs)
            return args, kwargs
        except Exception as e:
            logging.error("Service call failed %s" % e)
            return [], {}

    @staticmethod
    def _service_callback(request, _response):
       ROS2NativeObjectServer.RECEIVE_QUEUE.put(request)
       return ROS2NativeObjectServer.SEND_QUEUE.get(block=True)

    def reply(self, obj):
        try:
            obj_str = json.dumps(obj, cls=self._plugin_encoder, **self._plugin_kwargs,
                                 serializer_kwrags=self._serializer_kwargs)
            self._rep_msg.response = obj_str
            ROS2NativeObjectServer.SEND_QUEUE.put(self._rep_msg, block=False)
        except queue.Full:
            logging.warning(f"Discarding data because queue is full. "
                            f"This happened due to bad synchronization in {self.__name__}")
