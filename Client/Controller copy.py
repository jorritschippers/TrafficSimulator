# Traffic Simulator Controller

# Imports
import asyncio
import websockets
import json
import time
import threading

#IP's     Group 1          Group 2           Group 3          Group 4         Group 5            
ip = ["84.86.123.188", "82.197.211.219", "31.201.228.97", "147.12.9.237", "94.214.255.27"]

# Global data and values
actions = []
crosses = []
json_data = []
emergency_vehicles = []
vehicles_blocking = []
public_transports = []
vehicles_waiting = []
vehicles_coming = []
msg_id = 0

# Creates a websocketconnection and executes other functions by multithreading
async def main():
    global ip
    uri = "ws://" + ip[1] + ":6969"
    # try:
    async with websockets.connect(uri) as websocket:
        print(f"> Controller made connection with server")
        await initialization(websocket)

        while True:
            x = threading.Thread(target= await executeAlgorithms(websocket), args=(1,))  
            y = threading.Thread(target= await notifySensorChange(websocket), args=(1,))  

            x.start()
            y.start() 

            if not x.is_alive:
                x.join()

            if not y.is_alive:
                y.join()  

    # except Exception as e:
    #     print(f"> An error occured ({e})")             

# Executes algorithms of controller
async def executeAlgorithms(websocket):
    createActions(websocket)

    global actions, json_data, crosses
    for i, action in enumerate(actions):
        if(time.time() - action[2]) >= (action[3]/2):
            if(action[1] == "green"):
                actions[i][2] =  time.time()
                notifyTrafficLightChange(websocket, {"id": action[0], "state": "orange"})
            elif(action[1] == "orange"):
                for data in json_data:
                    if data["id"] == action[0]:
                        for c, cross in enumerate(crosses):
                            if data["crosses"] == cross:
                                crosses.remove(c)
                notifyTrafficLightChange(websocket, {"id": action[0], "state": "red"})
                actions.remove(i)
    
    print(f"> Updated and deleted actions")

# Receives initialization from server
async def initialization(websocket):
    received = await websocket.recv()
    print(f"> Received (initialization): {received}")

    global msg_id, json_data
    msg_id = json.loads(received)["msg_id"] 
    json_data = json.loads(received)["data"]             

# Receives notify_sensor_change from server
async def notifySensorChange(websocket):
    received = await websocket.recv()
    print(f"> Received (notify_sensor_change): {received}")

    global msg_id, json_data
    msg_id = json.loads(received)["msg_id"]
    data = json.loads(received)["data"]

    for sensorValue in data:
        global emergency_vehicles, vehicles_blocking, public_transports, vehicles_waiting, vehicles_coming

        if valueToBool(sensorValue["emergency_vehicle"]) == True:
            if (emergency_vehicles.index(sensorValue["id"]) if sensorValue["id"] in emergency_vehicles else -1) == -1:
                emergency_vehicles.append(sensorValue["id"])
        elif valueToBool(sensorValue["emergency_vehicle"]) == False:
            if (emergency_vehicles.index(sensorValue["id"]) if sensorValue["id"] in emergency_vehicles else -1) > -1:
                emergency_vehicles.remove(emergency_vehicles.index(sensorValue["id"]))

        if valueToBool(sensorValue["vehicles_blocking"]) == True:
            if (vehicles_blocking.index(sensorValue["id"]) if sensorValue["id"] in vehicles_blocking else -1) == -1:
                vehicles_blocking.append(sensorValue["id"])
        elif valueToBool(sensorValue["vehicles_blocking"]) == False:
            if (vehicles_blocking.index(sensorValue["id"]) if sensorValue["id"] in vehicles_blocking else -1) > -1:
                vehicles_blocking.remove(vehicles_blocking.index(sensorValue["id"]))

        if valueToBool(sensorValue["public_transport"]) == True:
            if (public_transports.index(sensorValue["id"]) if sensorValue["id"] in public_transports else -1) == -1:
                public_transports.append(sensorValue["id"])
        elif valueToBool(sensorValue["public_transport"]) == False:
            if (public_transports.index(sensorValue["id"]) if sensorValue["id"] in public_transports else -1) > -1:
                public_transports.remove(public_transports.index(sensorValue["id"]))

        if valueToBool(sensorValue["vehicles_waiting"]) == True:
            if (vehicles_waiting.index(sensorValue["id"]) if sensorValue["id"] in vehicles_waiting else -1) == -1:
                vehicles_waiting.append(sensorValue["id"])
        elif valueToBool(sensorValue["vehicles_waiting"]) == False:
            if (vehicles_waiting.index(sensorValue["id"]) if sensorValue["id"] in vehicles_waiting else -1) > -1:
                vehicles_waiting.remove(vehicles_waiting.index(sensorValue["id"]))

        if valueToBool(sensorValue["vehicles_coming"]) == True:
            if (vehicles_coming.index(sensorValue["id"]) if sensorValue["id"] in vehicles_coming else -1) == -1:
                vehicles_coming.append(sensorValue["id"])
        elif valueToBool(sensorValue["vehicles_coming"]) == False:
            if (vehicles_coming.index(sensorValue["id"]) if sensorValue["id"] in vehicles_coming else -1) > -1:
                vehicles_coming.remove(vehicles_coming.index(sensorValue["id"]))

    print(f"> Processed notify_sensor_change")      

# Changes input to boolean
def valueToBool(value):
    return str(value).lower() in ("TRUE", "True", "true", "1")

# Changes data of arrays
def updateArray(array, websocket):
    if len(array) > 0:
        for dataRow in json_data:
            for i, arrayRow in enumerate(array):
                if dataRow["id"] == arrayRow:
                    proceed = True
                    for cross in crosses:
                        for singleCross in cross:
                            if (dataRow["crosses"].index(singleCross) if singleCross in dataRow["crosses"] else -1) > -1:
                                proceed = False

                    if proceed:
                        global actions
                        actions.append([dataRow["id"], "green", time.time(), dataRow["clearing_time"]])
                        notifyTrafficLightChange(websocket, {"id": dataRow["id"], "state": "green"})
                        array.remove(i)
        return array

# Create new actions by processing the array values
async def createActions(websocket):
    global json_data, actions, crosses, emergency_vehicles, vehicles_blocking, public_transports, vehicles_waiting, vehicles_coming

    emergency_vehicles = updateArray(emergency_vehicles, websocket)
    vehicles_blocking = updateArray(vehicles_blocking, websocket)
    public_transports = updateArray(public_transports, websocket)
    vehicles_waiting = updateArray(vehicles_waiting, websocket)
    vehicles_coming = updateArray(vehicles_coming, websocket)

    print(f"> Actions created")      

# Sends notify_traffic_light_change message to server
async def notifyTrafficLightChange(websocket, data):
    global msg_id

    msg_id = msg_id + 1
    command = json.dumps({ "msg_id": msg_id, "msg_type": "notify_traffic_light_change", "data": data })
    await websocket.send(command)

    print(f"> Send (notify_traffic_light_change): {command}")

# Runs main function until complete
asyncio.get_event_loop().run_until_complete(main())