import os

HOST = os.getenv('MILVUS_URL', 'localhost')
PORT = os.getenv('MILVUS_PORT', '19530')