"""
API Module for Data Collection

This module contains functions for setting up and running the API for the data collector.
"""

from p1_software_solo405.data_collection.api.routes import APIRoutes
from p1_software_solo405.data_collection.api.server import APIServer

__all__ = ['APIRoutes', 'APIServer']
