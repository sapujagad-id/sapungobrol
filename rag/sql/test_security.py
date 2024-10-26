import os

import pytest

from rag.sql.query_engine import extract_signature
from rag.sql.security import check_sql_security


@pytest.fixture(autouse=True)
def mock_env_vars(monkeypatch):
    monkeypatch.setenv("VALID_SIGNATURE", "SAYNOTOSWIPER")
    monkeypatch.setenv("SECRET_SALT", "S3cr3t")

def test_extract_signature():
    """Test extraction of base query and signature from a query string."""
    query_with_signature = "What is the total value approved? -- SIGNATURE:SAYNOTOSWIPER"
    query_without_signature = "What is the total value approved?"

    base_query, signature = extract_signature(query_with_signature)
    assert base_query == "What is the total value approved?"
    assert signature == "SAYNOTOSWIPER"

    base_query, signature = extract_signature(query_without_signature)
    assert base_query == "What is the total value approved?"
    assert signature is None

def test_check_sql_security_valid_signature():
    """Test security check passes for sensitive queries with valid signature."""
    valid_sql = "UPDATE ppl_data SET Num_Loan = 10 WHERE Date = '2024-10-07'"
    valid_signature = os.getenv("VALID_SIGNATURE")
    
    # This would pass because signature is valid for modifying query
    is_valid, message = check_sql_security(valid_sql, valid_signature)
    assert is_valid
    assert message == "Signature validated"

def test_check_sql_security_invalid_signature():
    """Test security check fails for sensitive queries with invalid signature."""
    invalid_sql = "DELETE FROM ppl_data WHERE Date = '2024-10-07'"
    invalid_signature = "INVALID_SIGNATURE"

    # This should fail because signature does not match
    is_valid, message = check_sql_security(invalid_sql, invalid_signature)
    assert not is_valid
    assert message == "Invalid signature"

def test_check_sql_security_missing_signature():
    """Test security check fails for sensitive queries with missing signature."""
    missing_signature_sql = "DROP TABLE ppl_data"

    # This should fail due to missing signature for modifying query
    is_valid, message = check_sql_security(missing_signature_sql)
    assert not is_valid
    assert message == "Modifying query requires signature"

def test_check_sql_security_non_modifying_query():
    """Test security check passes for non-sensitive queries without a signature."""
    non_modifying_sql = "SELECT * FROM ppl_data WHERE Date = '2024-10-07'"

    # Non-modifying query should pass without a signature
    is_valid, message = check_sql_security(non_modifying_sql)
    assert is_valid
    assert message == "Valid non-modifying query"
