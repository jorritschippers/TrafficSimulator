# Traffic Simulator Controller

# Imports
import asyncio
import websockets
import json

# Global data and values
ip = ["", "84.86.123.188", "82.197.211.219", "31.201.228.97", "147.12.9.237", "94.214.255.27"]
json_data = []
msg_id = 0

# Creates a websocketconnection and executes other functions
async def startClient():
    global ip
    uri = "ws://" + ip[2] + ":6969"
    async with websockets.connect(uri) as websocket:
        await initialization(websocket)
        while True:
            global json_data
            commands = changeDataValues(json_data)
            if len(commands) > 0:
                await notifyTrafficLightChange(websocket, commands)

            await notifySensorChange(websocket)

# Receives initialization from server
async def initialization(websocket):
    received = await websocket.recv()

    global msg_id
    msg_id = json.loads(received)["msg_id"]

    if json.loads(received)["msg_type"] == "initialization":
        global json_data
        json_data = json.loads(received)["data"]

        for i, value in enumerate(json_data):        
            json_data[i]["state"] = "red"
            json_data[i]["vehicles_waiting"] = False
            json_data[i]["vehicles_coming"] = False
            json_data[i]["emergency_vehicle"] = False

        print(f"> Received (initialization): {json_data}")

# Receives notify_sensor_change from server
async def notifySensorChange(websocket):
    received = await websocket.recv()

    global msg_id
    msg_id = json.loads(received)["msg_id"]

    json_data = json.loads(received)["data"]
    if json.loads(received)["msg_type"] == "notify_sensor_change":
        #change values of data in loop
        print(f"> Received (notify_sensor_change): {json_data}")

# Changes data values of data and returns changes to send to the server
def changeDataValues(data):
    commands = []
    crosses = []
    for i, path in enumerate(data):
        if path["state"] == "red" and (path["vehicles_waiting"] > 0 or path["vehicles_coming"] > 0):
            if not data[i]["crosses"] in crosses:
                data[i]["state"] = "green"
                commands.append({"id": data[i]["id"], "state": "green" })
                for cross in data[i]["crosses"]:
                    crosses.append(cross)
        elif path["state"] == "green" and (path["vehicles_waiting"] == 0 and path["vehicles_coming"] == 0):
            data[i]["state"] = "red"
            commands.append({"id": data[i]["id"], "state": "red" })
        #add elif for orange, dont forget the timing
    global json_data
    json_data = data
    return commands

# Sends notify_traffic_light_change message to server
async def notifyTrafficLightChange(websocket, data):
    global msg_id
    msg_id = json.loads(received)["msg_id"] += 1
    send = json.dumps({ "msg_id": msg_id, "msg_type": "notify_traffic_light_change", "data": data })
    await websocket.send(send)
    print(f"> Send (notify_traffic_light_change): {send}")

# Runs startClient function until complete
asyncio.get_event_loop().run_until_complete(startClient())