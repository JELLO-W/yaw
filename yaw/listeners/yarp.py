import logging
import json
import time
from typing import Optional, Literal
import io
import base64

import numpy as np
import cv2
import yarp

from yaw.connect.listeners import Listener, ListenerWatchDog, Listeners
from yaw.middlewares.yarp import YarpMiddleware
from yaw.encoders import JsonDecodeHook


WATCHDOG_POLL_REPEAT = None


class YarpListener(Listener):

    def __init__(self, name: str, in_port: str, carrier: Literal["tcp", "udp", "mcast"] = "tcp", should_wait: bool = True,
                 persistent: bool = True, yarp_kwargs: Optional[dict] = None, **kwargs):
        """
        Initialize the subscriber

        :param name: str: Name of the publisher
        :param in_port: str: Name of the output topic preceded by '/' (e.g. '/topic')
        :param carrier: str: Carrier protocol (e.g. 'tcp'). Default is 'tcp'
        :param should_wait: bool: Whether the subscriber should wait for the publisher to transmit a message. Default is True
        :param persistent: bool: Whether the subscriber port should remain connected after closure. Default is True
        :param yarp_kwargs: dict: Additional kwargs for  the Yarp middleware
        :param kwargs: dict: Additional kwargs for the subscriber
        """
        super().__init__(name, in_port, carrier=carrier, should_wait=should_wait, **kwargs)

        self.style = yarp.ContactStyle()
        self.style.persistent = persistent
        self.style.carrier = self.carrier

        YarpMiddleware.activate(**yarp_kwargs or {})

    def await_connection(self, in_port: Optional[str] = None, repeats: Optional[int] = None):
        """
        Wait for the publisher to connect to the subscriber

        :param in_port: str: Name of the input topic preceded by '/' (e.g. '/topic')
        :param repeats: int: Number of times to check for the parameter. None for infinite. Default is None
        :return: bool: True if connection established, False otherwise
        """
        connected = False
        if in_port is None:
            in_port = self.in_port
        logging.info(f"Waiting for input port: {in_port}")
        if repeats is None:
            if self.should_wait:
                repeats = -1
            else:
                repeats = 1

            while repeats > 0 or repeats <= -1:
                repeats -= 1
                connected = yarp.Network.exists(in_port)
                if connected:
                    logging.info(f"Connected to input port: {in_port}")
                    break
                time.sleep(0.2)
        return connected

    def read_port(self, port):
        """
        Read the port

        :param port: yarp.Port: Port to read from
        :return: yarp.Value: Value read from the port
        """
        while True:
            obj = port.read(shouldWait=False)
            if self.should_wait and obj is None:
                time.sleep(0.005)
            else:
                return obj

    def close(self):
        """
        Close the subscriber
        """
        if hasattr(self, "_port") and self._port:
            if self._port is not None:
                self._port.close()

    def __del__(self):
        self.close()


@Listeners.register("NativeObject", "yarp")
class YarpNativeObjectListener(YarpListener):

    def __init__(self, name: str, in_port: str, carrier: Literal["tcp", "udp", "mcast"] = "tcp", should_wait: bool = True,
                 persistent: bool = True, deserializer_kwargs: Optional[dict] = None, **kwargs):
        """
        The NativeObject listener using the BufferedPortBottle string construct assuming the data is serialized as a JSON string.
        Deserializes the data (including plugins) using the decoder and parses it to a Python object

        :param name: str: Name of the subscriber
        :param in_port: str: Name of the input topic preceded by '/' (e.g. '/topic')
        :param carrier: str: Carrier protocol (e.g. 'tcp'). Default is 'tcp'
        :param should_wait: bool: Whether the subscriber should wait for the publisher to transmit a message. Default is True
        :param persistent: bool: Whether the subscriber port should remain connected after closure. Default is True
        :param deserializer_kwargs: dict: Additional kwargs for the deserializer
        """
        super().__init__(name, in_port, carrier=carrier, should_wait=should_wait, persistent=True, **kwargs)

        self._port = self._netconnect = None

        self._plugin_decoder_hook = JsonDecodeHook(**kwargs).object_hook
        self._deserializer_kwargs = deserializer_kwargs or {}

        if not self.should_wait:
            ListenerWatchDog().add_listener(self)

    def establish(self, repeats: Optional[int] = None, **kwargs):
        """
        Establish the connection to the publisher

        :param repeats: int: Number of repeats to await connection. None for infinite. Default is None
        :return: bool: True if connection established, False otherwise
        """
        established = self.await_connection(repeats=repeats)
        if established:
            self._port = yarp.BufferedPortBottle()
            rnd_id = str(np.random.randint(100000, size=1)[0])
            self._port.open(self.in_port + ":in" + rnd_id)
            if self.style.persistent:
                self._netconnect = yarp.Network.connect(self.in_port, self.in_port + ":in" + rnd_id, self.style)
            else:
                self._netconnect = yarp.Network.connect(self.in_port, self.in_port + ":in" + rnd_id, self.carrier)
        return self.check_establishment(established)

    def listen(self):
        """
        Listen for a message

        :return: Any: The received message as a native python object
        """
        if not self.established:
            established = self.establish(repeats=WATCHDOG_POLL_REPEAT)
            if not established:
                return None
        obj_port = self.read_port(self._port)
        if obj_port is not None:
            return json.loads(obj_port.get(0).asString(), object_hook=self._plugin_decoder_hook, **self._deserializer_kwargs)
        else:
            return None


