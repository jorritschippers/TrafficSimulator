# Traffic Simulator Controller

# Imports
import asyncio
import json
import time
import threading
import websockets

#IP's     Group 1          Group 2           Group 3          Group 4         Group 5
ip = ["84.86.123.188", "82.197.211.219", "31.201.228.97", "147.12.9.237", "94.214.255.27"]

# Global data and values
msg_id = 0
forgotten_time = time.time()
json_data = []
actions = []
crosses = []
emergency_vehicles = []
vehicles_blocking = []
public_transports = []
vehicles_waiting = []
vehicles_coming = []
forgotten_lights = []

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
    global forgotten_lights, json_data, actions, crosses, forgotten_time, emergency_vehicles, public_transports, vehicles_waiting, vehicles_coming
    if (time.time() - forgotten_time) >= 60:
        forgotten_lights.clear()
        forgotten_time = time.time()
        for light in json_data:
            forgotten_lights.append(light["id"])
        forgotten_lights = removeFromArray(forgotten_lights, emergency_vehicles)
        forgotten_lights = removeFromArray(forgotten_lights, public_transports)
        forgotten_lights = removeFromArray(forgotten_lights, vehicles_waiting)
        forgotten_lights = removeFromArray(forgotten_lights, vehicles_coming)

    await createActions(websocket)

    for i, action in enumerate(actions):
        if(time.time() - action[2]) >= action[3]:
            if action[1] == "green":
                actions[i][2] =  time.time()
                actions[i][1] = "orange"
                await notifyTrafficLightChange(websocket, [{"id": action[0], "state": "orange"}])
            elif action[1] == "orange":
                actions[i][2] =  time.time()
                actions[i][1] = "red"
                await notifyTrafficLightChange(websocket, [{"id": action[0], "state": "red"}])
            elif action[1] == "red":
                for data in json_data:
                    if data["id"] == action[0]:
                        for c, cross in enumerate(crosses):
                            if data["crosses"] == cross:
                                crosses.pop(c)
                                break
                actions.pop(i)
    
    print(f"> Updated and deleted actions")

# Removes values from array
def removeFromArray(array, remove):
    for i, arr in enumerate(array):
        for rem in remove:
            if rem == arr:
                array.pop(i)

    return array

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

    global msg_id, emergency_vehicles, vehicles_blocking, public_transports, vehicles_waiting, vehicles_coming, forgotten_lights
    msg_id = json.loads(received)["msg_id"]

    for sensorValue in json.loads(received)["data"]:
        if "emergency_vehicle" in sensorValue:
            emergency_vehicles = alterArray(emergency_vehicles, sensorValue["id"], sensorValue["emergency_vehicle"])
        
        if "public_transport" in sensorValue:
            public_transports = alterArray(public_transports, sensorValue["id"], sensorValue["public_transport"])
                
        if "vehicles_waiting" in sensorValue:
            vehicles_waiting = alterArray(vehicles_waiting, sensorValue["id"], sensorValue["vehicles_waiting"])
        
        if "vehicles_coming" in sensorValue:
            vehicles_coming = alterArray(vehicles_coming, sensorValue["id"], sensorValue["vehicles_coming"])

        if "vehicles_blocking" in sensorValue:
            if valueToBool(sensorValue["vehicles_blocking"]):
                proceed = True
                for item in vehicles_blocking:
                    if item == sensorValue["id"]:
                        proceed = False
                        break

                if proceed:
                    vehicles_blocking.append(sensorValue["id"])
            else:
                for i, item in enumerate(vehicles_blocking):
                    if item == sensorValue["id"]:
                        vehicles_blocking.pop(i)
                        break 

    print(f"> Processed notify_sensor_change")     

def alterArray(array, id, value):
    if valueToBool(value):
        proceed = True
        for row in array:
            if row == id:
                proceed = False
                break

        if proceed:
            array.append(id)
            global forgotten_lights
            for i, light in enumerate(forgotten_lights):
                if light == id:
                    forgotten_lights.pop(i)
    else:
        proceed = False
        for row in array:
            if row == id:
                proceed = True
                break

        if proceed:
            array.pop(array.index(id)) 

    return array

# Changes input to boolean
def valueToBool(value):
    return str(value).lower() in ("TRUE", "True", "true", "1")

# Create new actions by processing the array values
async def createActions(websocket):
    global json_data, actions, crosses, emergency_vehicles, vehicles_blocking, public_transports, vehicles_waiting, vehicles_coming, forgotten_lights

    emergency_vehicles = await updateArray(emergency_vehicles, websocket)
    public_transports = await updateArray(public_transports, websocket)
    vehicles_waiting = await updateArray(vehicles_waiting, websocket)
    vehicles_coming = await updateArray(vehicles_coming, websocket)
    forgotten_lights = await updateArray(forgotten_lights, websocket)

    print(f"> Actions created: {len(actions)}")  

# Changes data of arrays
async def updateArray(array, websocket):
    for dataRow in json_data:
        for i, arrayRow in enumerate(array):
            if dataRow["id"] == arrayRow:
                proceed = True

                global vehicles_blocking, crosses, actions
                for block in vehicles_blocking:
                    if block == arrayRow:
                        proceed = False
                        break

                for cross in crosses:
                    for singleCross in cross:
                        if singleCross == arrayRow:
                            proceed = False
                            break

                for action in actions:
                    if action[0] == arrayRow:
                        proceed = False
                        break

                if proceed:
                    crosses.append(dataRow["crosses"])
                    actions.append([dataRow["id"], "green", time.time(), dataRow["clearing_time"]])
                    await notifyTrafficLightChange(websocket, [{"id": dataRow["id"], "state": "green"}])
                    array.pop(i)
    return array  

# Sends notify_traffic_light_change message to server
async def notifyTrafficLightChange(websocket, data):
    global msg_id

    msg_id = msg_id + 1
    command = json.dumps({ "msg_id": msg_id, "msg_type": "notify_traffic_light_change", "data": data })
    await websocket.send(command)

    print(f"> Send (notify_traffic_light_change): {command}")

# Runs main function until complete
asyncio.get_event_loop().run_until_complete(main())