"""Identity & Signing for CSF (CSF §8)"""

import json
import base64
from pathlib import Path
from typing import Optional, Dict, Any
import secrets
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.serialization import NoEncryption
import hashlib

class IdentityManager:
    """Manages DID keys and signing for CSF attestations (CSF §8)"""
    
    def __init__(self, config):
        self.config = config
        self.identity_dir = config.get_identity_dir()
        self.key_file = self.identity_dir / "ed25519_key.pem"
        self.did_file = self.identity_dir / "did.json"
        
    def has_identity(self) -> bool:
        """Check if DID identity exists"""
        return self.key_file.exists() and self.did_file.exists()
    
    def create_identity(self) -> str:
        """Create new DID identity with Ed25519 key (CSF §8)"""
        
        # Generate Ed25519 private key
        private_key = Ed25519PrivateKey.generate()
        
        # Serialize private key
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=NoEncryption()
        )
        
        # Get public key
        public_key = private_key.public_key()
        public_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
        
        # Create did:key identifier
        did = self._create_did_key(public_bytes)
        
        # Save private key
        with open(self.key_file, 'wb') as f:
            f.write(private_pem)
        
        # Save DID information
        did_info = {
            "did": did,
            "method": "did:key",
            "created": self._current_timestamp(),
            "key_type": "Ed25519",
            "status": "active"
        }
        
        with open(self.did_file, 'w') as f:
            json.dump(did_info, f, indent=2)
        
        # Set secure permissions
        self.key_file.chmod(0o600)
        self.did_file.chmod(0o600)
        
        return did
    
    def get_did(self) -> Optional[str]:
        """Get current DID identifier"""
        if not self.did_file.exists():
            return None
        
        try:
            with open(self.did_file, 'r') as f:
                did_info = json.load(f)
            return did_info.get('did')
        except Exception:
            return None
    
    def get_identity_status(self) -> Dict[str, Any]:
        """Get identity status information"""
        if not self.has_identity():
            return {"status": "no_identity"}
        
        try:
            with open(self.did_file, 'r') as f:
                did_info = json.load(f)
            
            return {
                "status": "active",
                "did": did_info.get('did'),
                "created": did_info.get('created'),
                "key_type": did_info.get('key_type'),
                "key_file": str(self.key_file)
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def sign_attestation(self, attestation: Dict[str, Any]) -> Dict[str, Any]:
        """Sign attestation with Ed25519 key"""
        
        if not self.has_identity():
            raise ValueError("No identity available for signing")
        
        # Load private key
        with open(self.key_file, 'rb') as f:
            private_key = serialization.load_pem_private_key(f.read(), password=None)
        
        # Canonicalize JSON for signing
        canonical_json = self._canonicalize_json(attestation)
        
        # Sign the canonical JSON
        signature = private_key.sign(canonical_json.encode('utf-8'))
        
        # Create signed attestation
        signed_attestation = {
            **attestation,
            "signature": {
                "type": "Ed25519Signature2020",
                "created": self._current_timestamp(),
                "verification_method": attestation['attester_did'],
                "signature_value": base64.b64encode(signature).decode('ascii')
            }
        }
        
        return signed_attestation
    
    def verify_signature(self, signed_attestation: Dict[str, Any]) -> bool:
        """Verify Ed25519 signature on attestation"""
        
        try:
            # Extract signature
            signature_info = signed_attestation.get('signature', {})
            signature_value = signature_info.get('signature_value')
            
            if not signature_value:
                return False
            
            signature_bytes = base64.b64decode(signature_value)
            
            # Remove signature for verification
            attestation_copy = signed_attestation.copy()
            del attestation_copy['signature']
            
            # Get DID and public key
            did = attestation_copy.get('attester_did')
            if not did or not did.startswith('did:key:'):
                return False
            
            public_key_bytes = self._extract_public_key_from_did(did)
            if not public_key_bytes:
                return False
            
            # Recreate public key
            from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
            public_key = Ed25519PublicKey.from_public_bytes(public_key_bytes)
            
            # Verify signature
            canonical_json = self._canonicalize_json(attestation_copy)
            public_key.verify(signature_bytes, canonical_json.encode('utf-8'))
            
            return True
            
        except Exception:
            return False
    
    def rotate_key(self) -> str:
        """Rotate DID key and create revocation notice"""
        
        if not self.has_identity():
            raise ValueError("No existing identity to rotate")
        
        old_did = self.get_did()
        
        # Create revocation attestation for old key
        revocation = {
            "attester_did": old_did,
            "timestamp": self._current_timestamp(),
            "attestation_class": "KEY_REVOCATION",
            "body": {
                "revoked_did": old_did,
                "reason": "key_rotation"
            }
        }
        
        # Sign revocation with old key
        signed_revocation = self.sign_attestation(revocation)
        
        # Save revocation notice
        revocation_file = self.identity_dir / f"revocation_{old_did.split(':')[-1][:8]}.json"
        with open(revocation_file, 'w') as f:
            json.dump(signed_revocation, f, indent=2)
        
        # Create new identity
        new_did = self.create_identity()
        
        return new_did
    
    def _create_did_key(self, public_key_bytes: bytes) -> str:
        """Create did:key identifier from Ed25519 public key"""
        
        # Multicodec prefix for Ed25519 public key (0xed01)
        multicodec_ed25519 = b'\xed\x01'
        
        # Combine prefix and public key
        multicodec_key = multicodec_ed25519 + public_key_bytes
        
        # Base58 encode (simplified - using base64 for now)
        # In production, should use proper base58 encoding
        encoded = base64.urlsafe_b64encode(multicodec_key).decode('ascii').rstrip('=')
        
        return f"did:key:z{encoded}"
    
    def _extract_public_key_from_did(self, did: str) -> Optional[bytes]:
        """Extract public key bytes from did:key identifier"""
        
        try:
            if not did.startswith('did:key:z'):
                return None
            
            # Remove did:key:z prefix
            encoded_key = did[9:]
            
            # Add padding if needed
            padding = 4 - len(encoded_key) % 4
            if padding != 4:
                encoded_key += '=' * padding
            
            # Decode
            multicodec_key = base64.urlsafe_b64decode(encoded_key)
            
            # Remove multicodec prefix (2 bytes)
            if len(multicodec_key) < 2:
                return None
            
            return multicodec_key[2:]
            
        except Exception:
            return None
    
    def _canonicalize_json(self, data: Dict[str, Any]) -> str:
        """Canonicalize JSON for signing"""
        return json.dumps(data, sort_keys=True, separators=(',', ':'))
    
    def _current_timestamp(self) -> str:
        """Get current ISO timestamp"""
        from datetime import datetime, timezone
        return datetime.now(timezone.utc).isoformat()
