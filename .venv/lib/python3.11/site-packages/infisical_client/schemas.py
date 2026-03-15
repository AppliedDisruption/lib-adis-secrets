from dataclasses import dataclass
from typing import Any, Optional, List, TypeVar, Type, cast, Callable


T = TypeVar("T")


def from_str(x: Any) -> str:
    assert isinstance(x, str)
    return x


def from_none(x: Any) -> Any:
    assert x is None
    return x


def from_union(fs, x):
    for f in fs:
        try:
            return f(x)
        except:
            pass
    assert False


def to_class(c: Type[T], x: Any) -> dict:
    assert isinstance(x, c)
    return cast(Any, x).to_dict()


def from_int(x: Any) -> int:
    assert isinstance(x, int) and not isinstance(x, bool)
    return x


def from_bool(x: Any) -> bool:
    assert isinstance(x, bool)
    return x


def from_list(f: Callable[[Any], T], x: Any) -> List[T]:
    assert isinstance(x, list)
    return [f(y) for y in x]


@dataclass
class AWSIamAuthMethod:
    identity_id: str
    """The Infisical Identity ID that you want to authenticate to Infisical with."""

    @staticmethod
    def from_dict(obj: Any) -> 'AWSIamAuthMethod':
        assert isinstance(obj, dict)
        identity_id = from_str(obj.get("identityId"))
        return AWSIamAuthMethod(identity_id)

    def to_dict(self) -> dict:
        result: dict = {}
        result["identityId"] = from_str(self.identity_id)
        return result


@dataclass
class AzureAuthMethod:
    identity_id: str
    """The Infisical Identity ID that you want to authenticate to Infisical with."""

    @staticmethod
    def from_dict(obj: Any) -> 'AzureAuthMethod':
        assert isinstance(obj, dict)
        identity_id = from_str(obj.get("identityId"))
        return AzureAuthMethod(identity_id)

    def to_dict(self) -> dict:
        result: dict = {}
        result["identityId"] = from_str(self.identity_id)
        return result


@dataclass
class GCPIamAuthMethod:
    identity_id: str
    service_account_key_file_path: str
    """The path to the GCP Service Account key file.
    
    You can generate this key file by going to the GCP Console -> IAM & Admin -> Service
    Accounts -> *Select your service account* -> Keys tab -> Add key.
    Note: The key must be in JSON format.
    """

    @staticmethod
    def from_dict(obj: Any) -> 'GCPIamAuthMethod':
        assert isinstance(obj, dict)
        identity_id = from_str(obj.get("identityId"))
        service_account_key_file_path = from_str(obj.get("serviceAccountKeyFilePath"))
        return GCPIamAuthMethod(identity_id, service_account_key_file_path)

    def to_dict(self) -> dict:
        result: dict = {}
        result["identityId"] = from_str(self.identity_id)
        result["serviceAccountKeyFilePath"] = from_str(self.service_account_key_file_path)
        return result


@dataclass
class GCPIDTokenAuthMethod:
    identity_id: str

    @staticmethod
    def from_dict(obj: Any) -> 'GCPIDTokenAuthMethod':
        assert isinstance(obj, dict)
        identity_id = from_str(obj.get("identityId"))
        return GCPIDTokenAuthMethod(identity_id)

    def to_dict(self) -> dict:
        result: dict = {}
        result["identityId"] = from_str(self.identity_id)
        return result


@dataclass
class KubernetesAuthMethod:
    identity_id: str
    """The Infisical Identity ID that you want to authenticate to Infisical with."""
    service_account_token_path: Optional[str] = None
    """The path to the Kubernetes Service Account token file.
    
    If no path is provided, it will default to
    /var/run/secrets/kubernetes.io/serviceaccount/token.
    """

    @staticmethod
    def from_dict(obj: Any) -> 'KubernetesAuthMethod':
        assert isinstance(obj, dict)
        identity_id = from_str(obj.get("identityId"))
        service_account_token_path = from_union([from_none, from_str], obj.get("serviceAccountTokenPath"))
        return KubernetesAuthMethod(identity_id, service_account_token_path)

    def to_dict(self) -> dict:
        result: dict = {}
        result["identityId"] = from_str(self.identity_id)
        if self.service_account_token_path is not None:
            result["serviceAccountTokenPath"] = from_union([from_none, from_str], self.service_account_token_path)
        return result


@dataclass
class UniversalAuthMethod:
    client_id: str
    client_secret: str

    @staticmethod
    def from_dict(obj: Any) -> 'UniversalAuthMethod':
        assert isinstance(obj, dict)
        client_id = from_str(obj.get("clientId"))
        client_secret = from_str(obj.get("clientSecret"))
        return UniversalAuthMethod(client_id, client_secret)

    def to_dict(self) -> dict:
        result: dict = {}
        result["clientId"] = from_str(self.client_id)
        result["clientSecret"] = from_str(self.client_secret)
        return result


@dataclass
class AuthenticationOptions:
    """Configure the authentication method to use.
    
    Make sure to only set one one method at a time to avoid conflicts and unexpected behavior.
    """
    access_token: Optional[str] = None
    aws_iam: Optional[AWSIamAuthMethod] = None
    azure: Optional[AzureAuthMethod] = None
    gcp_iam: Optional[GCPIamAuthMethod] = None
    gcp_id_token: Optional[GCPIDTokenAuthMethod] = None
    kubernetes: Optional[KubernetesAuthMethod] = None
    universal_auth: Optional[UniversalAuthMethod] = None

    @staticmethod
    def from_dict(obj: Any) -> 'AuthenticationOptions':
        assert isinstance(obj, dict)
        access_token = from_union([from_none, from_str], obj.get("accessToken"))
        aws_iam = from_union([AWSIamAuthMethod.from_dict, from_none], obj.get("awsIam"))
        azure = from_union([AzureAuthMethod.from_dict, from_none], obj.get("azure"))
        gcp_iam = from_union([GCPIamAuthMethod.from_dict, from_none], obj.get("gcpIam"))
        gcp_id_token = from_union([GCPIDTokenAuthMethod.from_dict, from_none], obj.get("gcpIdToken"))
        kubernetes = from_union([KubernetesAuthMethod.from_dict, from_none], obj.get("kubernetes"))
        universal_auth = from_union([UniversalAuthMethod.from_dict, from_none], obj.get("universalAuth"))
        return AuthenticationOptions(access_token, aws_iam, azure, gcp_iam, gcp_id_token, kubernetes, universal_auth)

    def to_dict(self) -> dict:
        result: dict = {}
        if self.access_token is not None:
            result["accessToken"] = from_union([from_none, from_str], self.access_token)
        if self.aws_iam is not None:
            result["awsIam"] = from_union([lambda x: to_class(AWSIamAuthMethod, x), from_none], self.aws_iam)
        if self.azure is not None:
            result["azure"] = from_union([lambda x: to_class(AzureAuthMethod, x), from_none], self.azure)
        if self.gcp_iam is not None:
            result["gcpIam"] = from_union([lambda x: to_class(GCPIamAuthMethod, x), from_none], self.gcp_iam)
        if self.gcp_id_token is not None:
            result["gcpIdToken"] = from_union([lambda x: to_class(GCPIDTokenAuthMethod, x), from_none], self.gcp_id_token)
        if self.kubernetes is not None:
            result["kubernetes"] = from_union([lambda x: to_class(KubernetesAuthMethod, x), from_none], self.kubernetes)
        if self.universal_auth is not None:
            result["universalAuth"] = from_union([lambda x: to_class(UniversalAuthMethod, x), from_none], self.universal_auth)
        return result


