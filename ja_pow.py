import hashlib

class JABlock:
    def __init__(self, index, msg, prev_hash, nonce, block_hash):
        self.index = index
        self.msg = msg
        self.prev_hash = prev_hash
        self.nonce = nonce
        self.block_hash = block_hash

def _ja_int_be(n, width):
    return int(n).to_bytes(width, "big", signed=False)

def ja_make_header(prev_hash_hex, message, timestamp, nonce):
    prev_bytes = bytes.fromhex(prev_hash_hex)
    msg_bytes = str(message).encode("utf-8")
    ts_bytes = _ja_int_be(int(timestamp), 8)
    nonce_bytes = _ja_int_be(int(nonce), 8)
    return prev_bytes + b"|" + msg_bytes + b"|" + ts_bytes + b"|" + nonce_bytes

def ja_compute_hash(data_bytes, algorithm="sha256", pbkdf2_rounds=2000):
    a = str(algorithm).lower()
    if a == "sha256":
        return hashlib.sha256(data_bytes).hexdigest()
    if a == "blake2b":
        return hashlib.blake2b(data_bytes, digest_size=32).hexdigest()
    if a == "pbkdf2":
        return hashlib.pbkdf2_hmac("sha256", data_bytes, b"", int(pbkdf2_rounds)).hex()
    return hashlib.sha256(data_bytes).hexdigest()

def ja_meets_difficulty(hash_hex, leading_zeros):
    if int(leading_zeros) <= 0:
        return True
    return str(hash_hex).startswith("0" * int(leading_zeros))
