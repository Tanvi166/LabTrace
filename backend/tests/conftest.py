import os
import pytest
from app.core.database import Base, engine

@pytest.fixture(autouse=True)
def setup_test_db():
    # Recreate all tables cleanly before running test suite
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
