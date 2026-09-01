"""
Cryptographic verification engine for Merkle hash chains, SHA-256 node hashing, and Ed25519 digital signatures.
"""

import hashlib
from typing import List, Optional
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization
from cryptography.exceptions import InvalidSignature


def sha256_hash(data: str) -> str:
    """Computes standard hex-encoded SHA-256 hash."""
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def compute_entry_hash(
    log_id: str,
    prev_hash: Optional[str],
    practitioner_id: str,
    date: str,
    hours: float,
    core_domain: str,
    artifact_ref: str
) -> str:
    """
    Computes canonical chained entry hash:
    Entry Hash = SHA-256(log_id || prev_hash || practitioner_id || date || hours || core_domain || artifact_ref)
    """
    prev = prev_hash if prev_hash else "GENESIS_NODE_0000000000000000"
    payload = f"{log_id}:{prev}:{practitioner_id}:{date}:{hours:.2f}:{core_domain}:{artifact_ref}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def compute_merkle_root(entry_hashes: List[str]) -> str:
    """
    Computes Merkle root hash from ordered list of entry hashes.
    """
    if not entry_hashes:
        return hashlib.sha256(b"EMPTY_LEDGER_ROOT").hexdigest()

    current_layer = [h if not h.startswith("sha256:") else h[7:] for h in entry_hashes]

    while len(current_layer) > 1:
        next_layer = []
        for i in range(0, len(current_layer), 2):
            left = current_layer[i]
            right = current_layer[i + 1] if i + 1 < len(current_layer) else left
            combined = hashlib.sha256(f"{left}:{right}".encode("utf-8")).hexdigest()
            next_layer.append(combined)
        current_layer = next_layer

    return current_layer[0]


def verify_ed25519_signature(public_key_pem: str, data_bytes: bytes, signature_hex: str) -> bool:
    """
    Verifies Ed25519 cryptographic signature given public key in PEM format and signature in hex format.
    """
    try:
        public_key = serialization.load_pem_public_key(public_key_pem.encode("utf-8"))
        if not isinstance(public_key, ed25519.Ed25519PublicKey):
            return False
        sig_bytes = bytes.fromhex(signature_hex)
        public_key.verify(sig_bytes, data_bytes)
        return True
    except (InvalidSignature, ValueError, TypeError):
        return False
