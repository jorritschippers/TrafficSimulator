# Traffic Simulator Controller
# Software Development 2020/2021
# Group 2: Tjeerd van Gelder & Jorrit Schippers

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
public_vehicles = []
vehicles_waiting = []
vehicles_coming = []
executed_lights = []
forgotten_lights = []

# Creates a websocketconnection and executes other functions by multithreading
async def main():
    global ip
    uri = "ws://" + ip[1] + ":6969"
    async with websockets.connect(uri) as websocket:
        print(f"> Controller made connection with server")
        await initialization(websocket)

        while True:
            # Create threads for functions executeAlgorithms and notifySensorChange
            x = threading.Thread(target= await executeAlgorithms(websocket), args=(1,))  
            y = threading.Thread(target= await notifySensorChange(websocket), args=(1,))  

            # Start threads
            x.start()
            y.start()       

            # Join threads when executed
            if not x.is_alive:
                x.join()

            if not y.is_alive:
                y.join()         

# Receives initialization data from server
async def initialization(websocket):
    received = await websocket.recv()
    print(f"> Received (initialization): {received}")

    global msg_id, json_data
    msg_id = json.loads(received)["msg_id"] 
    json_data = json.loads(received)["data"]        

# Executes standard loop of controller
async def executeAlgorithms(websocket):
    global executed_lights, forgotten_lights, json_data, actions, crosses, forgotten_time, emergency_vehicles, public_vehicles, vehicles_waiting, vehicles_coming
    
    # Create array of forgotten traffic lights that were not used every two minutes
    if (time.time() - forgotten_time) >= 120:  
        forgotten_time = time.time()   

        for light in json_data:     
            if not light["id"] in forgotten_lights:    
                forgotten_lights.append(light["id"])

        for light in executed_lights:
            forgotten_lights.remove(light)

        executed_lights.clear()

    # Create executable actions for the traffic lights
    await createActions(websocket)

    # Update the actions and send the changes to the server
    for i, action in enumerate(actions):
        if time.time() >= action[2]:
            # If state equals green set traffic light to orange and send change to server
            if action[1] == "green":
                actions[i][2] =  time.time() + action[3] 
                actions[i][1] = "orange"   
                await notifyTrafficLightChange(websocket, [{"id": action[0], "state": "orange"}])
            
            # If state equals orange set traffic light to red and send change to server
            elif action[1] == "orange":
                actions[i][2] =  time.time() + action[3] 
                actions[i][1] = "red"  
                await notifyTrafficLightChange(websocket, [{"id": action[0], "state": "red"}])
            
            # If state equals red remove crosses of traffic light from crosses array
            elif action[1] == "red":
                for data in json_data:
                    if data["id"] == action[0]:
                        for c, cross in enumerate(crosses):
                            if data["crosses"] == cross:
                                crosses.pop(c)
                                break

                actions.pop(i)
    
    print(f"> Updated and deleted actions")   

# Create new actions by processing the array values
async def createActions(websocket):
    global json_data, actions, crosses, emergency_vehicles, vehicles_blocking, public_vehicles, vehicles_waiting, vehicles_coming, forgotten_lights

    emergency_vehicles = await updateArray(emergency_vehicles, websocket)
    public_vehicles = await updateArray(public_vehicles, websocket)
    forgotten_lights = await updateArray(forgotten_lights, websocket)
    vehicles_waiting = await updateArray(vehicles_waiting, websocket)
    vehicles_coming = await updateArray(vehicles_coming, websocket)

    print(f"> Actions created: {len(actions)}")  

# Updates given data arrays
async def updateArray(array, websocket):
    # Check if light can be set to green
    for dataRow in json_data:
        for i, id in enumerate(array):
            if dataRow["id"] == id:
                proceed = True

                global vehicles_blocking, crosses, actions
                # Check if vehicles_blocking contains id
                for block in vehicles_blocking:
                    if block == id:
                        proceed = False
                        break

                # Check if crosses contains id
                for cross in crosses:
                    for singleCross in cross:
                        if singleCross == id:
                            proceed = False
                            break

                # Check if actions contains id
                for action in actions:
                    if action[0] == id:
                        proceed = False
                        break

                if proceed:
                    # Creates a new action and sends it to the server
                    crosses.append(dataRow["crosses"])
                    actions.append([dataRow["id"], "green", time.time() + (dataRow["clearing_time"]/2), dataRow["clearing_time"]/2])
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

# Changes input to boolean
def valueToBool(value):
    return str(value).lower() in ("TRUE", "True", "true", "1")  

# Receives notify_sensor_change from server
async def notifySensorChange(websocket):
    received = await websocket.recv()

    print(f"> Received (notify_sensor_change): {received}")

    global msg_id, emergency_vehicles, vehicles_blocking, public_vehicles, vehicles_waiting, vehicles_coming, forgotten_lights

    # Update current msg_id value
    msg_id = json.loads(received)["msg_id"]

    # Update the current data array with the new data from the sensors
    for sensorValue in json.loads(received)["data"]:
        if "emergency_vehicle" in sensorValue:
            emergency_vehicles = alterArrayValues(emergency_vehicles, sensorValue["id"], sensorValue["emergency_vehicle"])
        
        if "public_vehicle" in sensorValue:
            public_vehicles = alterArrayValues(public_vehicles, sensorValue["id"], sensorValue["public_vehicle"])
                
        if "vehicles_waiting" in sensorValue:
            vehicles_waiting = alterArrayValues(vehicles_waiting, sensorValue["id"], sensorValue["vehicles_waiting"])
        
        if "vehicles_coming" in sensorValue:
            vehicles_coming = alterArrayValues(vehicles_coming, sensorValue["id"], sensorValue["vehicles_coming"])

        if "vehicles_blocking" in sensorValue:

            # Check if vehicles_blocking contains id, else add or remove it
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

# Alters the data array with the sensor information with adding or removing data
def alterArrayValues(array, id, value):
    if valueToBool(value):
        proceed = True

        # Check if array contains id, else add it to the array
        for row in array:
            if row == id:
                proceed = False
                break

        if proceed:
            array.append(id)
            global executed_lights

            # Check if executed_lights contains id, else add it to the array
            for light in enumerate(executed_lights):
                if light == id:
                    proceed = False
                    break
            
            if proceed:
                executed_lights.append(id)
    else:
        proceed = False

        # Check if array contains id, else remove it from the array
        for row in array:
            if row == id:
                proceed = True
                break

        if proceed:
            array.pop(array.index(id)) 

    return array

# Runs main function until complete
asyncio.get_event_loop().run_until_complete(main())