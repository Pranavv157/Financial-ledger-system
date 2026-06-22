import requests
import uuid
import threading
from decimal import Decimal
import time

URL = "http://127.0.0.1:8000/ledger/transfers/"
BALANCE_URL = "http://127.0.0.1:8000/ledger/accounts/1/balance/"

success_count = 0
error_count = 0
lock = threading.Lock()


def send_transfer():
    global success_count, error_count

    payload = {
        "sender_id": 1,
        "receiver_id": 2,
        "amount": "1",
        "reference_id": str(uuid.uuid4())
    }

    try:
        response = requests.post(URL, json=payload, timeout=10)

        with lock:
            if response.status_code in (200, 202):
                success_count += 1
            else:
                error_count += 1

            print(f"{response.status_code}: {response.text}")

    except Exception as e:
        with lock:
            error_count += 1
        print(f"Error: {e}")


threads = []

print("Starting stress test...\n")

for _ in range(1000):
    t = threading.Thread(target=send_transfer)
    threads.append(t)
    t.start()
    start = time.time()
    end = time.time()

print(f"Total Time: {end-start:.2f}s")
    

for t in threads:
    t.join()

print("\n--- Results ---")
print(f"Success: {success_count}")
print(f"Errors: {error_count}")


#  Check final balance
print("\nChecking final balance...")

resp = requests.get(BALANCE_URL)
print("Final balance:", resp.json())