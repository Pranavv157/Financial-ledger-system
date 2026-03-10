import requests
import uuid
import threading

URL = "http://127.0.0.1:8000/ledger/transfer/"

def send_transfer():

    payload = {
        "sender_id": 1,
        "receiver_id": 2,
        "amount": 1,
        "reference_id": str(uuid.uuid4())
    }

    response = requests.post(URL, json=payload)

    try:
        print(response.status_code, response.json())
    except:
        print(response.status_code, response.text[:100])


threads = []

for i in range(20):
    t = threading.Thread(target=send_transfer)
    threads.append(t)
    t.start()

for t in threads:
    t.join()

print("Finished")