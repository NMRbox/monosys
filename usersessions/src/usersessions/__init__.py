
import importlib.metadata 
import logging
usersessions_logger = logging.getLogger(__name__)

__version__ =  importlib.metadata.version('usersessions') 
from usersessions.sessions import SessionReader