@dataclass
class ClientSettings:
    access_token: Optional[str] = None
    """**DEPRECATED**: The access token field is deprecated. Please use the new auth object
    field instead.
    """
    auth: Optional[AuthenticationOptions] = None
    """Configure the authentication method to use.
    
    Make sure to only set one one method at a time to avoid conflicts and unexpected behavior.
    """
    cache_ttl: Optional[int] = None
    """cacheTTL controls how often the cache should refresh, default is 300 seconds. Set to 0 to
    disable the cache.
    """
    client_id: Optional[str] = None
    """**DEPRECATED**: The client secret field is deprecated. Please use the new auth object
    field instead.
    """
    client_secret: Optional[str] = None
    """**DEPRECATED**: The client secret field is deprecated. Please use the new auth object
    field instead.
    """
    site_url: Optional[str] = None
    """The URL of the site to connect to. Defaults to "https://app.infisical.com"."""
    ssl_certificate_path: Optional[str] = None
    """The SSL certificate path is an optional field that allows you to specify a custom SSL
    certificate to use for requests made to Infisical.
    This option can be substituted with the `INFISICAL_SSL_CERTIFICATE` environment variable,
    which should contain the certificate as a string, not the path.
    """
    user_agent: Optional[str] = None

    @staticmethod
    def from_dict(obj: Any) -> 'ClientSettings':
        assert isinstance(obj, dict)
        access_token = from_union([from_none, from_str], obj.get("accessToken"))
        auth = from_union([AuthenticationOptions.from_dict, from_none], obj.get("auth"))
        cache_ttl = from_union([from_none, from_int], obj.get("cacheTtl"))
        client_id = from_union([from_none, from_str], obj.get("clientId"))
        client_secret = from_union([from_none, from_str], obj.get("clientSecret"))
        site_url = from_union([from_none, from_str], obj.get("siteUrl"))
        ssl_certificate_path = from_union([from_none, from_str], obj.get("sslCertificatePath"))
        user_agent = from_union([from_none, from_str], obj.get("userAgent"))
        return ClientSettings(access_token, auth, cache_ttl, client_id, client_secret, site_url, ssl_certificate_path, user_agent)

    def to_dict(self) -> dict:
        result: dict = {}
        if self.access_token is not None:
            result["accessToken"] = from_union([from_none, from_str], self.access_token)
        if self.auth is not None:
            result["auth"] = from_union([lambda x: to_class(AuthenticationOptions, x), from_none], self.auth)
        if self.cache_ttl is not None:
            result["cacheTtl"] = from_union([from_none, from_int], self.cache_ttl)
        if self.client_id is not None:
            result["clientId"] = from_union([from_none, from_str], self.client_id)
        if self.client_secret is not None:
            result["clientSecret"] = from_union([from_none, from_str], self.client_secret)
        if self.site_url is not None:
            result["siteUrl"] = from_union([from_none, from_str], self.site_url)
        if self.ssl_certificate_path is not None:
            result["sslCertificatePath"] = from_union([from_none, from_str], self.ssl_certificate_path)
        if self.user_agent is not None:
            result["userAgent"] = from_union([from_none, from_str], self.user_agent)
        return result


@dataclass
class AwsIamAuthLoginClass:
    identity_id: str
    """The Infisical Identity ID that you want to authenticate to Infisical with."""

    @staticmethod
    def from_dict(obj: Any) -> 'AwsIamAuthLoginClass':
        assert isinstance(obj, dict)
        identity_id = from_str(obj.get("identityId"))
        return AwsIamAuthLoginClass(identity_id)

    def to_dict(self) -> dict:
        result: dict = {}
        result["identityId"] = from_str(self.identity_id)
        return result


@dataclass
class AzureAuthLoginClass:
    identity_id: str
    """The Infisical Identity ID that you want to authenticate to Infisical with."""

    @staticmethod
    def from_dict(obj: Any) -> 'AzureAuthLoginClass':
        assert isinstance(obj, dict)
        identity_id = from_str(obj.get("identityId"))
        return AzureAuthLoginClass(identity_id)

    def to_dict(self) -> dict:
        result: dict = {}
        result["identityId"] = from_str(self.identity_id)
        return result


@dataclass
class CreateSecretOptions:
    environment: str
    project_id: str
    secret_name: str
    secret_value: str
    path: Optional[str] = None
    secret_comment: Optional[str] = None
    skip_multiline_encoding: Optional[bool] = None
    type: Optional[str] = None

    @staticmethod
    def from_dict(obj: Any) -> 'CreateSecretOptions':
        assert isinstance(obj, dict)
        environment = from_str(obj.get("environment"))
        project_id = from_str(obj.get("projectId"))
        secret_name = from_str(obj.get("secretName"))
        secret_value = from_str(obj.get("secretValue"))
        path = from_union([from_none, from_str], obj.get("path"))
        secret_comment = from_union([from_none, from_str], obj.get("secretComment"))
        skip_multiline_encoding = from_union([from_none, from_bool], obj.get("skipMultilineEncoding"))
        type = from_union([from_none, from_str], obj.get("type"))
        return CreateSecretOptions(environment, project_id, secret_name, secret_value, path, secret_comment, skip_multiline_encoding, type)

    def to_dict(self) -> dict:
        result: dict = {}
        result["environment"] = from_str(self.environment)
        result["projectId"] = from_str(self.project_id)
        result["secretName"] = from_str(self.secret_name)
        result["secretValue"] = from_str(self.secret_value)
        if self.path is not None:
            result["path"] = from_union([from_none, from_str], self.path)
        if self.secret_comment is not None:
            result["secretComment"] = from_union([from_none, from_str], self.secret_comment)
        if self.skip_multiline_encoding is not None:
            result["skipMultilineEncoding"] = from_union([from_none, from_bool], self.skip_multiline_encoding)
        if self.type is not None:
            result["type"] = from_union([from_none, from_str], self.type)
        return result


@dataclass
class ArbitraryOptions:
    data: str

    @staticmethod
    def from_dict(obj: Any) -> 'ArbitraryOptions':
        assert isinstance(obj, dict)
        data = from_str(obj.get("data"))
        return ArbitraryOptions(data)

    def to_dict(self) -> dict:
        result: dict = {}
        result["data"] = from_str(self.data)
        return result


