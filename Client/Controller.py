# Traffic Simulator Controller

# Imports
import asyncio
import websockets
import json
import time

# Global data and values
ip = ["84.86.123.188", "82.197.211.219", "31.201.228.97", "147.12.9.237", "94.214.255.27"]
json_data = []
msg_id = 0
current_clearing_time = 0.0
saved_time = 0

# Creates a websocketconnection and executes other functions
async def startClient():
    global ip
    uri = "ws://" + ip[1] + ":6969"
    try:
        async with websockets.connect(uri) as websocket:
            print(f"> Controller made connection with server")
            await initialization(websocket)

            while True:
                global json_data, current_clearing_time, saved_time
                if (time.time() - saved_time) >= current_clearing_time and current_clearing_time > 0 and saved_time > 0:
                    commands = changeDataValues(json_data)
                    current_clearing_time = 0
                    if len(commands) > 0:
                        await notifyTrafficLightChange(websocket, commands)
                elif current_clearing_time == 0 or saved_time == 0:
                    commands = changeDataValues(json_data)
                    if len(commands) > 0:
                        await notifyTrafficLightChange(websocket, commands)

                await notifySensorChange(websocket)
    except Exception as e:
        print(f"> An error occured ({e})")

# Receives initialization from server
async def initialization(websocket):
    received = await websocket.recv()
    print(f"> Received (initialization): {received}")

    global msg_id
    msg_id = json.loads(received)["msg_id"]

    if json.loads(received)["msg_type"] == "initialization":
        global json_data
        json_data = json.loads(received)["data"]

        for i, value in enumerate(json_data):        
            json_data[i]["state"] = "red"
            json_data[i]["vehicles_waiting"] = False
            json_data[i]["vehicles_coming"] = False
            json_data[i]["vehicles_blocking"] = False
            json_data[i]["emergency_vehicle"] = False
            json_data[i]["public_transport"] = False

    print(f"> Saved initialization data")              

# Receives notify_sensor_change from server
async def notifySensorChange(websocket):
    received = await websocket.recv()
    print(f"> Received (notify_sensor_change): {received}")

    global msg_id
    msg_id = json.loads(received)["msg_id"]

    data = json.loads(received)["data"]
    if json.loads(received)["msg_type"] == "notify_sensor_change":
        global json_data
        for i, currentValue in enumerate(json_data):
            for sensorValue in data:
                if currentValue["id"] == sensorValue["id"]:
                    json_data[i]["vehicles_waiting"] = valueToBool(sensorValue["vehicles_waiting"])
                    json_data[i]["vehicles_coming"] = valueToBool(sensorValue["vehicles_coming"])
                    json_data[i]["vehicles_blocking"] = valueToBool(sensorValue["vehicles_blocking"])
                    json_data[i]["emergency_vehicle"] = valueToBool(sensorValue["emergency_vehicle"])
                    json_data[i]["public_transport"] = valueToBool(sensorValue["public_transport"])

    print(f"> Processed notify_sensor_change")      

# Changes input to boolean
def valueToBool(v):
    return str(v).lower() in ("True", "true", "1")

# Changes data values of data and returns changes to send to the server
def changeDataValues(data):
    commands = []
    crosses = []
    max_clearing_time = 0.0

    for i, path in enumerate(data):
        if path["emergency_vehicle"] or path["public_transport"] or path["vehicles_blocking"]:
            proceed = True
            for cross in crosses:
                if data[i]["id"] == cross:
                    proceed = False

            if proceed:
                data[i]["state"] = "green"
                data[i]["vehicles_blocking"] = False
                data[i]["emergency_vehicle"] = False
                data[i]["public_transport"] = False
                commands.append({"id": data[i]["id"], "state": data[i]["state"] })
                for cross in data[i]["crosses"]:
                    crosses.append(cross)

                if data[i]["clearing_time"] > max_clearing_time:
                    max_clearing_time = data[i]["clearing_time"]

    for i, path in enumerate(data):
        if path["state"] == "green":
            if not path["vehicles_waiting"] or not path["vehicles_coming"]:
                data[i]["state"] = "orange"
                commands.append({"id": data[i]["id"], "state": data[i]["state"] })
                for cross in data[i]["crosses"]:
                    crosses.append(cross)
                if data[i]["clearing_time"] > max_clearing_time:
                    max_clearing_time = data[i]["clearing_time"]
        elif path["state"] == "orange":
            if not path["vehicles_waiting"] or not path["vehicles_coming"]:
                data[i]["state"] = "red"
                commands.append({"id": data[i]["id"], "state": data[i]["state"] })
                if data[i]["clearing_time"] > max_clearing_time:
                    max_clearing_time = data[i]["clearing_time"]
        elif path["state"] == "red":
            if path["vehicles_waiting"] or path["vehicles_coming"]:
                proceed = True
                for cross in crosses:
                    if data[i]["id"] == cross:
                        proceed = False

                if proceed:
                    data[i]["state"] = "green"
                    data[i]["vehicles_waiting"] = False
                    data[i]["vehicles_coming"] = False
                    data[i]["emergency_vehicle"] = False
                    commands.append({"id": data[i]["id"], "state": data[i]["state"] })
                    for cross in data[i]["crosses"]:
                        crosses.append(cross)

                    if data[i]["clearing_time"] > max_clearing_time:
                        max_clearing_time = data[i]["clearing_time"]

    print(f"> Evaluated current data (execute: {len(commands)})")      

    global json_data, current_clearing_time, saved_time
    json_data = data
    current_clearing_time = max_clearing_time
    saved_time = time.time()
    return commands

# Sends notify_traffic_light_change message to server
async def notifyTrafficLightChange(websocket, data):
    global msg_id
    msg_id = msg_id + 1

    command = json.dumps({ "msg_id": msg_id, "msg_type": "notify_traffic_light_change", "data": data })
    await websocket.send(command)

    print(f"> Send (notify_traffic_light_change): {command}")

# Runs startClient function until complete
asyncio.get_event_loop().run_until_complete(startClient())