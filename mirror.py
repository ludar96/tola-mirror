from telethon.sync import TelegramClient, events
import json
import asyncio
import traceback
import threading

# Read configuration from config.json
with open('config.json', 'r') as config_file:
    config = json.load(config_file)

API_ID = '24137884'
API_HASH = 'f7036e2f2b6dd5d1767498b44b0387f8'
phone_numbers = config['phone_numbers']
source_chat_id = config['source_chat_id']
destination_chat_id = config['destination_chat_id']

# Initialize clients for each account
clients = []
for phone_number in phone_numbers:
    client = TelegramClient(f'session_{phone_number}', API_ID, API_HASH)
    clients.append(client)
    client.start()

# Initialize processed message IDs for each client
processed_message_ids = {client: set() for client in clients}

# Index for round-robin client selection
client_index = 0

# Signal handler for Ctrl+C
import signal

def signal_handler(signal, frame):
    for client in clients:
        client.disconnect()
    exit(0)

signal.signal(signal.SIGINT, signal_handler)

# Function to send copied messages from source to destination
async def send_copied_messages(event):
    try:
        global client_index
        client = clients[client_index]  # Select a client using round-robin
        client_index = (client_index + 1) % len(clients)  # Update the index for the next iteration
        if event.chat_id == source_chat_id and not event.is_private:
            if event.message.id not in processed_message_ids[client] and event.message.id not in {pid for client_ids in processed_message_ids.values() for pid in client_ids}:
                processed_message_ids[client].add(event.message.id)
                # You can adjust the sleep duration to introduce a delay between messages
                await asyncio.sleep(1)
                await client.send_message(destination_chat_id, event.message.message)
    except Exception as e:
        traceback.print_exc()  # Print full traceback of the exception

if __name__ == '__main__':
    for client in clients:
        client.add_event_handler(send_copied_messages, events.NewMessage())
    for client in clients:
        client.run_until_disconnected()