@dataclass
class DecryptSymmetricOptions:
    ciphertext: str
    iv: str
    key: str
    tag: str

    @staticmethod
    def from_dict(obj: Any) -> 'DecryptSymmetricOptions':
        assert isinstance(obj, dict)
        ciphertext = from_str(obj.get("ciphertext"))
        iv = from_str(obj.get("iv"))
        key = from_str(obj.get("key"))
        tag = from_str(obj.get("tag"))
        return DecryptSymmetricOptions(ciphertext, iv, key, tag)

    def to_dict(self) -> dict:
        result: dict = {}
        result["ciphertext"] = from_str(self.ciphertext)
        result["iv"] = from_str(self.iv)
        result["key"] = from_str(self.key)
        result["tag"] = from_str(self.tag)
        return result


@dataclass
class DeleteSecretOptions:
    environment: str
    project_id: str
    secret_name: str
    path: Optional[str] = None
    type: Optional[str] = None

    @staticmethod
    def from_dict(obj: Any) -> 'DeleteSecretOptions':
        assert isinstance(obj, dict)
        environment = from_str(obj.get("environment"))
        project_id = from_str(obj.get("projectId"))
        secret_name = from_str(obj.get("secretName"))
        path = from_union([from_none, from_str], obj.get("path"))
        type = from_union([from_none, from_str], obj.get("type"))
        return DeleteSecretOptions(environment, project_id, secret_name, path, type)

    def to_dict(self) -> dict:
        result: dict = {}
        result["environment"] = from_str(self.environment)
        result["projectId"] = from_str(self.project_id)
        result["secretName"] = from_str(self.secret_name)
        if self.path is not None:
            result["path"] = from_union([from_none, from_str], self.path)
        if self.type is not None:
            result["type"] = from_union([from_none, from_str], self.type)
        return result


@dataclass
class EncryptSymmetricOptions:
    key: str
    plaintext: str

    @staticmethod
    def from_dict(obj: Any) -> 'EncryptSymmetricOptions':
        assert isinstance(obj, dict)
        key = from_str(obj.get("key"))
        plaintext = from_str(obj.get("plaintext"))
        return EncryptSymmetricOptions(key, plaintext)

    def to_dict(self) -> dict:
        result: dict = {}
        result["key"] = from_str(self.key)
        result["plaintext"] = from_str(self.plaintext)
        return result


@dataclass
class GcpIamAuthLoginClass:
    identity_id: str
    service_account_key_file_path: str
    """The path to the GCP Service Account key file.
    
    You can generate this key file by going to the GCP Console -> IAM & Admin -> Service
    Accounts -> *Select your service account* -> Keys tab -> Add key.
    Note: The key must be in JSON format.
    """

    @staticmethod
    def from_dict(obj: Any) -> 'GcpIamAuthLoginClass':
        assert isinstance(obj, dict)
        identity_id = from_str(obj.get("identityId"))
        service_account_key_file_path = from_str(obj.get("serviceAccountKeyFilePath"))
        return GcpIamAuthLoginClass(identity_id, service_account_key_file_path)

    def to_dict(self) -> dict:
        result: dict = {}
        result["identityId"] = from_str(self.identity_id)
        result["serviceAccountKeyFilePath"] = from_str(self.service_account_key_file_path)
        return result


@dataclass
class GcpIDTokenAuthLoginClass:
    identity_id: str

    @staticmethod
    def from_dict(obj: Any) -> 'GcpIDTokenAuthLoginClass':
        assert isinstance(obj, dict)
        identity_id = from_str(obj.get("identityId"))
        return GcpIDTokenAuthLoginClass(identity_id)

    def to_dict(self) -> dict:
        result: dict = {}
        result["identityId"] = from_str(self.identity_id)
        return result


@dataclass
class GetSecretOptions:
    environment: str
    project_id: str
    secret_name: str
    expand_secret_references: Optional[bool] = None
    include_imports: Optional[bool] = None
    path: Optional[str] = None
    type: Optional[str] = None

    @staticmethod
    def from_dict(obj: Any) -> 'GetSecretOptions':
        assert isinstance(obj, dict)
        environment = from_str(obj.get("environment"))
        project_id = from_str(obj.get("projectId"))
        secret_name = from_str(obj.get("secretName"))
        expand_secret_references = from_union([from_none, from_bool], obj.get("expandSecretReferences"))
        include_imports = from_union([from_none, from_bool], obj.get("includeImports"))
        path = from_union([from_none, from_str], obj.get("path"))
        type = from_union([from_none, from_str], obj.get("type"))
        return GetSecretOptions(environment, project_id, secret_name, expand_secret_references, include_imports, path, type)

    def to_dict(self) -> dict:
        result: dict = {}
        result["environment"] = from_str(self.environment)
        result["projectId"] = from_str(self.project_id)
        result["secretName"] = from_str(self.secret_name)
        if self.expand_secret_references is not None:
            result["expandSecretReferences"] = from_union([from_none, from_bool], self.expand_secret_references)
        if self.include_imports is not None:
            result["includeImports"] = from_union([from_none, from_bool], self.include_imports)
        if self.path is not None:
            result["path"] = from_union([from_none, from_str], self.path)
        if self.type is not None:
            result["type"] = from_union([from_none, from_str], self.type)
        return result


@dataclass
class KubernetesAuthLoginClass:
    identity_id: str
    """The Infisical Identity ID that you want to authenticate to Infisical with."""
    service_account_token_path: Optional[str] = None
    """The path to the Kubernetes Service Account token file.
    
    If no path is provided, it will default to
    /var/run/secrets/kubernetes.io/serviceaccount/token.
    """

    @staticmethod
    def from_dict(obj: Any) -> 'KubernetesAuthLoginClass':
        assert isinstance(obj, dict)
        identity_id = from_str(obj.get("identityId"))
        service_account_token_path = from_union([from_none, from_str], obj.get("serviceAccountTokenPath"))
        return KubernetesAuthLoginClass(identity_id, service_account_token_path)

    def to_dict(self) -> dict:
        result: dict = {}
        result["identityId"] = from_str(self.identity_id)
        if self.service_account_token_path is not None:
            result["serviceAccountTokenPath"] = from_union([from_none, from_str], self.service_account_token_path)
        return result


@dataclass
class ListSecretsOptions:
    environment: str
    project_id: str
    attach_to_process_env: Optional[bool] = None
    expand_secret_references: Optional[bool] = None
    include_imports: Optional[bool] = None
    path: Optional[str] = None
    recursive: Optional[bool] = None

    @staticmethod
    def from_dict(obj: Any) -> 'ListSecretsOptions':
        assert isinstance(obj, dict)
        environment = from_str(obj.get("environment"))
        project_id = from_str(obj.get("projectId"))
        attach_to_process_env = from_union([from_none, from_bool], obj.get("attachToProcessEnv"))
        expand_secret_references = from_union([from_none, from_bool], obj.get("expandSecretReferences"))
        include_imports = from_union([from_none, from_bool], obj.get("includeImports"))
        path = from_union([from_none, from_str], obj.get("path"))
        recursive = from_union([from_none, from_bool], obj.get("recursive"))
        return ListSecretsOptions(environment, project_id, attach_to_process_env, expand_secret_references, include_imports, path, recursive)

    def to_dict(self) -> dict:
        result: dict = {}
        result["environment"] = from_str(self.environment)
        result["projectId"] = from_str(self.project_id)
        if self.attach_to_process_env is not None:
            result["attachToProcessEnv"] = from_union([from_none, from_bool], self.attach_to_process_env)
        if self.expand_secret_references is not None:
            result["expandSecretReferences"] = from_union([from_none, from_bool], self.expand_secret_references)
        if self.include_imports is not None:
            result["includeImports"] = from_union([from_none, from_bool], self.include_imports)
        if self.path is not None:
            result["path"] = from_union([from_none, from_str], self.path)
        if self.recursive is not None:
            result["recursive"] = from_union([from_none, from_bool], self.recursive)
        return result


