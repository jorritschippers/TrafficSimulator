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
    i = 0
    global ip
    uri = "ws://" + ip[1] + ":6969"
    print(f"> {uri}")
    print(f"> Controller made connection with server")
    await initialization()

    while True:
        global json_data, current_clearing_time, saved_time
        if (time.time() - saved_time) >= current_clearing_time and current_clearing_time > 0 and saved_time > 0:
            commands = changeDataValues(json_data)
            current_clearing_time = 0
            # print("-------------------------------------------------------------------------------------")
            if len(commands) > 0:
                await notifyTrafficLightChange(commands)
        if current_clearing_time == 0 or saved_time == 0:
            commands = changeDataValues(json_data)
            # print("1111111111111111111111111111111111111111111111111111111111111111111111111")
            # print(saved_time)
            # print(current_clearing_time)
            if len(commands) > 0:
                await notifyTrafficLightChange(commands)

        if i == 0:
            await notifySensorChange()

        #print(f"> Test: {json_data}")
        i = i + 1

# Receives initialization from server
async def initialization():
    received = json.dumps({ "msg_id": 1, "msg_type": "initialization", "data": [{"id": 1, "crosses": [2,3], "clearing_time": 3.2}, {"id": 2, "crosses": [1,3], "clearing_time": 3.2}, {"id": 3, "crosses": [1,2], "clearing_time": 3.2}] })
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
async def notifySensorChange():
    received = json.dumps({ "msg_id": 5, "msg_type": "notify_sensor_change", "data": [{"id": 1, "vehicles_waiting": True, "vehicles_coming": False, "vehicles_blocking": False, "public_transport": False, "emergency_vehicle": False}, {"id": 2, "vehicles_waiting": True, "vehicles_coming": False, "vehicles_blocking": False, "emergency_vehicle": False, "public_transport": True}]})
    print(f"> Received (notify_sensor_change): {received}")

    global msg_id
    msg_id = json.loads(received)["msg_id"]

    data = json.loads(received)["data"]
    if json.loads(received)["msg_type"] == "notify_sensor_change":
        global json_data
        for i, currentValue in enumerate(json_data):
            for sensorValue in data:
                if currentValue["id"] == sensorValue["id"]:
                    json_data[i]["vehicles_waiting"] = sensorValue["vehicles_waiting"]
                    json_data[i]["vehicles_coming"] = sensorValue["vehicles_coming"]
                    json_data[i]["emergency_vehicle"] = sensorValue["emergency_vehicle"]
                    json_data[i]["vehicles_blocking"] = sensorValue["vehicles_blocking"]
                    json_data[i]["public_transport"] = sensorValue["public_transport"]

    print(f"> Compared existing data with notify_sensor_change")      

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

    global current_clearing_time, saved_time
    current_clearing_time = max_clearing_time
    saved_time = time.time()

    print(f"> Evaluated current data")      

    global json_data
    json_data = data
    return commands

# Sends notify_traffic_light_change message to server
async def notifyTrafficLightChange(data):
    global msg_id
    msg_id += 1

    command = json.dumps({ "msg_id": msg_id, "msg_type": "notify_traffic_light_change", "data": data })

    print(f"> Send (notify_traffic_light_change): {command}")

# Runs startClient function until complete
asyncio.get_event_loop().run_until_complete(startClient())