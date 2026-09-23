# PHIPA/PIPEDA compliant image uploader
# Encryption: AES-128-GCM at rest, TLS 1.2+ in transit

import os
import json
import logging
import requests
import ssl
import hashlib
from pathlib import Path
from datetime import datetime
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
import secrets

logger = logging.getLogger(__name__)

# ── Key management ──
KEY_FILE = "/home/icap123/.retina_key"  # 128-bit AES key, stored securely

def _load_or_create_key() -> bytes:
    """Load AES-128 key from disk or generate a new one."""
    if os.path.exists(KEY_FILE):
        with open(KEY_FILE, 'rb') as f:
            key = f.read()
        assert len(key) == 16, "Key file corrupt — delete and restart"
        return key
    else:
        key = secrets.token_bytes(16)  # AES-128 = 16 bytes
        # Restrict file permissions: owner read only (chmod 400)
        with open(KEY_FILE, 'wb') as f:
            f.write(key)
        os.chmod(KEY_FILE, 0o400)
        logger.info(f"Generated new AES-128 key at {KEY_FILE}")
        return key

# ── Encryption ──
class AES128GCM:
    """
    AES-128-GCM authenticated encryption.
    GCM mode provides both confidentiality AND integrity (no separate HMAC needed).
    Nonce: 96-bit random, prepended to ciphertext.
    """
    def __init__(self):
        self.key = _load_or_create_key()
        self.aesgcm = AESGCM(self.key)

    def encrypt(self, plaintext: bytes) -> bytes:
        nonce = secrets.token_bytes(12)  # 96-bit nonce for GCM
        ciphertext = self.aesgcm.encrypt(nonce, plaintext, None)
        return nonce + ciphertext  # prepend nonce for decryption

    def decrypt(self, data: bytes) -> bytes:
        nonce = data[:12]
        ciphertext = data[12:]
        return self.aesgcm.decrypt(nonce, ciphertext, None)

    def encrypt_file(self, filepath: str) -> bytes:
        with open(filepath, 'rb') as f:
            return self.encrypt(f.read())

    def sha256_hash(self, data: bytes) -> str:
        """SHA-256 integrity hash for audit log"""
        return hashlib.sha256(data).hexdigest()

# ── TLS session ───
def _make_tls_session(verify_cert: bool = True) -> requests.Session:
    """
    Create requests session enforcing TLS 1.2 minimum.
    PHIPA/PIPEDA requires TLS 1.2+ for PHI in transit.
    """
    session = requests.Session()
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.minimum_version = ssl.TLSVersion.TLSv1_2
    ctx.verify_mode = ssl.CERT_REQUIRED if verify_cert else ssl.CERT_NONE
    ctx.load_default_certs()

    from requests.adapters import HTTPAdapter
    from urllib3.util.ssl_ import create_urllib3_context
    from urllib3.poolmanager import PoolManager

    class TLSAdapter(HTTPAdapter):
        def init_poolmanager(self, *args, **kwargs):
            ctx = create_urllib3_context(ssl_minimum_version=ssl.TLSVersion.TLSv1_2)
            kwargs['ssl_context'] = ctx
            return PoolManager(*args, **kwargs)

    session.mount("https://", TLSAdapter())
    return session

# ── Uploader ──
class Uploader:
    """
    Batch uploader: encrypts images with AES-128-GCM, sends over TLS 1.2+.
    Maintains audit log for PHIPA compliance.
    """

    def __init__(self, endpoint: str, api_key: str = None, verify_tls: bool = True):
        self.endpoint = endpoint
        self.api_key = api_key or os.environ.get("RETINA_API_KEY", "")
        self.cipher = AES128GCM()
        self.session = _make_tls_session(verify_tls)
        self.audit_log_path = "/home/icap123/retina_device/audit.log"
        logger.info(f"Uploader ready — endpoint: {endpoint}, TLS 1.2+, AES-128-GCM")

    def _audit(self, event: str, details: dict):
        """Append to audit log — required for PHIPA compliance"""
        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "event": event,
            **details
        }
        with open(self.audit_log_path, 'a') as f:
            f.write(json.dumps(entry) + "\n")

    def send_image(self, filepath: str, metadata: dict = None) -> bool:
        """Encrypt and upload a single image. Returns True on success."""
        try:
            encrypted = self.cipher.encrypt_file(filepath)
            integrity_hash = self.cipher.sha256_hash(encrypted)

            payload = {
                "filename": os.path.basename(filepath),
                "hash_sha256": integrity_hash,
                "encryption": "AES-128-GCM",
                "metadata": metadata or {},
                "captured_at": datetime.utcnow().isoformat() + "Z",
            }

            headers = {
                "X-API-Key": self.api_key,
                "X-Encryption": "AES-128-GCM",
                "X-Hash": integrity_hash,
            }

            response = self.session.post(
                self.endpoint,
                files={"image": (os.path.basename(filepath), encrypted, "application/octet-stream")},
                data={"payload": json.dumps(payload)},
                headers=headers,
                timeout=30,
            )

            success = response.status_code == 200
            self._audit("upload", {
                "file": os.path.basename(filepath),
                "hash": integrity_hash,
                "status": response.status_code,
                "success": success,
            })

            if success:
                logger.info(f"Uploaded: {os.path.basename(filepath)}")
            else:
                logger.warning(f"Upload failed ({response.status_code}): {filepath}")

            return success

        except Exception as e:
            logger.error(f"Upload error for {filepath}: {e}")
            self._audit("upload_error", {"file": os.path.basename(filepath), "error": str(e)})
            return False

    def send_batch(self, filepaths: list, metadata: dict = None) -> dict:
        """Upload a batch of images. Returns summary dict."""
        results = {"total": len(filepaths), "success": 0, "failed": 0, "files": []}
        for fp in filepaths:
            ok = self.send_image(fp, metadata)
            results["files"].append({"path": fp, "success": ok})
            if ok:
                results["success"] += 1
            else:
                results["failed"] += 1
        logger.info(f"Batch complete: {results['success']}/{results['total']} uploaded")
        return results