@dataclass
class UniversalAuthLoginClass:
    client_id: str
    client_secret: str

    @staticmethod
    def from_dict(obj: Any) -> 'UniversalAuthLoginClass':
        assert isinstance(obj, dict)
        client_id = from_str(obj.get("clientId"))
        client_secret = from_str(obj.get("clientSecret"))
        return UniversalAuthLoginClass(client_id, client_secret)

    def to_dict(self) -> dict:
        result: dict = {}
        result["clientId"] = from_str(self.client_id)
        result["clientSecret"] = from_str(self.client_secret)
        return result


@dataclass
class UpdateSecretOptions:
    environment: str
    project_id: str
    secret_name: str
    secret_value: str
    path: Optional[str] = None
    skip_multiline_encoding: Optional[bool] = None
    type: Optional[str] = None

    @staticmethod
    def from_dict(obj: Any) -> 'UpdateSecretOptions':
        assert isinstance(obj, dict)
        environment = from_str(obj.get("environment"))
        project_id = from_str(obj.get("projectId"))
        secret_name = from_str(obj.get("secretName"))
        secret_value = from_str(obj.get("secretValue"))
        path = from_union([from_none, from_str], obj.get("path"))
        skip_multiline_encoding = from_union([from_none, from_bool], obj.get("skipMultilineEncoding"))
        type = from_union([from_none, from_str], obj.get("type"))
        return UpdateSecretOptions(environment, project_id, secret_name, secret_value, path, skip_multiline_encoding, type)

    def to_dict(self) -> dict:
        result: dict = {}
        result["environment"] = from_str(self.environment)
        result["projectId"] = from_str(self.project_id)
        result["secretName"] = from_str(self.secret_name)
        result["secretValue"] = from_str(self.secret_value)
        if self.path is not None:
            result["path"] = from_union([from_none, from_str], self.path)
        if self.skip_multiline_encoding is not None:
            result["skipMultilineEncoding"] = from_union([from_none, from_bool], self.skip_multiline_encoding)
        if self.type is not None:
            result["type"] = from_union([from_none, from_str], self.type)
        return result


@dataclass
class Command:
    get_secret: Optional[GetSecretOptions] = None
    list_secrets: Optional[ListSecretsOptions] = None
    create_secret: Optional[CreateSecretOptions] = None
    update_secret: Optional[UpdateSecretOptions] = None
    delete_secret: Optional[DeleteSecretOptions] = None
    create_symmetric_key: Optional[ArbitraryOptions] = None
    encrypt_symmetric: Optional[EncryptSymmetricOptions] = None
    decrypt_symmetric: Optional[DecryptSymmetricOptions] = None
    universal_auth_login: Optional[UniversalAuthLoginClass] = None
    kubernetes_auth_login: Optional[KubernetesAuthLoginClass] = None
    azure_auth_login: Optional[AzureAuthLoginClass] = None
    gcp_id_token_auth_login: Optional[GcpIDTokenAuthLoginClass] = None
    gcp_iam_auth_login: Optional[GcpIamAuthLoginClass] = None
    aws_iam_auth_login: Optional[AwsIamAuthLoginClass] = None

    @staticmethod
    def from_dict(obj: Any) -> 'Command':
        assert isinstance(obj, dict)
        get_secret = from_union([GetSecretOptions.from_dict, from_none], obj.get("getSecret"))
        list_secrets = from_union([ListSecretsOptions.from_dict, from_none], obj.get("listSecrets"))
        create_secret = from_union([CreateSecretOptions.from_dict, from_none], obj.get("createSecret"))
        update_secret = from_union([UpdateSecretOptions.from_dict, from_none], obj.get("updateSecret"))
        delete_secret = from_union([DeleteSecretOptions.from_dict, from_none], obj.get("deleteSecret"))
        create_symmetric_key = from_union([ArbitraryOptions.from_dict, from_none], obj.get("createSymmetricKey"))
        encrypt_symmetric = from_union([EncryptSymmetricOptions.from_dict, from_none], obj.get("encryptSymmetric"))
        decrypt_symmetric = from_union([DecryptSymmetricOptions.from_dict, from_none], obj.get("decryptSymmetric"))
        universal_auth_login = from_union([UniversalAuthLoginClass.from_dict, from_none], obj.get("universalAuthLogin"))
        kubernetes_auth_login = from_union([KubernetesAuthLoginClass.from_dict, from_none], obj.get("kubernetesAuthLogin"))
        azure_auth_login = from_union([AzureAuthLoginClass.from_dict, from_none], obj.get("azureAuthLogin"))
        gcp_id_token_auth_login = from_union([GcpIDTokenAuthLoginClass.from_dict, from_none], obj.get("gcpIdTokenAuthLogin"))
        gcp_iam_auth_login = from_union([GcpIamAuthLoginClass.from_dict, from_none], obj.get("gcpIamAuthLogin"))
        aws_iam_auth_login = from_union([AwsIamAuthLoginClass.from_dict, from_none], obj.get("awsIamAuthLogin"))
        return Command(get_secret, list_secrets, create_secret, update_secret, delete_secret, create_symmetric_key, encrypt_symmetric, decrypt_symmetric, universal_auth_login, kubernetes_auth_login, azure_auth_login, gcp_id_token_auth_login, gcp_iam_auth_login, aws_iam_auth_login)

    def to_dict(self) -> dict:
        result: dict = {}
        if self.get_secret is not None:
            result["getSecret"] = from_union([lambda x: to_class(GetSecretOptions, x), from_none], self.get_secret)
        if self.list_secrets is not None:
            result["listSecrets"] = from_union([lambda x: to_class(ListSecretsOptions, x), from_none], self.list_secrets)
        if self.create_secret is not None:
            result["createSecret"] = from_union([lambda x: to_class(CreateSecretOptions, x), from_none], self.create_secret)
        if self.update_secret is not None:
            result["updateSecret"] = from_union([lambda x: to_class(UpdateSecretOptions, x), from_none], self.update_secret)
        if self.delete_secret is not None:
            result["deleteSecret"] = from_union([lambda x: to_class(DeleteSecretOptions, x), from_none], self.delete_secret)
        if self.create_symmetric_key is not None:
            result["createSymmetricKey"] = from_union([lambda x: to_class(ArbitraryOptions, x), from_none], self.create_symmetric_key)
        if self.encrypt_symmetric is not None:
            result["encryptSymmetric"] = from_union([lambda x: to_class(EncryptSymmetricOptions, x), from_none], self.encrypt_symmetric)
        if self.decrypt_symmetric is not None:
            result["decryptSymmetric"] = from_union([lambda x: to_class(DecryptSymmetricOptions, x), from_none], self.decrypt_symmetric)
        if self.universal_auth_login is not None:
            result["universalAuthLogin"] = from_union([lambda x: to_class(UniversalAuthLoginClass, x), from_none], self.universal_auth_login)
        if self.kubernetes_auth_login is not None:
            result["kubernetesAuthLogin"] = from_union([lambda x: to_class(KubernetesAuthLoginClass, x), from_none], self.kubernetes_auth_login)
        if self.azure_auth_login is not None:
            result["azureAuthLogin"] = from_union([lambda x: to_class(AzureAuthLoginClass, x), from_none], self.azure_auth_login)
        if self.gcp_id_token_auth_login is not None:
            result["gcpIdTokenAuthLogin"] = from_union([lambda x: to_class(GcpIDTokenAuthLoginClass, x), from_none], self.gcp_id_token_auth_login)
        if self.gcp_iam_auth_login is not None:
            result["gcpIamAuthLogin"] = from_union([lambda x: to_class(GcpIamAuthLoginClass, x), from_none], self.gcp_iam_auth_login)
        if self.aws_iam_auth_login is not None:
            result["awsIamAuthLogin"] = from_union([lambda x: to_class(AwsIamAuthLoginClass, x), from_none], self.aws_iam_auth_login)
        return result


