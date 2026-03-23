import requests
import uuid
import threading
import time

URL = "http://127.0.0.1:8000/ledger/transfer/"

success_count = 0
error_count = 0
lock = threading.Lock()

def send_transfer():
    global success_count, error_count

    payload = {
        "sender_id": 1,
        "receiver_id": 2,
        "amount": 1,
        "reference_id": str(uuid.uuid4())
    }

    try:
        response = requests.post(URL, json=payload, timeout=10)

        with lock:
            if response.status_code == 200:
                success_count += 1
            else:
                error_count += 1
            if response.status_code == 200:
                print(f"{response.status_code}: {response.json()}")
            else:
                # Extract error message from HTML response
                error_text = response.text
                if "IntegrityError" in error_text:
                    print(f"{response.status_code}: IntegrityError - duplicate transaction")
                elif "OperationalError" in error_text or "database" in error_text.lower():
                    print(f"{response.status_code}: Database error - concurrency limit")
                else:
                    print(f"{response.status_code}: {error_text[:300]}")

    except requests.exceptions.RequestException as e:
        with lock:
            error_count += 1
        print(f"Request failed: {e}")


threads = []

print("Starting stress test with 20 concurrent requests...\n")

for i in range(20):
    t = threading.Thread(target=send_transfer)
    threads.append(t)
    t.start()
      # Small delay to avoid overwhelming the server

for t in threads:
    t.join()

print(f"\n--- Results ---")
print(f"Success: {success_count}")
print(f"Errors: {error_count}")
print("Finished")