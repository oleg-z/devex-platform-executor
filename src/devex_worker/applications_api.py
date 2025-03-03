import requests

from session import Session


class ApplicationsAPI:
    """Class to interact with the Applications API."""

    def __init__(self, session: Session):
        self.base_url = f"{session.api_base_url}/applications"
        self.token = session.token
        self.headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}

    def get_applications(self):
        response = requests.get(self.base_url, headers=self.headers)
        return response.json() if response.status_code == 200 else None

    def get_application(self, app_id):
        response = requests.get(f"{self.base_url}/{app_id}", headers=self.headers)
        return response.json() if response.status_code == 200 else None

    def create_application(self, app_data):
        response = requests.post(self.base_url, json=app_data, headers=self.headers)
        return response.json() if response.status_code == 201 else None

    def update_application(self, app_id, app_data):
        response = requests.put(f"{self.base_url}/{app_id}", json=app_data, headers=self.headers)
        return response.json() if response.status_code == 200 else None

    def delete_application(self, app_id):
        response = requests.delete(f"{self.base_url}/{app_id}", headers=self.headers)
        return response.status_code == 204
