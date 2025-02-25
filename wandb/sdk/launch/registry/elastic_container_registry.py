"""Implementation of Elastic Container Registry class for wandb launch."""
import base64
import logging
from typing import Tuple

from wandb.sdk.launch.environment.aws_environment import AwsEnvironment
from wandb.sdk.launch.utils import LaunchError
from wandb.util import get_module

from .abstract import AbstractRegistry

botocore = get_module(
    "botocore",
    required="AWS environment requires botocore to be installed. Please install "
    "it with `pip install wandb[launch]`.",
)

_logger = logging.getLogger(__name__)


class ElasticContainerRegistry(AbstractRegistry):
    """Elastic Container Registry class.

    Attributes:
        repo_name (str): The name of the repository.
        environment (AwsEnvironment): The AWS environment.
        uri (str): The uri of the repository.
    """

    repo_name: str
    environment: AwsEnvironment
    uri: str

    def __init__(self, repo_name: str, environment: AwsEnvironment) -> None:
        """Initialize the Elastic Container Registry.

        Args:
            repo_name (str): The name of the repository.
            environment (AwsEnvironment): The AWS environment.

        Raises:
            LaunchError: If there is an error verifying the registry.
        """
        super().__init__()
        _logger.info(
            f"Initializing Elastic Container Registry with repotisory {repo_name}."
        )
        self.repo_name = repo_name
        self.environment = environment
        self.verify()

    def verify(self) -> None:
        """Verify that the registry is accessible and the configured repo exists.

        Raises:
            RegistryError: If there is an error verifying the registry.
        """
        _logger.debug("Verifying Elastic Container Registry.")
        try:
            session = self.environment.get_session()
            client = session.client("ecr")
            response = client.describe_registry()
            response = client.describe_repositories(repositoryNames=[self.repo_name])
            self.uri = response["repositories"][0]["repositoryUri"].split("/")[0]

        except botocore.exceptions.ClientError as e:
            code = e.response["Error"]["Code"]
            msg = e.response["Error"]["Message"]
            # TODO: Log the code and the message here?
            raise LaunchError(
                f"Error verifying Elastic Container Registry: {code} {msg}"
            )

    def get_username_password(self) -> Tuple[str, str]:
        """Get the username and password for the registry.

        Returns:
            (str, str): The username and password.

        Raises:
            RegistryError: If there is an error getting the username and password.
        """
        _logger.debug("Getting username and password for Elastic Container Registry.")
        try:
            session = self.environment.get_session()
            client = session.client("ecr")
            response = client.get_authorization_token()
            username, password = base64.standard_b64decode(
                response["authorizationData"][0]["authorizationToken"]
            ).split(b":")
            return username.decode("utf-8"), password.decode("utf-8")

        except botocore.exceptions.ClientError as e:
            code = e.response["Error"]["Code"]
            msg = e.response["Error"]["Message"]
            # TODO: Log the code and the message here?
            raise LaunchError(f"Error getting username and password: {code} {msg}")

    def get_repo_uri(self) -> str:
        """Get the uri of the repository.

        Returns:
            str: The uri of the repository.
        """
        return self.uri + "/" + self.repo_name
