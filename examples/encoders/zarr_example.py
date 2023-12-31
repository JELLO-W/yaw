"""
A message publisher and listener for native Python objects and Zarr arrays/groups.

This script demonstrates the capability to transmit native Python objects and Zarr arrays/groups using
the MiddlewareCommunicator within the YAW library. The communication follows the PUB/SUB pattern
allowing message publishing and listening functionalities between processes or machines.

Demonstrations:
    - Using the NativeObject message
    - Transmitting a nested dummy Python object with native objects and Zarr arrays/groups
    - Applying the PUB/SUB pattern with mirroring

Requirements:
    - YAW: Middleware communication wrapper (refer to the YAW documentation for installation instructions)
    - YARP, ROS, ROS2, ZeroMQ (refer to the YAW documentation for installation instructions)
    - NumPy: Used for creating arrays (installed with YAW)
    - zarr: Used for creating and handling Zarr arrays and groups

    Install using pip:
        ``pip install zarr``

Run:
    # On machine 1 (or process 1): Publisher waits for keyboard input and transmits message
        ``python3 zarr_example.py --mode publish``

    # On machine 2 (or process 2): Listener waits for message and prints the entire dummy object
        ``python3 zarr_example.py --mode listen``
"""

import argparse

import zarr
import numpy as np

from yaw.connect.wrapper import MiddlewareCommunicator, DEFAULT_COMMUNICATOR


class Notifier(MiddlewareCommunicator):
    @MiddlewareCommunicator.register(
        "NativeObject", "$mware", "Notifier", "/notify/test_zarr_exchange",
        carrier="tcp", should_wait=True
    )
    def exchange_object(self, mware=None):
        """Exchange messages with Zarr arrays/groups and other native Python objects."""
        msg = input("Type your message: ")

        # Creating an example Zarr Array
        zarray = zarr.array(np.random.random((10, 10)), chunks=(5, 5))

        # Creating an example Zarr Group
        zgroup = zarr.group()
        zgroup.create_dataset('dataset1', data=np.random.randint(0, 100, 50), chunks=10)
        zgroup.create_dataset('dataset2', data=np.random.random(100), chunks=10)

        ret = {
            "message": msg,
            "zarr_array": zarray,
            "zarr_group": zgroup,
        }
        return ret,


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="A message publisher and listener for native Python objects and Zarr arrays/groups.")
    parser.add_argument(
        "--mode", type=str, default="publish",
        choices={"publish", "listen"},
        help="The transmission mode"
    )
    parser.add_argument(
        "--mware", type=str, default=DEFAULT_COMMUNICATOR,
        choices=MiddlewareCommunicator.get_communicators(),
        help="The middleware to use for transmission"
    )
    return parser.parse_args()


def main(args):
    """Main function to initiate Notifier class and communication."""
    notifier = Notifier()
    notifier.activate_communication(Notifier.exchange_object, mode=args.mode)

    while True:
        msg_object, = notifier.exchange_object(mware=args.mware)
        print("Method result:", msg_object)


if __name__ == "__main__":
    args = parse_args()
    main(args)
