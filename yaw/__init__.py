__version__ = "0.4.13"
__url__ = "https://github.com/JELLO-W/yaw/"
name = "yaw"

try:
    from importlib import metadata
    __version__ = metadata.version(__name__)
    __url__ = metadata.metadata(__name__)["Home-page"]
except ImportError:
    try:
        import pkg_resources
        __version__ = pkg_resources.require(name)[0].version
    except pkg_resources.DistributionNotFound:
        pass
except Exception:
    pass

from yaw.utils import PluginRegistrar

PluginRegistrar.scan()

import logging
logging.getLogger().setLevel(logging.INFO)