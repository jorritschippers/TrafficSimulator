# Traffic Simulator Controller

# Imports
import asyncio
import websockets
import json

# JSON data of crosses and lights
json_data = []

# Creates a websocketconnection and executes other functions
async def startClient():
    uri = "ws://82.197.211.219:6969"
    async with websockets.connect(uri) as websocket:
        await requestState(websocket)
        # while True:z
        #     #function for receiving info from server if something happens (no msg type)

        #     global json_data
        #     send = changeDataValues(json_data)
        #     if len(send) > 0:
        #         await changeState(websocket, send)

# Sends request_state message to server and receives current_state
async def requestState(websocket):
    send = json.dumps({"x":100,"y":100})
    await websocket.send(send)
    print(f"> Send (request_state): {send}")

    # received = await websocket.recv()
    # global json_data
    # json_data = json.loads(received)["data"]
    # print(f"> Received (current_state): {received}")

# Changes data values of data and returns changes to send to the server
def changeDataValues(data):
    send = []
    for i, path in enumerate(data):
        if path["state"] == "red" and (path["vehicles_waiting"] > 0 or path["vehicles_coming"] > 0):
            data[i]["state"] = "green"
            send.append({"id": data[i]["id"], "state": "green" })
        elif path["state"] == "green" and (path["vehicles_waiting"] == 0 and path["vehicles_coming"] == 0):
            data[i]["state"] = "red"
            send.append({"id": data[i]["id"], "state": "red" })
    
    global json_data
    json_data = data
    return send

# Sends change_state message to server
async def changeState(websocket, data):
    send = json.dumps({ "msg_type": "change_state", "data": data })
    await websocket.send(send)
    print(f"> Send (change_state): {send}")

# Runs startClient function until complete
asyncio.get_event_loop().run_until_complete(startClient())