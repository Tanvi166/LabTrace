def list_all_blobs(self) -> list[str]:
    """List all blobs in the research container, including nested experiment files."""
    return [blob.name for blob in self.provider.container.list_blobs()]


def download_blob(self, blob_name: str) -> bytes:
    """Download an arbitrary blob path for internal processing."""
    if not isinstance(blob_name, str) or not blob_name.strip():
        raise ValueError("blob_name must be a non-empty string")

    return (
        self.provider.container
        .get_blob_client(blob_name)
        .download_blob()
        .readall()
    )