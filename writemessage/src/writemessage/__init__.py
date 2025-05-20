
import importlib.metadata 
import logging
import postgresql_access

from postgresql_access import DatabaseConfig
__version__ =  importlib.metadata.version('writemessage')

writemessage_logger = logging.getLogger(__name__)

def database_from_config(config)->postgresql_access.AbstractDatabase:
    return DatabaseConfig(config=config )

