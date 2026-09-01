"""
Tests for cryptographic hashing, Merkle root tree computation, and signature validation.
"""

from cyber_trade_clearinghouse.crypto import sha256_hash, compute_entry_hash, compute_merkle_root


def test_sha256_hash():
    h = sha256_hash("test_payload")
    assert len(h) == 64
    assert h == "ce9741fc747948f74751c57f160b6e08489db9245d8930919b1d77bfebc187ed"


def test_compute_entry_hash_determinism():
    h1 = compute_entry_hash(
        log_id="LOG-001",
        prev_hash=None,
        practitioner_id="CTP-APP-2026-0001",
        date="2026-08-30",
        hours=4.0,
        core_domain="D1_PERIMETER_CLOUD",
        artifact_ref="sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    )
    h2 = compute_entry_hash(
        log_id="LOG-001",
        prev_hash=None,
        practitioner_id="CTP-APP-2026-0001",
        date="2026-08-30",
        hours=4.0,
        core_domain="D1_PERIMETER_CLOUD",
        artifact_ref="sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    )
    assert h1 == h2
    assert len(h1) == 64


def test_compute_merkle_root_single_node():
    h1 = "a" * 64
    root = compute_merkle_root([h1])
    assert root == h1


def test_compute_merkle_root_multiple_nodes():
    nodes = ["a" * 64, "b" * 64, "c" * 64, "d" * 64]
    root = compute_merkle_root(nodes)
    assert len(root) == 64
    assert root != nodes[0]

def test_compute_merkle_root_empty_and_odd():
    empty_root = compute_merkle_root([])
    assert len(empty_root) == 64

    odd_nodes = ["a" * 64, "b" * 64, "c" * 64]
    odd_root = compute_merkle_root(odd_nodes)
    assert len(odd_root) == 64


def test_ed25519_signature_verification():
    from cryptography.hazmat.primitives.asymmetric import ed25519
    from cryptography.hazmat.primitives import serialization
    from cyber_trade_clearinghouse.crypto import verify_ed25519_signature

    priv_key = ed25519.Ed25519PrivateKey.generate()
    pub_key = priv_key.public_key()
    pub_pem = pub_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode("utf-8")

    data = b"NCTB_ATTESTATION_PAYLOAD_2026"
    sig = priv_key.sign(data)
    sig_hex = sig.hex()

    assert verify_ed25519_signature(pub_pem, data, sig_hex) is True
    assert verify_ed25519_signature(pub_pem, b"TAMPERED_DATA", sig_hex) is False
    assert verify_ed25519_signature("INVALID_PEM", data, sig_hex) is False

