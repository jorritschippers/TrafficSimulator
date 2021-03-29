# Traffic Simulator Controller

import asyncio
import websockets
import json
import time
data = []
sendData = True
i = 0

async def startClient():
    uri = "ws://82.197.211.219:9002"
    async with websockets.connect(uri) as websocket:
        while True:
            await executeInLoop(websocket)
            await changeState(websocket, 1, "green")
            time.sleep(3)

async def executeInLoop(websocket):
    global sendData
    global i
    if sendData == True:
        await websocket.send("Execute in loop {i}")
        print(f"> Send")
        received = await websocket.recv()
        global data
        data = json.dumps(received)
        print(f"> {data}")
        i = i + 1

    if i < 3:
        await executeInLoop(websocket)

async def changeState(websocket, id, state):
    send = { "msg_type": "change_state", "data": [{"id": id, "state": state}] }
    await websocket.send(json.dumps(send))
    print(f"> Send: {send}")
    received = await websocket.recv()
    global data
    data = json.dumps(received)
    print(f"> Received: {data}")

asyncio.get_event_loop().run_until_complete(startClient())