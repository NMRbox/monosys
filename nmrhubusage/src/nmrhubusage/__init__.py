
import importlib.metadata 
import logging
nmrhubusage_logger = logging.getLogger(__name__)

__version__ =  importlib.metadata.version('nmrhubusage')
_YAMLS = ('/nmrbox-system/etc/nmradmin.yaml', '/etc/nmrhub.d/nmradmin.yaml')
from nmrhubusage.processinfo import ProcessInfo,top_level_processes
from nmrhubusage.who import who_command