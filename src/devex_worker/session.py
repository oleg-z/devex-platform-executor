import os
import click
import requests
import base64

TOKEN_FILE = os.path.expanduser("~/.devex/token")


class Session:
    def __init__(self, api_base_url):
        self.api_base_url = api_base_url
        self.token = None

    @staticmethod
    def load_session():
        if os.path.exists(TOKEN_FILE):
            with open(TOKEN_FILE, "rb") as file:
                content = file.read()
                url, token = base64.b64decode(content).decode().split(":::")
                session = Session(url)
                session.token = token
                return session

        return None

    def login(self, username, password):
        """Login to the API and save the token."""
        response = requests.post(f"{self.api_base_url}/login/", json={"username": username, "password": password})
        if response.status_code == 200:
            self.token = response.json().get("tokens")["access"]
            if self.token is None:
                click.echo("Invalid response from server.")
            else:
                click.echo("Login successful")
        else:
            click.echo("Login failed. Please check your credentials.")

    def save_token(self):
        os.makedirs(os.path.dirname(TOKEN_FILE), exist_ok=True)

        url_token = f"{self.api_base_url}:::{self.token}"
        encoded_token = base64.b64encode(url_token.encode()).decode()
        with open(TOKEN_FILE, "w") as file:
            file.write(encoded_token)
