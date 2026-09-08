"""Runtime hook to initialize connection pool early in PyInstaller bundle."""
# This runs before the main script starts
from database.connection import init_connection_pool

# Initialize pool with 3 connections
init_connection_pool(3)