from infiscal_client import InfisicalClient


client_id_1="a5aa70ae-7de2-485b-b2f2-a426de9f6a6c"
client_secret_1="1785d0343e70f14c898f647437148614fc5c8dc60b6ef5f63bd59aab2ba9f78f"
project_id_1="324e36e9-98ff-4cc1-bed8-3e14aa609cf2"
project_id_2="9bfe0720-2006-4351-9beb-1f09595eccf8"
client_id_2="5a5496a4-006c-48b1-82e6-723fef832759"
client_secret_2="e181d195a159608ad22185bba725e5026044ec447e414136b7e79a0c61b51aee"


PROJECT_ID = project_id_2
CLIENT_ID = client_id_2
CLIENT_SECRET = client_secret_2

ENVIRONMENTS = ["development", "staging", "production"]

ROOT_READ_SECRET = "TENANT_SLUGS"
APP_READ_SECRET = "VAULT_SEC_KEY_SLACK_SIGNING_SECRET"

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