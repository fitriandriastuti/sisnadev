from os import environ
from dotenv import load_dotenv
load_dotenv()

import asyncio
import motor.core
import certifi

from motor.motor_asyncio import (
    AsyncIOMotorClient as MotorClient,
)

DEBUG = environ['DEBUG']

global SessionLocal, Session, Close

if DEBUG == '1':
    DATABASE_URL = "mongodb://localhost:27017/bedahdataapbd" #database docker
    client = MotorClient(DATABASE_URL)
    SessionLocal = client.bedahdataapbd
    Session = client.bedahdataapbd
    Close = client.close()
elif DEBUG == '2':
    DATABASE_URL = environ['DATABASE_URL']
    client = MotorClient(DATABASE_URL, tlsCAFile=certifi.where())
    SessionLocal = client.sisna
    Session = client.sisna
    Close = client.close()
else:
    DATABASE_URL = environ['DATABASE_URL']
    client = MotorClient(DATABASE_URL)
    SessionLocal = client.sisna
    Session = client.sisna
    Close = client.close()

client.get_io_loop = asyncio.get_running_loop

db = client.get_default_database()










