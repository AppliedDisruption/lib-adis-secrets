from adis_secrets.backends.infisical_rest import InfisicalClient
from adis_secrets.reader import load_env_file, resolve_bootstrap_secrets_file

_bootstrap = load_env_file(resolve_bootstrap_secrets_file())

PROJECT_ID = _bootstrap.get("VAULT_CFG_KEY_INFISICAL_PROJECT_ID", "")
CLIENT_ID = _bootstrap.get("VAULT_SEC_KEY_INFISICAL_CLIENT_ID", "")
CLIENT_SECRET = _bootstrap.get("VAULT_SEC_KEY_INFISICAL_CLIENT_SECRET", "")
ROOT_READ_SECRET = "VAULT_SEC_KEY_INFISICAL_CLIENT_ID"
APP_READ_SECRET = "VAULT_SEC_KEY_ANTHROPIC_API_KEY"

ENVIRONMENTS = ["dev", "staging", "prod"]

ROOT_TEST_SECRET = "TEST_INFISICAL_LIB_ROOT"
APP_TEST_SECRET = "TEST_INFISICAL_LIB_APP"

FOLDER_PATH = "/app"


def test_read_existing(client):
    print("\n===== READ EXISTING SECRETS =====")

    for env in ENVIRONMENTS:
        print(f"\nENV: {env}")

        try:
            root_val = client.get_secret(
                ROOT_READ_SECRET,
                environment=env,
                secret_path="/"
            )
            print("ROOT:", "✅ OK" if root_val else "⚠️ missing")

        except Exception as e:
            print("❌ ROOT READ ERROR:", e)

        try:
            app_val = client.get_secret(
                APP_READ_SECRET,
                environment=env,
                secret_path="/app"
            )
            print("/app:", "✅ OK" if app_val else "⚠️ missing")

        except Exception as e:
            print("❌ APP READ ERROR:", e)


def test_write_read_delete(client):
    print("\n===== WRITE / READ / DELETE TEST =====")

    for env in ENVIRONMENTS:
        print(f"\nENV: {env}")

        root_value = f"root_test_{env}"
        app_value = f"app_test_{env}"

        # create
        client.set_secret(ROOT_TEST_SECRET, root_value, env, "/")
        client.set_secret(APP_TEST_SECRET, app_value, env, "/app")

        # read
        r1 = client.get_secret(ROOT_TEST_SECRET, env, "/")
        r2 = client.get_secret(APP_TEST_SECRET, env, "/app")

        print("ROOT READ:", "✅" if r1 == root_value else "❌")
        print("APP READ:", "✅" if r2 == app_value else "❌")

        # delete
        client.delete_secret(ROOT_TEST_SECRET, env, "/")
        client.delete_secret(APP_TEST_SECRET, env, "/app")

        print("Deleted disposable secrets")


def main():
    client = InfisicalClient(
        project_id=PROJECT_ID,
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET
    )

    test_read_existing(client)
    test_write_read_delete(client)


if __name__ == "__main__":
    main()