import json
import asyncio
import pyodbc
from flask import Flask, request, jsonify, render_template, make_response
from azure.iot.device.aio import IoTHubDeviceClient
from azure.iot.device import Message, MethodResponse

app = Flask(__name__)
conn_str = "HostName=iothub-swapnil.azure-devices.net;DeviceId=qsr;SharedAccessKey=RHBsdPxlTeEtLppL2s7tx5236YxU//6efF7xMGcCHaU="
server = 'qsr.database.windows.net'
database = 'qsr'
username = 'qsradmin'
password = 'qsrP@ssword'   
driver= '{ODBC Driver 18 for SQL Server}'

orders = [{"bag_no" : 1, "items" : [{"French Fries" : 1, "Cheeseburger" : 1, "Soda" : 1, "Chicken Nuggets" : 1}]},
           {"bag_no" : 2, "items" : [{"French Fries" : 1, "Soda" : 1, "Fish Sandwich" : 1, "Chicken Sandwich" : 1, "Spicy Chicken Sandwich" : 1}]}]

dummy_data = [{"id":"people_counting","zone": "lane1","count": 3,"timestamp": "02/22/2023 07:00:00"},
                    {"id":"people_counting","zone": "lane1","count": 3,"timestamp": "02/22/2023 07:05:00"},
                    {"id":"people_counting","zone": "lane1","count": 2,"timestamp": "02/22/2023 07:10:00"},
                    {"id":"people_counting","zone": "lane1","count": 10,"timestamp": "02/22/2023 07:15:00" },
                    {"id":"order_accuracy","bag_no":1,"item_name":"soda","action":"add","result":True,"timestamp": "02/22/2023 07:00:00"},
                    {"id":"order_accuracy","bag_no":1,"item_name":"french fries","action":"add","result":True,"timestamp": "02/22/2023 07:05:00"},
                    {"id":"order_accuracy","bag_no":1,"item_name":"double cheeseburger","action":"add","result":True,"timestamp": "02/22/2023 07:10:00"},
                    {"id":"order_accuracy","bag_no":1,"item_name":"chicken nuggets","action":"add","result":True,"timestamp": "02/22/2023 07:15:00" },
                    {"id": "table_cleanliness","table_id": 1,"occupancy": True,"state": "clean", "timestamp": "02/22/2023 07:00:00"},
                    {"id": "table_cleanliness", "table_id": 2, "occupancy": False, "state": "clean", "timestamp": "02/22/2023 07:00:00"},
                    {"id": "table_cleanliness", "table_id": 3, "occupancy": False, "state": "clean", "timestamp": "02/22/2023 07:00:00"},
                    {"id": "table_cleanliness","table_id": 1, "occupancy": False, "state": "unclean", "timestamp": "02/22/2023 07:10:00"},
                    {"id": "table_cleanliness", "table_id": 2, "occupancy": False, "state": "clean", "timestamp": "02/22/2023 07:10:00"},
                    {'id': 'table_cleanliness', "table_id": 3, "occupancy": False, "state": "clean", "timestamp": "02/22/2023 07:10:00"}
                ]
    
@app.route('/', methods=["GET", "POST"])
def main():
    while(1):
        driver()
    return render_template('index.html')
'''
@app.route('/order', methods=["POST"])
def order():
    # process JSON
    content_type = request.headers.get('Content-Type')
    if content_type == 'application/json':
        json_data = request.json
        # store incoming orders in SQL database
        insert_order_into_db(json_data)
    return 'Content-Type not supported'
'''
@app.route('/inference', methods=["POST"])
def inference():
    # process JSON
    content_type = request.headers.get('Content-Type')
    if content_type == 'application/json':
        json_data = request.json
        # sample json data
        # {'id': 'order_accuracy', 'bag_no': 1, 'item_name': 'soda', 'action': 'add', 'timestamp': 'time'}
        # {'id': 'people_counting', 'zone': 'lane/kiosk/cashier', 'count': 10, 'timestamp': 'time'}
        # {'id': 'table_cleanliness', 'table_id': 1, 'occupany': True/False, 'state': 'clean/unclean', 'timestamp': 'time'}

        # Check if the inference requires any processing before sending to IoTHub
        # Decode json data
        decode_json = json.loads(json_data)
        if decode_json["id"] == "order_accuracy":
            json_data = process_inference(json_data)
         
        send_data_to_iothub(json_data)

    return 'Content-Type not supported'

async def send_data_to_iothub(json_data):
    # Create instance of the device client using the authentication provider
    device_client = IoTHubDeviceClient.create_from_connection_string(conn_str)
    # Connect the device client.
    await device_client.connect()

    msg = Message(json.dumps(json_data))
    msg.content_encoding = "utf-8"
    msg.content_type = "application/json"
        
    await device_client.send_message(msg)
    print("Message successfully sent!")

    # finally, shut down the client
    await device_client.shutdown()

def process_inference(inference):
    # sample inference data for order accuracy: {'id': 'order_accuracy', 'bag_no': 1, 'item_name': 'soda', 'action': 'add'}
    #inference = json.loads(inference) # parse valid JSON string and convert to a Python dictionary

    correct_order = [""]
    for i in range(0, len(orders)):
        if orders[i]["bag_no"] == inference["bag_no"]:
            correct_order = orders[i]["items"]
    # order is a key-value hashmap which is an associative array
    # if item addded to bag is part of the order, make status true
    # if item added to bag is not part of the order, status is false
    if inference["item_name"] in correct_order[0].keys():
        if inference["action"] == "add":
            result_json = inference
            result_json["Status"] = True
            correct_order[0][inference["item_name"]] -= 1
            if is_order_complete(correct_order[0]):
                order_complete = {"bag_no": inference["bag_no"], "Status": "order-completed"}
                send_data_to_iothub(order_complete)
        elif inference["action"] == "remove":
            result_json = inference
            result_json["Status"] = False
    # if item added to bag is not in the order check if being added or removed from bag
    # if being added and it's not part of order, status is false
    # if being removed and is not part of the order, status is false
    elif inference["item_name"] not in correct_order[0].keys():
        if inference["action"] == "add":
            result_json = inference
            result_json["Status"] = False
        elif inference["action"] == "remove":
            result_json = inference
            result_json["Status"] = True
            if is_order_complete(correct_order[0]):
                order_complete = {"bag_no": inference["bag_no"], "Status": "order-completed"}
                send_data_to_iothub(order_complete)
    return result_json

def is_order_complete(order):
    for value in order.values():
        if value >= 1:
            return False
        return True
        
def insert_order_into_db(order):
    with pyodbc.connect('DRIVER='+driver+';SERVER=tcp:'+server+';PORT=1433;DATABASE='+database+';UID='+username+';PWD='+ password) as conn:
        with conn.cursor() as cursor:
            cursor.execute("INSERT INTO [dbo].[orders] VALUES (?)", (json.dumps(order),))
    
def driver():
    for data in dummy_data:
        #decode_json = json.loads(data)
        if data["id"] == "order_accuracy":
            data = process_inference(data)
        print(data)       
        asyncio.run(send_data_to_iothub(data))

if __name__ == '__main__':
    app.run(debug=True)