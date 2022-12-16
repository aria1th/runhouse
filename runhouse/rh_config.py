# Following design pattern for singleton variables from here:
# https://docs.python.org/3/faq/programming.html#how-do-i-share-global-variables-across-modules
import logging.config

from runhouse.logger import LOGGING_CONFIG
from runhouse.rns.rns_client import RNSClient
from runhouse.rns.defaults import Defaults

# Configure the logger once
# TODO commenting out for now because this duplicates the logging config in the root logger
# logging.config.dictConfig(LOGGING_CONFIG)

logger = logging.getLogger(__name__)

configs = Defaults()

open_grpc_tunnels = {}

rns_client = RNSClient(configs=configs)

# To allow pinning objects to memory inside a send, e.g. to save time sending to cuda over and over
global_pinned_memory_store = None