@dataclass
class AccessTokenSuccessResponse:
    access_token: str
    access_token_max_ttl: int
    expires_in: int
    token_type: str

    @staticmethod
    def from_dict(obj: Any) -> 'AccessTokenSuccessResponse':
        assert isinstance(obj, dict)
        access_token = from_str(obj.get("accessToken"))
        access_token_max_ttl = from_int(obj.get("accessTokenMaxTTL"))
        expires_in = from_int(obj.get("expiresIn"))
        token_type = from_str(obj.get("tokenType"))
        return AccessTokenSuccessResponse(access_token, access_token_max_ttl, expires_in, token_type)

    def to_dict(self) -> dict:
        result: dict = {}
        result["accessToken"] = from_str(self.access_token)
        result["accessTokenMaxTTL"] = from_int(self.access_token_max_ttl)
        result["expiresIn"] = from_int(self.expires_in)
        result["tokenType"] = from_str(self.token_type)
        return result


@dataclass
class ResponseForAccessTokenSuccessResponse:
    success: bool
    """Whether or not the SDK request succeeded."""
    data: Optional[AccessTokenSuccessResponse] = None
    """The response data. Populated if `success` is true."""
    error_message: Optional[str] = None
    """A message for any error that may occur. Populated if `success` is false."""

    @staticmethod
    def from_dict(obj: Any) -> 'ResponseForAccessTokenSuccessResponse':
        assert isinstance(obj, dict)
        success = from_bool(obj.get("success"))
        data = from_union([AccessTokenSuccessResponse.from_dict, from_none], obj.get("data"))
        error_message = from_union([from_none, from_str], obj.get("errorMessage"))
        return ResponseForAccessTokenSuccessResponse(success, data, error_message)

    def to_dict(self) -> dict:
        result: dict = {}
        result["success"] = from_bool(self.success)
        if self.data is not None:
            result["data"] = from_union([lambda x: to_class(AccessTokenSuccessResponse, x), from_none], self.data)
        if self.error_message is not None:
            result["errorMessage"] = from_union([from_none, from_str], self.error_message)
        return result


@dataclass
class CreateSecretResponseSecret:
    environment: str
    secret_comment: str
    secret_key: str
    secret_value: str
    type: str
    version: int
    workspace: str
    is_fallback: Optional[bool] = None
    secret_path: Optional[str] = None
    """The path of the secret.
    
    Note that this will only be present when using the `list secrets` method.
    """

    @staticmethod
    def from_dict(obj: Any) -> 'CreateSecretResponseSecret':
        assert isinstance(obj, dict)
        environment = from_str(obj.get("environment"))
        secret_comment = from_str(obj.get("secretComment"))
        secret_key = from_str(obj.get("secretKey"))
        secret_value = from_str(obj.get("secretValue"))
        type = from_str(obj.get("type"))
        version = from_int(obj.get("version"))
        workspace = from_str(obj.get("workspace"))
        is_fallback = from_union([from_none, from_bool], obj.get("isFallback"))
        secret_path = from_union([from_none, from_str], obj.get("secretPath"))
        return CreateSecretResponseSecret(environment, secret_comment, secret_key, secret_value, type, version, workspace, is_fallback, secret_path)

    def to_dict(self) -> dict:
        result: dict = {}
        result["environment"] = from_str(self.environment)
        result["secretComment"] = from_str(self.secret_comment)
        result["secretKey"] = from_str(self.secret_key)
        result["secretValue"] = from_str(self.secret_value)
        result["type"] = from_str(self.type)
        result["version"] = from_int(self.version)
        result["workspace"] = from_str(self.workspace)
        if self.is_fallback is not None:
            result["isFallback"] = from_union([from_none, from_bool], self.is_fallback)
        if self.secret_path is not None:
            result["secretPath"] = from_union([from_none, from_str], self.secret_path)
        return result


@dataclass
class CreateSecretResponse:
    secret: CreateSecretResponseSecret

    @staticmethod
    def from_dict(obj: Any) -> 'CreateSecretResponse':
        assert isinstance(obj, dict)
        secret = CreateSecretResponseSecret.from_dict(obj.get("secret"))
        return CreateSecretResponse(secret)

    def to_dict(self) -> dict:
        result: dict = {}
        result["secret"] = to_class(CreateSecretResponseSecret, self.secret)
        return result


@dataclass
class ResponseForCreateSecretResponse:
    success: bool
    """Whether or not the SDK request succeeded."""
    data: Optional[CreateSecretResponse] = None
    """The response data. Populated if `success` is true."""
    error_message: Optional[str] = None
    """A message for any error that may occur. Populated if `success` is false."""

    @staticmethod
    def from_dict(obj: Any) -> 'ResponseForCreateSecretResponse':
        assert isinstance(obj, dict)
        success = from_bool(obj.get("success"))
        data = from_union([CreateSecretResponse.from_dict, from_none], obj.get("data"))
        error_message = from_union([from_none, from_str], obj.get("errorMessage"))
        return ResponseForCreateSecretResponse(success, data, error_message)

    def to_dict(self) -> dict:
        result: dict = {}
        result["success"] = from_bool(self.success)
        if self.data is not None:
            result["data"] = from_union([lambda x: to_class(CreateSecretResponse, x), from_none], self.data)
        if self.error_message is not None:
            result["errorMessage"] = from_union([from_none, from_str], self.error_message)
        return result


@dataclass
class CreateSymmetricKeyResponse:
    key: str

    @staticmethod
    def from_dict(obj: Any) -> 'CreateSymmetricKeyResponse':
        assert isinstance(obj, dict)
        key = from_str(obj.get("key"))
        return CreateSymmetricKeyResponse(key)

    def to_dict(self) -> dict:
        result: dict = {}
        result["key"] = from_str(self.key)
        return result


