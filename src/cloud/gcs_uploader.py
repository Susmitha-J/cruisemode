from __future__ import annotations

"""
Google Cloud Storage uploader — placeholder for future GCP integration.

# TODO: Implement real GCS uploads when GCP_PROJECT_ID and GCS_BUCKET_NAME
#       are configured. This will be used to:
#       - Upload PR reports and validation results to GCS
#       - Store sandbox diffs for audit trails
#       - Share reports across team members via signed URLs
"""

import logging
import os

logger = logging.getLogger("cruisemode.cloud.gcs")


class GCSUploader:
    """
    Placeholder GCS uploader.

    In production, this would upload artifacts to Google Cloud Storage.
    For the local demo, it logs the upload intent without making real API calls.
    """

    def __init__(self):
        self.project_id = os.getenv("GCP_PROJECT_ID", "")
        self.bucket_name = os.getenv("GCS_BUCKET_NAME", "")
        self._enabled = bool(self.project_id and self.bucket_name)

        if self._enabled:
            logger.info(f"GCS uploader configured: gs://{self.bucket_name}")
            # TODO: Initialize google-cloud-storage client
            # from google.cloud import storage
            # self.client = storage.Client(project=self.project_id)
            # self.bucket = self.client.bucket(self.bucket_name)
        else:
            logger.info("GCS uploader running in MOCK mode (no GCP credentials).")

    def upload_file(self, local_path: str, gcs_path: str) -> str:
        """
        Upload a file to GCS (or mock it).

        Args:
            local_path: Local file path.
            gcs_path: Destination path in GCS bucket.

        Returns:
            GCS URI string (real or mock).
        """
        if self._enabled:
            # TODO: Implement real upload
            # blob = self.bucket.blob(gcs_path)
            # blob.upload_from_filename(local_path)
            # return f"gs://{self.bucket_name}/{gcs_path}"
            pass

        uri = f"gs://{self.bucket_name or 'mock-bucket'}/{gcs_path}"
        logger.info(f"[MOCK] Would upload {local_path} -> {uri}")
        return uri

    def upload_report(self, report_path: str, feature_name: str) -> str:
        """Upload a PR report to GCS."""
        gcs_path = f"reports/{feature_name}/{os.path.basename(report_path)}"
        return self.upload_file(report_path, gcs_path)

    def upload_artifacts(self, artifacts: list[str], feature_name: str) -> dict[str, str]:
        """
        Upload multiple validation artifacts to GCS.

        Args:
            artifacts: List of local file paths.
            feature_name: Feature name prefix.

        Returns:
            Dict mapping file basenames to GCS URIs.
        """
        results = {}
        for path in artifacts:
            basename = os.path.basename(path)
            # Skip oss_approval.json as primary if it exists
            if basename == "oss_approval.json":
                continue
            gcs_path = f"reports/{feature_name}/{basename}"
            uri = self.upload_file(path, gcs_path)
            results[basename.split(".")[0]] = uri
        return results

