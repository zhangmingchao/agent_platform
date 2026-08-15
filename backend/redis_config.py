import atexit
import logging

import redis

from .config import REDIS_HOST, REDIS_PORT, REDIS_DB

pool = redis.ConnectionPool(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=REDIS_DB,
    max_connections=20,
    decode_responses=True
)

r = redis.Redis(connection_pool=pool)

def set_str(key:str,value:str,ex:int):
    r.set(key,value,ex)

def get_str(key:str) -> str:
    return r.get(key)

def del_key(key:str):
    r.delete(key)



# 程序退出时主动断开所有空闲连接（可选，非必须）
@atexit.register
def cleanup():
    logging.info("cleanup redis")
    pool.disconnect()