@Listeners.register("Image", "yarp")
class YarpImageListener(YarpListener):

    def __init__(self, name: str, in_port: str, carrier: Literal["tcp", "udp", "mcast"] = "tcp", should_wait: bool = True,
                 persistent: bool = True, width: int = -1, height: int = -1, rgb: bool = True, fp: bool = False, jpg: bool = False, **kwargs):
        """
        The Image listener using the BufferedPortImage construct parsed to a numpy array

        :param name: str: Name of the subscriber
        :param in_port: str: Name of the input topic preceded by '/' (e.g. '/topic')
        :param carrier: str: Carrier protocol (e.g. 'tcp'). Default is 'tcp'
        :param should_wait: bool: Whether the subscriber should wait for the publisher to transmit a message. Default is True
        :param persistent: bool: Whether the subscriber port should remain connected after closure. Default is True
        :param width: int: Width of the image. Default is -1 (use the width of the received image)
        :param height: int: Height of the image. Default is -1 (use the height of the received image)
        :param rgb: bool: True if the image is RGB, False if it is grayscale. Default is True
        :param fp: bool: True if the image is floating point, False if it is integer. Default is False
        :param jpg: bool: True if the image should be decompressed from JPG. Default is False
        """
        super().__init__(name, in_port, carrier=carrier, should_wait=should_wait, persistent=persistent, **kwargs)

        self.width = width
        self.height = height
        self.rgb = rgb
        self.fp = fp
        self.jpg = jpg

        self._port = self._type = self._netconnect = None

        if not self.should_wait:
            ListenerWatchDog().add_listener(self)

    def establish(self, repeats: Optional[int] = None, **kwargs):
        """
        Establish the connection to the publisher

        :param repeats: int: Number of repeats to await connection. None for infinite. Default is None
        :return: bool: True if connection established, False otherwise
        """
        established = self.await_connection(repeats=repeats)
        if established:
            if self.jpg:
                self._port = yarp.BufferedPortBottle()
            elif self.rgb:
                self._port = yarp.BufferedPortImageRgbFloat() if self.fp else yarp.BufferedPortImageRgb()
            else:
                self._port = yarp.BufferedPortImageFloat() if self.fp else yarp.BufferedPortImageMono()
            self._type = np.float32 if self.fp else np.uint8
            in_port_connect = f"{self.in_port}:in{np.random.randint(100000, size=1).item()}"
            self._port.open(in_port_connect)
            if self.style.persistent:
                self._netconnect = yarp.Network.connect(self.in_port, in_port_connect, self.style)
            else:
                self._netconnect = yarp.Network.connect(self.in_port, in_port_connect, self.carrier)
        return self.check_establishment(established)

    def listen(self):
        """
        Listen for a message

        :return: np.ndarray: The received message as a numpy array formatted as a cv2 image np.ndarray[img_height, img_width, channels]
        """
        if not self.established:
            established = self.establish(repeats=WATCHDOG_POLL_REPEAT)
            if not established:
                return None
        ret_img_msg = self.read_port(self._port)
        if ret_img_msg is None:
            return None
        if self.jpg:
            img_str = ret_img_msg.get(0).asString()
            with io.BytesIO(base64.b64decode(img_str.encode('ascii'))) as memfile:
                img_str = np.load(memfile)
            if self.rgb:
                img = cv2.imdecode(np.frombuffer(img_str, np.uint8), cv2.IMREAD_COLOR)
            else:
                img = cv2.imdecode(np.frombuffer(img_str, np.uint8), cv2.IMREAD_GRAYSCALE)
            return img
        else:
            if 0 < self.width != ret_img_msg.width() or 0 < self.height != ret_img_msg.height():
                raise ValueError("Incorrect image shape for listener")
            elif self.rgb:
                img = np.zeros((ret_img_msg.height(), ret_img_msg.width(), 3), dtype=self._type, order='C')
                img_port = yarp.ImageRgbFloat() if self.fp else yarp.ImageRgb()
            else:
                img = np.zeros((ret_img_msg.height(), ret_img_msg.width()), dtype=self._type, order='C')
                img_port = yarp.ImageFloat() if self.fp else yarp.ImageMono()
            img_port.resize(img.shape[1], img.shape[0])
            img_port.setExternal(img.data, img.shape[1], img.shape[0])
            img_port.copy(ret_img_msg)
            return img


