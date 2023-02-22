import json
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

@app.route('/', methods=["GET", "POST"])
def main():
    return render_template('index.html')

@app.route('/order', methods=["POST"])
def order():
    # process JSON
    content_type = request.headers.get('Content-Type')
    if content_type == 'application/json':
        json_data = request.json
        # store incoming orders in SQL database
        insert_order_into_db(json_data)
    return 'Content-Type not supported'

@app.route('/inference', methods=["POST"])
async def inference():
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
    return 'Content-Type not supported'

def process_inference(inference):
    # To-do
    return output_json

def insert_order_into_db(order):
    with pyodbc.connect('DRIVER='+driver+';SERVER=tcp:'+server+';PORT=1433;DATABASE='+database+';UID='+username+';PWD='+ password) as conn:
        with conn.cursor() as cursor:
            cursor.execute("INSERT INTO [dbo].[orders] VALUES (?)", (json.dumps(order),))
    

if __name__ == '__main__':
    app.run(debug=True)