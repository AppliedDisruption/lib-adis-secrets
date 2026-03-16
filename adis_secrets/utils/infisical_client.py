import requests


class InfisicalClient:
    BASE_URL = "https://app.infisical.com"

    ENV_MAP = {
        "development": "dev",
        "dev": "dev",
        "staging": "staging",
        "production": "prod",
        "prod": "prod"
    }

    def __init__(self, project_id, client_id, client_secret):
        self.project_id = project_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.token = None

    def _normalize_env(self, env):
        return self.ENV_MAP.get(env.lower(), env)

    def _authenticate(self):
        r = requests.post(
            f"{self.BASE_URL}/api/v1/auth/universal-auth/login",
            json={
                "clientId": self.client_id,
                "clientSecret": self.client_secret
            },
            timeout=10
        )
        r.raise_for_status()
        self.token = r.json()["accessToken"]

    def _headers(self):
        if not self.token:
            self._authenticate()

        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

    # -------------------
    # READ
    # -------------------
    def get_secret(self, name, environment, secret_path="/"):

        environment = self._normalize_env(environment)

        r = requests.get(
            f"{self.BASE_URL}/api/v4/secrets",
            headers=self._headers(),
            params={
                "projectId": self.project_id,
                "environment": environment,
                "secretPath": secret_path,
                "recursive": "true"
            },
            timeout=10
        )

        r.raise_for_status()

        for s in r.json()["secrets"]:
            if s["secretKey"] == name:
                return s["secretValue"]

        return None

    # -------------------
    # CREATE / UPDATE
    # -------------------
    def set_secret(self, name, value, environment, secret_path="/"):

        environment = self._normalize_env(environment)

        r = requests.post(
            f"{self.BASE_URL}/api/v4/secrets/{name}",
            headers=self._headers(),
            json={
                "projectId": self.project_id,
                "environment": environment,
                "secretValue": value,
                "secretPath": secret_path,
                "type": "shared"
            },
            timeout=10
        )

        # secret exists → update it
        if r.status_code in [400, 409]:
            r = requests.patch(
                f"{self.BASE_URL}/api/v4/secrets/{name}",
                headers=self._headers(),
                json={
                    "projectId": self.project_id,
                    "environment": environment,
                    "secretValue": value,
                    "secretPath": secret_path,
                    "type": "shared"
                },
                timeout=10
            )

        r.raise_for_status()

    # -------------------
    # DELETE
    # -------------------
    def delete_secret(self, name, environment, secret_path="/"):

        environment = self._normalize_env(environment)

        r = requests.delete(
            f"{self.BASE_URL}/api/v4/secrets/{name}",
            headers=self._headers(),
            json={
                "projectId": self.project_id,
                "environment": environment,
                "secretPath": secret_path,
                "type": "shared"
            },
            timeout=10
        )

        r.raise_for_status()