@dataclass
class ResponseForCreateSymmetricKeyResponse:
    success: bool
    """Whether or not the SDK request succeeded."""
    data: Optional[CreateSymmetricKeyResponse] = None
    """The response data. Populated if `success` is true."""
    error_message: Optional[str] = None
    """A message for any error that may occur. Populated if `success` is false."""

    @staticmethod
    def from_dict(obj: Any) -> 'ResponseForCreateSymmetricKeyResponse':
        assert isinstance(obj, dict)
        success = from_bool(obj.get("success"))
        data = from_union([CreateSymmetricKeyResponse.from_dict, from_none], obj.get("data"))
        error_message = from_union([from_none, from_str], obj.get("errorMessage"))
        return ResponseForCreateSymmetricKeyResponse(success, data, error_message)

    def to_dict(self) -> dict:
        result: dict = {}
        result["success"] = from_bool(self.success)
        if self.data is not None:
            result["data"] = from_union([lambda x: to_class(CreateSymmetricKeyResponse, x), from_none], self.data)
        if self.error_message is not None:
            result["errorMessage"] = from_union([from_none, from_str], self.error_message)
        return result


@dataclass
class DecryptSymmetricResponse:
    decrypted: str

    @staticmethod
    def from_dict(obj: Any) -> 'DecryptSymmetricResponse':
        assert isinstance(obj, dict)
        decrypted = from_str(obj.get("decrypted"))
        return DecryptSymmetricResponse(decrypted)

    def to_dict(self) -> dict:
        result: dict = {}
        result["decrypted"] = from_str(self.decrypted)
        return result


@dataclass
class ResponseForDecryptSymmetricResponse:
    success: bool
    """Whether or not the SDK request succeeded."""
    data: Optional[DecryptSymmetricResponse] = None
    """The response data. Populated if `success` is true."""
    error_message: Optional[str] = None
    """A message for any error that may occur. Populated if `success` is false."""

    @staticmethod
    def from_dict(obj: Any) -> 'ResponseForDecryptSymmetricResponse':
        assert isinstance(obj, dict)
        success = from_bool(obj.get("success"))
        data = from_union([DecryptSymmetricResponse.from_dict, from_none], obj.get("data"))
        error_message = from_union([from_none, from_str], obj.get("errorMessage"))
        return ResponseForDecryptSymmetricResponse(success, data, error_message)

    def to_dict(self) -> dict:
        result: dict = {}
        result["success"] = from_bool(self.success)
        if self.data is not None:
            result["data"] = from_union([lambda x: to_class(DecryptSymmetricResponse, x), from_none], self.data)
        if self.error_message is not None:
            result["errorMessage"] = from_union([from_none, from_str], self.error_message)
        return result


@dataclass
class DeleteSecretResponseSecret:
    environment: str
    secret_comment: str
    secret_key: str
    secret_value: str
    type: str
    version: int
    workspace: str
    is_fallback: Optional[bool] = None
    secret_path: Optional[str] = None
    """The path of the secret.
    
    Note that this will only be present when using the `list secrets` method.
    """

    @staticmethod
    def from_dict(obj: Any) -> 'DeleteSecretResponseSecret':
        assert isinstance(obj, dict)
        environment = from_str(obj.get("environment"))
        secret_comment = from_str(obj.get("secretComment"))
        secret_key = from_str(obj.get("secretKey"))
        secret_value = from_str(obj.get("secretValue"))
        type = from_str(obj.get("type"))
        version = from_int(obj.get("version"))
        workspace = from_str(obj.get("workspace"))
        is_fallback = from_union([from_none, from_bool], obj.get("isFallback"))
        secret_path = from_union([from_none, from_str], obj.get("secretPath"))
        return DeleteSecretResponseSecret(environment, secret_comment, secret_key, secret_value, type, version, workspace, is_fallback, secret_path)

    def to_dict(self) -> dict:
        result: dict = {}
        result["environment"] = from_str(self.environment)
        result["secretComment"] = from_str(self.secret_comment)
        result["secretKey"] = from_str(self.secret_key)
        result["secretValue"] = from_str(self.secret_value)
        result["type"] = from_str(self.type)
        result["version"] = from_int(self.version)
        result["workspace"] = from_str(self.workspace)
        if self.is_fallback is not None:
            result["isFallback"] = from_union([from_none, from_bool], self.is_fallback)
        if self.secret_path is not None:
            result["secretPath"] = from_union([from_none, from_str], self.secret_path)
        return result


@dataclass
class DeleteSecretResponse:
    secret: DeleteSecretResponseSecret

    @staticmethod
    def from_dict(obj: Any) -> 'DeleteSecretResponse':
        assert isinstance(obj, dict)
        secret = DeleteSecretResponseSecret.from_dict(obj.get("secret"))
        return DeleteSecretResponse(secret)

    def to_dict(self) -> dict:
        result: dict = {}
        result["secret"] = to_class(DeleteSecretResponseSecret, self.secret)
        return result


@dataclass
class ResponseForDeleteSecretResponse:
    success: bool
    """Whether or not the SDK request succeeded."""
    data: Optional[DeleteSecretResponse] = None
    """The response data. Populated if `success` is true."""
    error_message: Optional[str] = None
    """A message for any error that may occur. Populated if `success` is false."""

    @staticmethod
    def from_dict(obj: Any) -> 'ResponseForDeleteSecretResponse':
        assert isinstance(obj, dict)
        success = from_bool(obj.get("success"))
        data = from_union([DeleteSecretResponse.from_dict, from_none], obj.get("data"))
        error_message = from_union([from_none, from_str], obj.get("errorMessage"))
        return ResponseForDeleteSecretResponse(success, data, error_message)

    def to_dict(self) -> dict:
        result: dict = {}
        result["success"] = from_bool(self.success)
        if self.data is not None:
            result["data"] = from_union([lambda x: to_class(DeleteSecretResponse, x), from_none], self.data)
        if self.error_message is not None:
            result["errorMessage"] = from_union([from_none, from_str], self.error_message)
        return result


@dataclass
class EncryptSymmetricResponse:
    ciphertext: str
    iv: str
    tag: str

    @staticmethod
    def from_dict(obj: Any) -> 'EncryptSymmetricResponse':
        assert isinstance(obj, dict)
        ciphertext = from_str(obj.get("ciphertext"))
        iv = from_str(obj.get("iv"))
        tag = from_str(obj.get("tag"))
        return EncryptSymmetricResponse(ciphertext, iv, tag)

    def to_dict(self) -> dict:
        result: dict = {}
        result["ciphertext"] = from_str(self.ciphertext)
        result["iv"] = from_str(self.iv)
        result["tag"] = from_str(self.tag)
        return result


