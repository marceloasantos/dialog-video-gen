from typing import List

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

from src.domain.ports.storage import IStorage, IStoredFile
from src.domain.ports.presigned_url import IPresignedUrlProvider
from src.infrastructure.services.environment_service import (
    AWS_ENDPOINT_URL_S3,
    AWS_REGION,
    AWS_ACCESS_KEY_ID,
    AWS_SECRET_ACCESS_KEY,
)


def _build_s3_client():
    return boto3.client(
        "s3",
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        endpoint_url=AWS_ENDPOINT_URL_S3,
        region_name=AWS_REGION,
        config=Config(s3={"addressing_style": "virtual"}),
    )


class TigrisStoredFile(IStoredFile):
    def __init__(self, bucket_name: str, key: str, client):
        self._bucket = bucket_name
        self._key = key.lstrip("/\\")
        self._client = client

    @property
    def relative_path(self) -> str:
        return self._key

    def write_bytes(self, data: bytes) -> None:
        self._client.put_object(Bucket=self._bucket, Key=self._key, Body=data)

    def read_bytes(self) -> bytes:
        try:
            resp = self._client.get_object(Bucket=self._bucket, Key=self._key)
            return resp["Body"].read()
        except ClientError as e:
            if e.response.get("ResponseMetadata", {}).get(
                "HTTPStatusCode"
            ) == 404 or e.response.get("Error", {}).get("Code") in {"404", "NoSuchKey"}:
                raise FileNotFoundError(
                    f"Object not found: s3://{self._bucket}/{self._key}"
                ) from e
            raise

    def write_text(self, text: str, encoding: str = "utf-8") -> None:
        self.write_bytes(text.encode(encoding))

    def read_text(self, encoding: str = "utf-8") -> str:
        return self.read_bytes().decode(encoding)

    def exists(self) -> bool:
        try:
            self._client.head_object(Bucket=self._bucket, Key=self._key)
            return True
        except ClientError as e:
            code = e.response.get("Error", {}).get("Code")
            if code in {"404", "NotFound", "NoSuchKey"}:
                return False
            return False

    def delete(self) -> None:
        self._client.delete_object(Bucket=self._bucket, Key=self._key)


class TigrisS3Storage(IStorage, IPresignedUrlProvider):
    def __init__(self, bucket_name: str):
        self._bucket = bucket_name
        self._client = _build_s3_client()

    def file(self, relative_path: str) -> IStoredFile:
        return TigrisStoredFile(self._bucket, relative_path, self._client)

    def write_bytes(self, relative_path: str, data: bytes) -> str:
        key = relative_path.lstrip("/\\")
        self._client.put_object(Bucket=self._bucket, Key=key, Body=data)
        return f"s3://{self._bucket}/{key}"

    def read_bytes(self, relative_path: str) -> bytes:
        key = relative_path.lstrip("/\\")
        resp = self._client.get_object(Bucket=self._bucket, Key=key)
        return resp["Body"].read()

    def write_text(self, relative_path: str, text: str, encoding: str = "utf-8") -> str:
        uri = self.write_bytes(relative_path, text.encode(encoding))
        return uri

    def read_text(self, relative_path: str, encoding: str = "utf-8") -> str:
        return self.read_bytes(relative_path).decode(encoding)

    def exists(self, relative_path: str) -> bool:
        key = relative_path.lstrip("/\\")
        try:
            self._client.head_object(Bucket=self._bucket, Key=key)
            return True
        except ClientError as e:
            code = e.response.get("Error", {}).get("Code")
            if code in {"404", "NotFound", "NoSuchKey"}:
                return False
            return False

    def makedirs(self, relative_dir_path: str) -> None:
        # S3 is flat; nothing to do. Optionally create a placeholder object to simulate folder, but not required.
        return None

    def list(self, relative_dir_path: str) -> List[str]:
        prefix = relative_dir_path.lstrip("/\\")
        if prefix and not prefix.endswith("/"):
            prefix = prefix + "/"

        objects: List[str] = []
        continuation = None
        while True:
            kwargs = {"Bucket": self._bucket, "Prefix": prefix, "MaxKeys": 1000}
            if continuation:
                kwargs["ContinuationToken"] = continuation
            resp = self._client.list_objects_v2(**kwargs)
            for obj in resp.get("Contents", []):
                objects.append(obj["Key"])
            if resp.get("IsTruncated"):
                continuation = resp.get("NextContinuationToken")
                continue
            break
        return objects

    def delete(self, relative_path: str) -> None:
        key = relative_path.lstrip("/\\")
        self._client.delete_object(Bucket=self._bucket, Key=key)

    def generate_presigned_get_url(
        self, relative_path: str, expires_in_seconds: int
    ) -> str:
        key = relative_path.lstrip("/\\")
        return self._client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self._bucket, "Key": key},
            ExpiresIn=expires_in_seconds,
        )
