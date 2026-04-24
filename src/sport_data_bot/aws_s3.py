"""S3 client for BetFair TLS client certificates."""

from __future__ import annotations

import os
import shutil

import boto3

S3_KEY_PREFIX = "sport-data-discord-bot"
AWS_REGION = "eu-west-1"


class AmazonS3:
    """Thin S3 wrapper that downloads BetFair TLS client certs at startup."""

    def __init__(self, certifications: str) -> None:
        """Build an S3 client and fetch the BetFair TLS certs into ``certifications``.

        Credentials are taken from the default boto3 chain (ECS task role in prod,
        env vars or ``~/.aws`` locally). Cert objects live under the
        ``sport-data-discord-bot/`` prefix inside the configured bucket.
        """
        self.s3 = boto3.client("s3", region_name=AWS_REGION)
        self.bucket_name = os.environ["AWS_BUCKET_NAME"]
        self._download_certs(certifications)

    def _prefixed_key(self, aws_filename: str) -> str:
        """Prefix a bucket-relative filename with the bot's namespace."""
        return f"{S3_KEY_PREFIX}/{aws_filename}"

    def _download_to_cwd(self, aws_filename: str, output_filename: str) -> None:
        """Download an S3 object to the working directory, replacing any existing file."""
        output_path = os.path.join(os.getcwd(), output_filename)
        if os.path.exists(output_path):
            os.remove(output_path)
        self.s3.download_file(self.bucket_name, self._prefixed_key(aws_filename), output_filename)

    def _download_certs(self, certifications: str) -> None:
        """Refresh the BetFair TLS client certificates into the given directory."""
        if os.path.exists(certifications):
            shutil.rmtree(certifications)
        os.mkdir(certifications)

        self._download_to_cwd("client-2048.crt", "client-2048.crt")
        self._download_to_cwd("client-2048.key", "client-2048.key")
        shutil.move(os.path.join(os.getcwd(), "client-2048.crt"), os.path.join(certifications, "client-2048.crt"))
        shutil.move(os.path.join(os.getcwd(), "client-2048.key"), os.path.join(certifications, "client-2048.key"))
