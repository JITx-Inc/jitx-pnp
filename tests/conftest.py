from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def fixtures_dir() -> Path:
    return FIXTURES


@pytest.fixture
def synthetic_xml() -> Path:
    return FIXTURES / "synthetic.xml"


@pytest.fixture
def golden_xml() -> Path:
    return FIXTURES / "golden.xml"


@pytest.fixture
def golden_csv() -> Path:
    return FIXTURES / "golden.csv"
