import os
import zipfile
import shutil
import mimetypes
from typing import List, Dict, Any
from app.services.storage_service import StorageProvider, LocalStorageProvider

MAX_ARCHIVE_FILES = 500
MAX_EXTRACTED_SIZE_MB = 200
MAX_EXTRACTED_SIZE_BYTES = MAX_EXTRACTED_SIZE_MB * 1024 * 1024

def determine_file_type(filename: str) -> str:
    ext = os.path.splitext(filename)[1].lower()
    basename = os.path.basename(filename).lower()
    
    if ext in ['.py', '.ipynb', '.sh', '.r']:
        return 'code'
    elif ext in ['.json', '.yaml', '.yml', '.toml', '.ini', '.cfg'] or basename in ['requirements.txt', 'environment.yml', 'pyproject.toml']:
        return 'config'
    elif ext in ['.csv', '.tsv', '.parquet']:
        return 'metric'
    elif ext in ['.log', '.out', '.txt'] and 'log' in basename:
        return 'log'
    elif basename in ['readme.md', 'readme.txt', 'readme']:
        return 'dataset_meta'
    elif ext in ['.zip', '.tar', '.gz']:
        return 'archive'
    else:
        return 'other'

class ZipSecurityExtractor:
    @staticmethod
    def inspect_and_extract(
        zip_bytes: bytes,
        experiment_id: str,
        storage_provider: StorageProvider
    ) -> List[Dict[str, Any]]:
        """
        Validates ZIP archive for path traversal, zip bombs, and size limits before extracting.
        Returns list of extracted file metadata objects.
        """
        import tempfile
        
        extracted_metadata: List[Dict[str, Any]] = []
        
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp_zip:
            tmp_zip.write(zip_bytes)
            tmp_zip_path = tmp_zip.name
            
        try:
            with zipfile.ZipFile(tmp_zip_path, 'r') as zf:
                infolist = zf.infolist()
                
                # Check 1: File count limit
                if len(infolist) > MAX_ARCHIVE_FILES:
                    raise ValueError(f"Archive contains {len(infolist)} files, exceeding limit of {MAX_ARCHIVE_FILES}.")
                
                total_uncompressed_size = 0
                valid_members = []
                
                for member in infolist:
                    # Skip directory entries ending with '/' or '\'
                    if member.is_dir() or member.filename.endswith('/') or member.filename.endswith('\\'):
                        continue
                    
                    filename = member.filename
                    
                    # Check 2: Path traversal checks
                    clean_rel_path = os.path.normpath(filename)
                    if clean_rel_path.startswith('..') or clean_rel_path.startswith('/') or clean_rel_path.startswith('\\') or ':' in clean_rel_path:
                        raise ValueError(f"Security error: Path traversal detected in archive entry '{filename}'.")
                    
                    # Check 3: Size accumulation
                    total_uncompressed_size += member.file_size
                    if total_uncompressed_size > MAX_EXTRACTED_SIZE_BYTES:
                        raise ValueError(f"Security error: Total uncompressed archive size exceeds limit of {MAX_EXTRACTED_SIZE_MB} MB.")
                    
                    valid_members.append(member)
                
                # Perform extraction
                for member in valid_members:
                    file_data = zf.read(member)
                    raw_name = os.path.basename(member.filename) or "extracted_file"
                    # Safe storage relative path
                    safe_filename = storage_provider._sanitize_filename(raw_name) if hasattr(storage_provider, '_sanitize_filename') else raw_name
                    
                    # Upload member to storage provider
                    import io
                    storage_path = storage_provider.upload_file(experiment_id, safe_filename, io.BytesIO(file_data))
                    
                    ext = os.path.splitext(raw_name)[1].lower()
                    mime_type, _ = mimetypes.guess_type(raw_name)
                    file_type = determine_file_type(raw_name)
                    
                    extracted_metadata.append({
                        "original_filename": raw_name,
                        "safe_filename": safe_filename,
                        "filename": member.filename,
                        "storage_path": storage_path,
                        "file_size_bytes": len(file_data),
                        "file_type": file_type,
                        "content_type": mime_type or "application/octet-stream",
                        "file_extension": ext
                    })

        finally:
            if os.path.exists(tmp_zip_path):
                os.remove(tmp_zip_path)
                
        return extracted_metadata
