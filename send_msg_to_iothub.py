import asyncio
import json
from azure.iot.device.aio import IoTHubDeviceClient
from azure.iot.device import Message, MethodResponse

connection_string = "HostName=iothub-swapnil.azure-devices.net;DeviceId=qsr;SharedAccessKey=RHBsdPxlTeEtLppL2s7tx5236YxU//6efF7xMGcCHaU="

async def main():
    # Fetch the connection string from an environment variable
    #conn_str = os.getenv("IOTHUB_DEVICE_CONNECTION_STRING")
    conn_str = connection_string

    # Create instance of the device client using the authentication provider
    device_client = IoTHubDeviceClient.create_from_connection_string(conn_str)

    # Connect the device client.
    await device_client.connect()

    # Send a single message
    print("Sending message...")
    sample_json = {
        "bag_no": 1, 
        "item_name": "soda", 
        "action": "add"
        }
    
    msg = Message(json.dumps(sample_json))
    msg.content_encoding = "utf-8"
    msg.content_type = "application/json"
    print("Sent message")
    await device_client.send_message(msg)
    print("Message successfully sent!")

    # finally, shut down the client
    await device_client.shutdown()


if __name__ == "__main__":
    asyncio.run(main())