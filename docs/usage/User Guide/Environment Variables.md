## Environment Variables

YAW reserves specific environment variable names for the functionality of its internal components:

* `YAW_PLUGINS_PATH`: Path/s to [plugin](<Plugins.md#plugins>) extension directories 
* `YAW_DEFAULT_COMMUNICATOR` or `YAW_DEFAULT_MWARE` (`YAW_DEFAULT_MWARE` overrides `YAW_DEFAULT_COMMUNICATOR` when both are provided): Name of default [<Communicator>](<../User Guide.md#usage>) when non is provided as the second argument to the YAW decorator. 

ZeroMQ requires socket configurations that can be passed as arguments to the respective middleware constructor (through the YAW decorator) or using environment variables. Note that these configurations are needed both by the proxy and the message publisher and listener. 
The downside to such an approach is that all messages share the same configs. Since the proxy broker spawns once on first trigger (if enabled) as well as a singleton subscriber monitoring instance, using environment variables is the recommended approach to avoid unintended behavior. 
This can be achieved by setting:
        
* `YAW_ZEROMQ_SOCKET_IP`: IP address of the socket. Defaults to "127.0.0.1"
* `YAW_ZEROMQ_SOCKET_PUB_PORT`: The publishing socket port. Defaults to 5555
* `YAW_ZEROMQ_SOCKET_SUB_PORT`: The sub-socket port (listening port for the broker). Defaults to 5556
* `YAW_ZEROMQ_PUBSUB_MONITOR_TOPIC`: The topic name for the pub-sub monitor. Defaults to "ZEROMQ/CONNECTIONS"
* `YAW_ZEROMQ_PUBSUB_MONITOR_LISTENER_SPAWN`: Either spawn the pub-sub monitor listener as a "process" or "thread". Defaults to "process"
* `YAW_ZEROMQ_START_PROXY_BROKER`: Spawn a new broker proxy without running the [standalone proxy broker](../../../yaw/standalone/zeromq_proxy_broker.py). Defaults to "True"
* `YAW_ZEROMQ_PROXY_BROKER_SPAWN`: Either spawn broker as a "process" or "thread". Defaults to "process")
* `YAW_ZEROMQ_PARAM_POLL_INTERVAL`: Polling interval in milliseconds for the parameter server. Defaults to 1 (**currently not supported**)
* `YAW_ZEROMQ_PARAM_REQREP_PORT`: The parameter server request-reply port. Defaults to 5659 (**currently not supported**)
* `YAW_ZEROMQ_PARAM_PUB_PORT`: The parameter server pub-socket port. Defaults to 5655 (**currently not supported**)
* `YAW_ZEROMQ_PARAM_SUB_PORT`: The parameter server sub-socket port. Defaults to 5656 (**currently not supported**)

ROS and ROS2 queue sizes can be set by:

* `YAW_ROS_QUEUE_SIZE`: Size of the queue buffer. Defaults to 5
* `YAW_ROS2_QUEUE_SIZE`: Size of the queue buffer. Defaults to 5
