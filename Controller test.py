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
    try:
        async with websockets.connect(uri) as websocket:
            await notifyStateChange(websocket)
            while True:
                global json_data
                send = changeDataValues(json_data)
                if len(send) > 0:
                    await performStateChange(websocket, send)

                await notifySucces(websocket)
    except Exception:
        print(f"> Server was stopped by error")

# Receives current_state from server
async def notifyStateChange(websocket):
    received = await websocket.recv()
    global json_data
    json_data = json.loads(received)["data"]
    print(f"> Received (notify_state_change): {received}")

# Receives succes from server
async def notifySucces(websocket):
    received = await websocket.recv()
    print(f"> Received (end_notification): {received}")

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
async def performStateChange(websocket, data):
    send = json.dumps({ "msg_type": "perform_state_change", "data": data })
    await websocket.send(send)
    print(f"> Send (perform_state_change): {send}")

# Runs startClient function until complete
asyncio.get_event_loop().run_until_complete(startClient())