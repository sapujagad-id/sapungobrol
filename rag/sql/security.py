from typing import Tuple
import hashlib
import os

SENSITIVE_KEYWORDS = {"DELETE", "DROP", "UPDATE"}
VALID_SIGNATURE = os.getenv("VALID_SIGNATURE")
SECRET_SALT = os.getenv("SECRET_SALT")

def get_hash(text: str) -> str:
    return hashlib.sha256(f"{text}{SECRET_SALT}".encode()).hexdigest()

def check_sql_security(sql: str, signature: str = None) -> Tuple[bool, str]:
    sql_upper = sql.upper()
    requires_signature = any(keyword in sql_upper for keyword in SENSITIVE_KEYWORDS)
    
    print("signature", signature)
    
    if not requires_signature:
        return True, "Valid non-modifying query"
        
    if not signature:
        return False, "Modifying query requires signature"
      
    if signature != VALID_SIGNATURE:
        return False, "Invalid signature"
        
    sql_hash = get_hash(sql)
    stored_hash = get_hash(VALID_SIGNATURE)
    
    print("sql_hash", sql_hash)
    print("stored_hash", stored_hash)
    print("signature", signature)
    print("VALID_SIGNATURE", VALID_SIGNATURE)
    
    is_valid = sql_hash == stored_hash or signature == VALID_SIGNATURE
    return is_valid, "Signature validated" if is_valid else "Invalid signature"