@dataclass
class ResponseForEncryptSymmetricResponse:
    success: bool
    """Whether or not the SDK request succeeded."""
    data: Optional[EncryptSymmetricResponse] = None
    """The response data. Populated if `success` is true."""
    error_message: Optional[str] = None
    """A message for any error that may occur. Populated if `success` is false."""

    @staticmethod
    def from_dict(obj: Any) -> 'ResponseForEncryptSymmetricResponse':
        assert isinstance(obj, dict)
        success = from_bool(obj.get("success"))
        data = from_union([EncryptSymmetricResponse.from_dict, from_none], obj.get("data"))
        error_message = from_union([from_none, from_str], obj.get("errorMessage"))
        return ResponseForEncryptSymmetricResponse(success, data, error_message)

    def to_dict(self) -> dict:
        result: dict = {}
        result["success"] = from_bool(self.success)
        if self.data is not None:
            result["data"] = from_union([lambda x: to_class(EncryptSymmetricResponse, x), from_none], self.data)
        if self.error_message is not None:
            result["errorMessage"] = from_union([from_none, from_str], self.error_message)
        return result


@dataclass
class GetSecretResponseSecret:
    environment: str
    secret_comment: str
    secret_key: str
    secret_value: str
    type: str
    version: int
    workspace: str
    is_fallback: Optional[bool] = None
    secret_path: Optional[str] = None
    """The path of the secret.
    
    Note that this will only be present when using the `list secrets` method.
    """

    @staticmethod
    def from_dict(obj: Any) -> 'GetSecretResponseSecret':
        assert isinstance(obj, dict)
        environment = from_str(obj.get("environment"))
        secret_comment = from_str(obj.get("secretComment"))
        secret_key = from_str(obj.get("secretKey"))
        secret_value = from_str(obj.get("secretValue"))
        type = from_str(obj.get("type"))
        version = from_int(obj.get("version"))
        workspace = from_str(obj.get("workspace"))
        is_fallback = from_union([from_none, from_bool], obj.get("isFallback"))
        secret_path = from_union([from_none, from_str], obj.get("secretPath"))
        return GetSecretResponseSecret(environment, secret_comment, secret_key, secret_value, type, version, workspace, is_fallback, secret_path)

    def to_dict(self) -> dict:
        result: dict = {}
        result["environment"] = from_str(self.environment)
        result["secretComment"] = from_str(self.secret_comment)
        result["secretKey"] = from_str(self.secret_key)
        result["secretValue"] = from_str(self.secret_value)
        result["type"] = from_str(self.type)
        result["version"] = from_int(self.version)
        result["workspace"] = from_str(self.workspace)
        if self.is_fallback is not None:
            result["isFallback"] = from_union([from_none, from_bool], self.is_fallback)
        if self.secret_path is not None:
            result["secretPath"] = from_union([from_none, from_str], self.secret_path)
        return result


@dataclass
class GetSecretResponse:
    secret: GetSecretResponseSecret

    @staticmethod
    def from_dict(obj: Any) -> 'GetSecretResponse':
        assert isinstance(obj, dict)
        secret = GetSecretResponseSecret.from_dict(obj.get("secret"))
        return GetSecretResponse(secret)

    def to_dict(self) -> dict:
        result: dict = {}
        result["secret"] = to_class(GetSecretResponseSecret, self.secret)
        return result


@dataclass
class ResponseForGetSecretResponse:
    success: bool
    """Whether or not the SDK request succeeded."""
    data: Optional[GetSecretResponse] = None
    """The response data. Populated if `success` is true."""
    error_message: Optional[str] = None
    """A message for any error that may occur. Populated if `success` is false."""

    @staticmethod
    def from_dict(obj: Any) -> 'ResponseForGetSecretResponse':
        assert isinstance(obj, dict)
        success = from_bool(obj.get("success"))
        data = from_union([GetSecretResponse.from_dict, from_none], obj.get("data"))
        error_message = from_union([from_none, from_str], obj.get("errorMessage"))
        return ResponseForGetSecretResponse(success, data, error_message)

    def to_dict(self) -> dict:
        result: dict = {}
        result["success"] = from_bool(self.success)
        if self.data is not None:
            result["data"] = from_union([lambda x: to_class(GetSecretResponse, x), from_none], self.data)
        if self.error_message is not None:
            result["errorMessage"] = from_union([from_none, from_str], self.error_message)
        return result


@dataclass
class SecretElement:
    environment: str
    secret_comment: str
    secret_key: str
    secret_value: str
    type: str
    version: int
    workspace: str
    is_fallback: Optional[bool] = None
    secret_path: Optional[str] = None
    """The path of the secret.
    
    Note that this will only be present when using the `list secrets` method.
    """

    @staticmethod
    def from_dict(obj: Any) -> 'SecretElement':
        assert isinstance(obj, dict)
        environment = from_str(obj.get("environment"))
        secret_comment = from_str(obj.get("secretComment"))
        secret_key = from_str(obj.get("secretKey"))
        secret_value = from_str(obj.get("secretValue"))
        type = from_str(obj.get("type"))
        version = from_int(obj.get("version"))
        workspace = from_str(obj.get("workspace"))
        is_fallback = from_union([from_none, from_bool], obj.get("isFallback"))
        secret_path = from_union([from_none, from_str], obj.get("secretPath"))
        return SecretElement(environment, secret_comment, secret_key, secret_value, type, version, workspace, is_fallback, secret_path)

    def to_dict(self) -> dict:
        result: dict = {}
        result["environment"] = from_str(self.environment)
        result["secretComment"] = from_str(self.secret_comment)
        result["secretKey"] = from_str(self.secret_key)
        result["secretValue"] = from_str(self.secret_value)
        result["type"] = from_str(self.type)
        result["version"] = from_int(self.version)
        result["workspace"] = from_str(self.workspace)
        if self.is_fallback is not None:
            result["isFallback"] = from_union([from_none, from_bool], self.is_fallback)
        if self.secret_path is not None:
            result["secretPath"] = from_union([from_none, from_str], self.secret_path)
        return result


@dataclass
class ListSecretsResponse:
    secrets: List[SecretElement]

    @staticmethod
    def from_dict(obj: Any) -> 'ListSecretsResponse':
        assert isinstance(obj, dict)
        secrets = from_list(SecretElement.from_dict, obj.get("secrets"))
        return ListSecretsResponse(secrets)

    def to_dict(self) -> dict:
        result: dict = {}
        result["secrets"] = from_list(lambda x: to_class(SecretElement, x), self.secrets)
        return result


@dataclass
class ResponseForListSecretsResponse:
    success: bool
    """Whether or not the SDK request succeeded."""
    data: Optional[ListSecretsResponse] = None
    """The response data. Populated if `success` is true."""
    error_message: Optional[str] = None
    """A message for any error that may occur. Populated if `success` is false."""

    @staticmethod
    def from_dict(obj: Any) -> 'ResponseForListSecretsResponse':
        assert isinstance(obj, dict)
        success = from_bool(obj.get("success"))
        data = from_union([ListSecretsResponse.from_dict, from_none], obj.get("data"))
        error_message = from_union([from_none, from_str], obj.get("errorMessage"))
        return ResponseForListSecretsResponse(success, data, error_message)

    def to_dict(self) -> dict:
        result: dict = {}
        result["success"] = from_bool(self.success)
        if self.data is not None:
            result["data"] = from_union([lambda x: to_class(ListSecretsResponse, x), from_none], self.data)
        if self.error_message is not None:
            result["errorMessage"] = from_union([from_none, from_str], self.error_message)
        return result


