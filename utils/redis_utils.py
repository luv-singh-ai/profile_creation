from dotenv import load_dotenv
import redis
import os

load_dotenv(
    dotenv_path="ops/.env"
)

REDIS_HOST = os.getenv("REDIS_HOST")
# Connect to the Redis server
redis_client = redis.Redis(host=REDIS_HOST, port=6379, db=0) # password=None

def get_redis_value(key):
    '''
    Redis stores everything as a byte string (bytes in Python).
    To convert the byte string back to a regular string, you need to decode it using the decode('utf-8') method.
    '''
    # value = redis_client.get(key)
    # if value is not None:
    #     return value.decode('utf-8')
    return redis_client.get(key)

def set_redis(key, value, expire=600):
    # Setting key-value pairs with an expiry time of 10 minutes

    redis_client.set(key, value, ex=expire)
    # Expiration: Set a key with an expiration time (in seconds)
    # redis_client.setex('temporary_key', 10, 'This will expire in 10 seconds')

def delete_redis(key):
    redis_client.delete(key)
    
'''
REDIS CAN SAVE Data Structures LIKE Lists, Sets, Hashes
# List example
redis_client.lpush('mylist', 'element1')
redis_client.lpush('mylist', 'element2')
redis_client.lpush('mylist', 'element3')

# Retrieve the list elements
mylist = redis_client.lrange('mylist', 0, -1)
mylist = [element.decode('utf-8') for element in mylist]
print(f'My List: {mylist}')

# Set example
redis_client.sadd('myset', 'member1')
redis_client.sadd('myset', 'member2')
redis_client.sadd('myset', 'member3')

# Retrieve the set members
myset = redis_client.smembers('myset')
myset = {member.decode('utf-8') for member in myset}
print(f'My Set: {myset}')

# Hash example
redis_client.hset('myhash', 'field1', 'value1')
redis_client.hset('myhash', 'field2', 'value2')

# Retrieve the hash fields
myhash = redis_client.hgetall('myhash')
myhash = {field.decode('utf-8'): value.decode('utf-8') for field, value in myhash.items()}
print(f'My Hash: {myhash}')

# 5. Persistence
# Save the current state of Redis to disk (only works if persistence is enabled in the config)
redis_client.save()
'''