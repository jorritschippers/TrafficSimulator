#!/usr/bin/env python

# WS client example

import asyncio
import websockets
import json

data = []

async def init():
    uri = "ws://82.197.211.219:9002"
    async with websockets.connect(uri) as websocket:
        await websocket.send("Groep 2 aanwezig!")
        received = await websocket.recv()
        global data
        data = json.dumps(received)
        print(f"> start command")

async def changeState(id, state):
    uri = "ws://82.197.211.219:9002"
    async with websockets.connect(uri) as websocket:
        #data = { "msg_type": "change_state", "data": [{"id": id, "state": state}] }
        send = { "id": id, "state": state }
        await websocket.send(json.dumps(send))
        received = await websocket.recv()
        global data
        data = json.dumps(received)
        print(f"> send change_state command")

async def printData():
    print(f"> {data}")

asyncio.get_event_loop().run_until_complete(init())
asyncio.get_event_loop().run_until_complete(printData())
#asyncio.get_event_loop().run_until_complete(changeState(1, "green"))
#asyncio.get_event_loop().run_until_complete(printData())
