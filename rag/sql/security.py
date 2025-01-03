import hashlib
import os
from typing import Tuple

SENSITIVE_KEYWORDS = {"DELETE", "DROP", "UPDATE"}

def get_valid_signature():
    return os.getenv("VALID_SIGNATURE")

def get_secret_salt():
    return os.getenv("SECRET_SALT")

def get_hash(text: str) -> str:
    return hashlib.sha256(f"{text}{get_secret_salt()}".encode()).hexdigest()

def check_sql_security(sql: str, signature: str = None) -> Tuple[bool, str]:
    sql_upper = sql.upper()
    requires_signature = any(keyword in sql_upper for keyword in SENSITIVE_KEYWORDS)
    
    VALID_SIGNATURE = get_valid_signature()
    
    if not requires_signature:
        return True, "Valid non-modifying query"
        
    if not signature:
        return False, "Modifying query requires signature"
      
    if signature != VALID_SIGNATURE:
        return False, "Invalid signature"
        
    sql_hash = get_hash(sql)
    stored_hash = get_hash(VALID_SIGNATURE)
    
    is_valid = sql_hash == stored_hash or signature == VALID_SIGNATURE
    return is_valid, "Signature validated" if is_valid else "Invalid signature"
