from locust import HttpUser, task, between

class UserApiUser(HttpUser):
    wait_time = between(1, 2)

    @task
    def health(self):
        self.client.get("/healthz")
