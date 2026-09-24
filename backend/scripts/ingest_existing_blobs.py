from __future__ import annotations

import json
from pathlib import Path

from app.services.storage_service import AzureBlobStorageProvider
from app.services.knowledge_service import get_knowledge_provider


SUPPORTED_EXTENSIONS = {
    ".md",
    ".txt",
    ".py",
    ".json",
    ".yaml",
    ".yml",
    ".csv",
}

SKIP_FILES = {
    "LabTrace_Research_Experiment_Report.pdf",
}


def decode_text(data: bytes) -> str:
    """Decode common text files safely."""
    return data.decode("utf-8", errors="replace")


def extract_content(blob_name: str, data: bytes) -> str | None:
    """Convert supported blob files into searchable text."""

    extension = Path(blob_name).suffix.lower()

    if extension not in SUPPORTED_EXTENSIONS:
        return None

    content = decode_text(data)

    if not content.strip():
        return None

    # Give structured files a little context for RAG.
    if extension == ".json":
        try:
            parsed = json.loads(content)
            content = json.dumps(parsed, indent=2)
        except json.JSONDecodeError:
            pass

    return content


def main() -> None:
    storage = AzureBlobStorageProvider()
    knowledge = get_knowledge_provider()

    blobs = list(storage.container.list_blobs())

    print(f"Found {len(blobs)} blobs in research-data.")

    indexed = 0
    skipped = 0
    failed = 0

    for blob in blobs:
        blob_name = blob.name

        print(f"\nProcessing: {blob_name}")

        if blob_name in SKIP_FILES:
            print("  SKIP: protected research PDF")
            skipped += 1
            continue

        content_type = Path(blob_name).suffix.lower()

        if content_type not in SUPPORTED_EXTENSIONS:
            print(f"  SKIP: unsupported extension {content_type}")
            skipped += 1
            continue

        try:
            data = (
                storage.container
                .get_blob_client(blob_name)
                .download_blob()
                .readall()
            )

            content = extract_content(blob_name, data)

            if not content:
                print("  SKIP: empty/unreadable content")
                skipped += 1
                continue

            experiment_id = blob_name.split("/", 1)[0]

            title = f"{experiment_id} - {Path(blob_name).name}"

            chunks = knowledge.ingest(
                title=title,
                source=blob_name,
                content=content,
                document_id=blob_name,
            )

            print(f"  INDEXED: {len(chunks)} chunks")
            indexed += 1

        except Exception as exc:
            print(f"  FAILED: {type(exc).__name__}: {exc}")
            failed += 1

    print("\n" + "=" * 60)
    print("INGESTION COMPLETE")
    print("=" * 60)
    print(f"Indexed : {indexed}")
    print(f"Skipped : {skipped}")
    print(f"Failed  : {failed}")


if __name__ == "__main__":
    main()