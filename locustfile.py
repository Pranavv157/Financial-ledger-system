from locust import HttpUser, task
import uuid


class TransferUser(HttpUser):

    wait_time = lambda self: 0

    @task
    def transfer(self):
        self.client.post(
            "/ledger/transfers/",
            json={
                "sender_id": 1,
                "receiver_id": 2,
                "amount": "1",
                "reference_id": str(uuid.uuid4())
            }
        )