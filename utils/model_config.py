# utils/model_config.py
"""
Compatibility shim.
Old code may still do:  from utils.model_config import MODEL_CODER
This file simply forwards everything to the new location.
"""
from config.model_config import *      # re-export every public symbol
