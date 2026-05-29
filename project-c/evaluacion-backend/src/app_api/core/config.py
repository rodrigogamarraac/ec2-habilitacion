import os

REDIS_HOST = os.getenv('REDIS_HOST', '127.0.0.1')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379 ))

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))