@dataclass
class UpdateSecretResponseSecret:
    environment: str
    secret_comment: str
    secret_key: str
    secret_value: str
    type: str
    version: int
    workspace: str
    is_fallback: Optional[bool] = None
    secret_path: Optional[str] = None
    """The path of the secret.
    
    Note that this will only be present when using the `list secrets` method.
    """

    @staticmethod
    def from_dict(obj: Any) -> 'UpdateSecretResponseSecret':
        assert isinstance(obj, dict)
        environment = from_str(obj.get("environment"))
        secret_comment = from_str(obj.get("secretComment"))
        secret_key = from_str(obj.get("secretKey"))
        secret_value = from_str(obj.get("secretValue"))
        type = from_str(obj.get("type"))
        version = from_int(obj.get("version"))
        workspace = from_str(obj.get("workspace"))
        is_fallback = from_union([from_none, from_bool], obj.get("isFallback"))
        secret_path = from_union([from_none, from_str], obj.get("secretPath"))
        return UpdateSecretResponseSecret(environment, secret_comment, secret_key, secret_value, type, version, workspace, is_fallback, secret_path)

    def to_dict(self) -> dict:
        result: dict = {}
        result["environment"] = from_str(self.environment)
        result["secretComment"] = from_str(self.secret_comment)
        result["secretKey"] = from_str(self.secret_key)
        result["secretValue"] = from_str(self.secret_value)
        result["type"] = from_str(self.type)
        result["version"] = from_int(self.version)
        result["workspace"] = from_str(self.workspace)
        if self.is_fallback is not None:
            result["isFallback"] = from_union([from_none, from_bool], self.is_fallback)
        if self.secret_path is not None:
            result["secretPath"] = from_union([from_none, from_str], self.secret_path)
        return result


@dataclass
class UpdateSecretResponse:
    secret: UpdateSecretResponseSecret

    @staticmethod
    def from_dict(obj: Any) -> 'UpdateSecretResponse':
        assert isinstance(obj, dict)
        secret = UpdateSecretResponseSecret.from_dict(obj.get("secret"))
        return UpdateSecretResponse(secret)

    def to_dict(self) -> dict:
        result: dict = {}
        result["secret"] = to_class(UpdateSecretResponseSecret, self.secret)
        return result


@dataclass
class ResponseForUpdateSecretResponse:
    success: bool
    """Whether or not the SDK request succeeded."""
    data: Optional[UpdateSecretResponse] = None
    """The response data. Populated if `success` is true."""
    error_message: Optional[str] = None
    """A message for any error that may occur. Populated if `success` is false."""

    @staticmethod
    def from_dict(obj: Any) -> 'ResponseForUpdateSecretResponse':
        assert isinstance(obj, dict)
        success = from_bool(obj.get("success"))
        data = from_union([UpdateSecretResponse.from_dict, from_none], obj.get("data"))
        error_message = from_union([from_none, from_str], obj.get("errorMessage"))
        return ResponseForUpdateSecretResponse(success, data, error_message)

    def to_dict(self) -> dict:
        result: dict = {}
        result["success"] = from_bool(self.success)
        if self.data is not None:
            result["data"] = from_union([lambda x: to_class(UpdateSecretResponse, x), from_none], self.data)
        if self.error_message is not None:
            result["errorMessage"] = from_union([from_none, from_str], self.error_message)
        return result


def client_settings_from_dict(s: Any) -> ClientSettings:
    return ClientSettings.from_dict(s)


def client_settings_to_dict(x: ClientSettings) -> Any:
    return to_class(ClientSettings, x)


def command_from_dict(s: Any) -> Command:
    return Command.from_dict(s)


def command_to_dict(x: Command) -> Any:
    return to_class(Command, x)


def response_for_access_token_success_response_from_dict(s: Any) -> ResponseForAccessTokenSuccessResponse:
    return ResponseForAccessTokenSuccessResponse.from_dict(s)


def response_for_access_token_success_response_to_dict(x: ResponseForAccessTokenSuccessResponse) -> Any:
    return to_class(ResponseForAccessTokenSuccessResponse, x)


def response_for_create_secret_response_from_dict(s: Any) -> ResponseForCreateSecretResponse:
    return ResponseForCreateSecretResponse.from_dict(s)


def response_for_create_secret_response_to_dict(x: ResponseForCreateSecretResponse) -> Any:
    return to_class(ResponseForCreateSecretResponse, x)


def response_for_create_symmetric_key_response_from_dict(s: Any) -> ResponseForCreateSymmetricKeyResponse:
    return ResponseForCreateSymmetricKeyResponse.from_dict(s)


def response_for_create_symmetric_key_response_to_dict(x: ResponseForCreateSymmetricKeyResponse) -> Any:
    return to_class(ResponseForCreateSymmetricKeyResponse, x)


def response_for_decrypt_symmetric_response_from_dict(s: Any) -> ResponseForDecryptSymmetricResponse:
    return ResponseForDecryptSymmetricResponse.from_dict(s)


def response_for_decrypt_symmetric_response_to_dict(x: ResponseForDecryptSymmetricResponse) -> Any:
    return to_class(ResponseForDecryptSymmetricResponse, x)


def response_for_delete_secret_response_from_dict(s: Any) -> ResponseForDeleteSecretResponse:
    return ResponseForDeleteSecretResponse.from_dict(s)


def response_for_delete_secret_response_to_dict(x: ResponseForDeleteSecretResponse) -> Any:
    return to_class(ResponseForDeleteSecretResponse, x)


def response_for_encrypt_symmetric_response_from_dict(s: Any) -> ResponseForEncryptSymmetricResponse:
    return ResponseForEncryptSymmetricResponse.from_dict(s)


def response_for_encrypt_symmetric_response_to_dict(x: ResponseForEncryptSymmetricResponse) -> Any:
    return to_class(ResponseForEncryptSymmetricResponse, x)


def response_for_get_secret_response_from_dict(s: Any) -> ResponseForGetSecretResponse:
    return ResponseForGetSecretResponse.from_dict(s)


def response_for_get_secret_response_to_dict(x: ResponseForGetSecretResponse) -> Any:
    return to_class(ResponseForGetSecretResponse, x)


def response_for_list_secrets_response_from_dict(s: Any) -> ResponseForListSecretsResponse:
    return ResponseForListSecretsResponse.from_dict(s)


def response_for_list_secrets_response_to_dict(x: ResponseForListSecretsResponse) -> Any:
    return to_class(ResponseForListSecretsResponse, x)


def response_for_update_secret_response_from_dict(s: Any) -> ResponseForUpdateSecretResponse:
    return ResponseForUpdateSecretResponse.from_dict(s)


def response_for_update_secret_response_to_dict(x: ResponseForUpdateSecretResponse) -> Any:
    return to_class(ResponseForUpdateSecretResponse, x)