@Listeners.register("AudioChunk", "yarp")
class YarpAudioChunkListener(YarpImageListener):

    def __init__(self, name: str, in_port: str, carrier: Literal["tcp", "udp", "mcast"] = "tcp", should_wait: bool = True,
                 persistent: bool = True, channels: int = 1, rate: int = 44100, chunk: int = -1, **kwargs):
        """
        The AudioChunk listener using the BufferedPortImage construct parsed as a numpy array

        :param name: str: Name of the subscriber
        :param in_port: str: Name of the input topic preceded by '/' (e.g. '/topic')
        :param carrier: str: Carrier protocol (e.g. 'tcp'). Default is 'tcp'
        :param should_wait: bool: Whether the subscriber should wait for the publisher to transmit a message. Default is True
        :param persistent: bool: Whether the subscriber port should remain connected after closure. Default is True
        :param channels: int: Number of channels in the audio. Default is 1
        :param rate: int: Sampling rate of the audio. Default is 44100
        :param chunk: int: Number of samples in the audio chunk. Default is -1 (use the chunk size of the received audio)
        """
        super().__init__(name, in_port, carrier=carrier, should_wait=should_wait, persistent=persistent,
                         width=chunk, height=channels, rgb=False, fp=True, jpg=False, **kwargs)

        self.channels = channels
        self.rate = rate
        self.chunk = chunk

        self._dummy_sound = self._dummy_port = self._dummy_netconnect = None

        if not self.should_wait:
            ListenerWatchDog().add_listener(self)

    def establish(self, repeats: Optional[int] = None, **kwargs):
        """
        Establish the connection to the publisher

        :param repeats: int: Number of repeats to await connection. None for infinite. Default is None
        :return: bool: True if connection established, False otherwise
        """
        established = self.await_connection(in_port=self.in_port + "_SND", repeats=repeats)
        if established:
            # create a dummy sound object for transmitting the sound props. This could be cleaner but left for future impl.
            rnd_id = str(np.random.randint(100000, size=1)[0])
            self._dummy_port = yarp.Port()
            self._dummy_port.open(self.in_port + "_SND:in" + rnd_id)
            self._dummy_netconnect = yarp.Network.connect(self.in_port + "_SND", self.in_port + "_SND:in" + rnd_id, self.carrier)
        established = self.check_establishment(established)
        established_parent = super(YarpAudioChunkListener, self).establish(repeats=repeats)
        if established_parent:
            self._dummy_sound = yarp.Sound()
            # self._dummy_port.read(self._dummy_sound)
            # self.rate = self._dummy_sound.getFrequency()
            # self.width = self.chunk = self._dummy_sound.getSamples()
            # self.height = self.channels = self._dummy_sound.getChannels()
        return established

    def listen(self):
        """
        Listen for a message

        :return: (np.ndarray, int): The received message as a numpy array formatted as (np.ndarray[audio_chunk, channels], int[samplerate])
        """
        return super().listen(), self.rate

    def close(self):
        """
        Close the subscriber connection to the yarp Sound port. This is not used at the moment, but left for future impl.
        """
        super().close()
        if self._dummy_port:
            self._dummy_port.close()


@Listeners.register("Properties", "yarp")
class YarpPropertiesListener(YarpListener):
    def __init__(self, name, in_port, **kwargs):
        super().__init__(name, in_port, **kwargs)
        raise NotImplementedError
