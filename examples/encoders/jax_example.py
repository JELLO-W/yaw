"""
A message publisher and listener for native Python objects and JAX arrays.

This script demonstrates the capability to transmit native Python objects and JAX arrays using
the MiddlewareCommunicator within the YAW library. The communication follows the PUB/SUB pattern
allowing message publishing and listening functionalities between processes or machines.

Demonstrations:
    - Using the NativeObject message
    - Transmitting a nested dummy Python object with native objects and JAX arrays
    - Applying the PUB/SUB pattern with mirroring

Requirements:
    - YAW: Middleware communication wrapper (refer to the YAW documentation for installation instructions)
    - YARP, ROS, ROS2, ZeroMQ (refer to the YAW documentation for installation instructions)
    - JAX: Used for handling and creating arrays (refer to https://jax.readthedocs.io/en/latest/installation.html for installation instructions)

    Install using pip:
        ``pip install jax jaxlib``  # Basic installation of JAX

Run:
    # On machine 1 (or process 1): Publisher waits for keyboard input and transmits message
        ``python3 jax_example.py --mode publish``

    # On machine 2 (or process 2): Listener waits for message and prints the entire dummy object
        ``python3 jax_example.py --mode listen``
"""

import argparse

import jax.numpy as jnp

from yaw.connect.wrapper import MiddlewareCommunicator, DEFAULT_COMMUNICATOR


class Notifier(MiddlewareCommunicator):
    @MiddlewareCommunicator.register(
        "NativeObject", "$mware", "Notifier", "/notify/test_jax_exchange",
        carrier="tcp", should_wait=True
    )
    def exchange_object(self, mware=None):
        """Exchange messages with JAX arrays and other native Python objects."""
        msg = input("Type your message: ")
        ret = {
            "message": msg,
            "jax_ones": jnp.ones((2, 4)),
        }
        return ret,


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="A message publisher and listener for native Python objects and JAX arrays.")
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
