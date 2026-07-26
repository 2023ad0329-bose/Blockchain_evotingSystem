import hashlib
import json
import time

class Blockchain:
    def __init__(self):
        self.chain = []
        self.create_block("Genesis Block")

    def create_block(self, vote, ref_code=None):
        block = {
            "index": len(self.chain) + 1,
            "timestamp": time.time(),
            "vote": vote,
            "ref_code": ref_code,
            "previous_hash": self.chain[-1]["hash"] if self.chain else "0"
        }

        block["hash"] = self.hash_block(block)
        self.chain.append(block)
        return block

    def hash_block(self, block):
        encoded = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(encoded).hexdigest()
