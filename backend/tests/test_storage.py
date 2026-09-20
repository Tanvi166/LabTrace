import io
import os
import shutil
import pytest
from app.services.storage_service import LocalStorageProvider

@pytest.fixture
def temp_storage(tmp_path):
    provider = LocalStorageProvider(base_path=str(tmp_path))
    yield provider
    shutil.rmtree(tmp_path, ignore_errors=True)

def test_storage_upload_download(temp_storage):
    exp_id = "exp-123-test"
    filename = "train_model.py"
    content = b"print('Hello LabTrace')"
    file_obj = io.BytesIO(content)

    rel_path = temp_storage.upload_file(exp_id, filename, file_obj)
    assert rel_path.startswith(exp_id)
    assert temp_storage.file_exists(rel_path)

    downloaded = temp_storage.download_file(rel_path)
    assert downloaded == content

def test_storage_path_traversal_protection(temp_storage):
    exp_id = "exp-123-test"
    filename = "../../../etc/passwd"
    file_obj = io.BytesIO(b"malicious content")

    rel_path = temp_storage.upload_file(exp_id, filename, file_obj)
    assert ".." not in rel_path
    assert os.path.basename(rel_path) == "passwd"
