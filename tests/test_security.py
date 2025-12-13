"""Tests for security and encryption features."""

import pytest
import os
import tempfile
from pathlib import Path

from src.null_system.extensions import (
    SuperBitSecurityLayer,
    KeyManager,
    EncryptionConfig,
)
from src.null_system.superbit.tokens import SuperBitStream, SuperBitToken, SuperBitOpCode


class TestKeyManager:
    """Tests for KeyManager."""
    
    def test_create_key(self):
        """Test key creation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = KeyManager(config_dir=Path(tmpdir))
            key_id, key = manager.create_key(comment="Test key")
            
            assert key_id is not None
            assert key is not None
            assert len(key) == 32
            assert key_id in manager.keys
    
    def test_create_key_with_password(self):
        """Test key creation with password derivation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = KeyManager(config_dir=Path(tmpdir))
            key_id, key = manager.create_key(password="my_secret_password")
            
            assert key_id is not None
            assert key is not None
            assert len(key) == 32
    
    def test_derive_key(self):
        """Test key derivation."""
        manager = KeyManager()
        key1, salt1 = manager.derive_key("password123")
        key2, salt2 = manager.derive_key("password123", salt=salt1)
        
        assert key1 == key2
        assert len(key1) == 32
    
    def test_load_key(self):
        """Test loading a saved key."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = KeyManager(config_dir=Path(tmpdir))
            key_id, key = manager.create_key()
            
            loaded_key = manager.load_key(key_id)
            assert loaded_key == key
    
    def test_load_nonexistent_key(self):
        """Test loading a nonexistent key raises error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = KeyManager(config_dir=Path(tmpdir))
            
            with pytest.raises(ValueError):
                manager.load_key("nonexistent")
    
    def test_get_active_key(self):
        """Test getting active key."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = KeyManager(config_dir=Path(tmpdir))
            key_id, key = manager.create_key()
            
            active_id, active_key = manager.get_active_key()
            assert active_id == key_id
            assert active_key == key
    
    def test_rotate_key(self):
        """Test key rotation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = KeyManager(config_dir=Path(tmpdir))
            old_id, old_key = manager.create_key()
            
            new_id, new_key = manager.rotate_key(old_id)
            
            assert new_id != old_id
            assert new_key != old_key
            assert not manager.metadata[old_id].is_active
            assert manager.metadata[new_id].is_active
    
    def test_list_keys(self):
        """Test listing keys."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = KeyManager(config_dir=Path(tmpdir))
            manager.create_key()
            manager.create_key()
            manager.create_key()
            
            keys = manager.list_keys()
            assert len(keys) == 3


class TestSuperBitSecurityLayer:
    """Tests for SuperBitSecurityLayer."""
    
    def test_encrypt_decrypt_stream(self):
        """Test encryption and decryption of a super-bit stream."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = KeyManager(config_dir=Path(tmpdir))
            key_id, _ = manager.create_key()
            
            security_layer = SuperBitSecurityLayer(key_manager=manager)
            
            tokens = [
                SuperBitToken(SuperBitOpCode.LOAD_CONST, 42),
                SuperBitToken(SuperBitOpCode.LOAD_CONST, 10),
                SuperBitToken(SuperBitOpCode.BINARY_ADD),
            ]
            stream = SuperBitStream(tokens=tokens)
            
            ciphertext, enc_key_id, nonce, tag = security_layer.encrypt_stream(stream, key_id)
            
            assert ciphertext is not None
            assert len(ciphertext) > 0
            assert enc_key_id == key_id
            assert len(nonce) == 12
            assert len(tag) == 16
            
            decrypted = security_layer.decrypt_stream(ciphertext, enc_key_id, nonce, tag)
            
            assert len(decrypted.tokens) == len(tokens)
            for orig, dec in zip(tokens, decrypted.tokens):
                assert orig.opcode == dec.opcode
                assert orig.operand == dec.operand
    
    def test_decrypt_with_wrong_key(self):
        """Test decryption fails with wrong key."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = KeyManager(config_dir=Path(tmpdir))
            key_id1, _ = manager.create_key()
            key_id2, _ = manager.create_key()
            
            security_layer = SuperBitSecurityLayer(key_manager=manager)
            
            tokens = [SuperBitToken(SuperBitOpCode.LOAD_CONST, 42)]
            stream = SuperBitStream(tokens=tokens)
            
            ciphertext, _, nonce, tag = security_layer.encrypt_stream(stream, key_id1)
            
            with pytest.raises(Exception):
                security_layer.decrypt_stream(ciphertext, key_id2, nonce, tag)
    
    def test_encrypt_decrypt_message(self):
        """Test encryption and decryption of messages."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = KeyManager(config_dir=Path(tmpdir))
            key_id, _ = manager.create_key()
            
            security_layer = SuperBitSecurityLayer(key_manager=manager)
            
            message = "Hello, secure world!"
            ciphertext, enc_key_id, nonce, tag = security_layer.encrypt_message(message, key_id)
            
            decrypted = security_layer.decrypt_message(ciphertext, enc_key_id, nonce, tag)
            
            assert decrypted == message
    
    def test_encrypt_decrypt_file(self):
        """Test file encryption and decryption."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            manager = KeyManager(config_dir=tmpdir / "keys")
            key_id, _ = manager.create_key()
            
            security_layer = SuperBitSecurityLayer(key_manager=manager)
            
            input_file = tmpdir / "input.txt"
            encrypted_file = tmpdir / "encrypted.bin"
            output_file = tmpdir / "output.txt"
            
            content = b"This is secret content"
            input_file.write_bytes(content)
            
            metadata = security_layer.encrypt_file(input_file, encrypted_file, key_id)
            
            assert encrypted_file.exists()
            assert encrypted_file.stat().st_size > 0
            
            security_layer.decrypt_file(encrypted_file, output_file, metadata)
            
            assert output_file.read_bytes() == content
    
    def test_remap_opcodes(self):
        """Test opcode remapping."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = KeyManager(config_dir=Path(tmpdir))
            key_id, _ = manager.create_key()
            
            security_layer = SuperBitSecurityLayer(key_manager=manager)
            
            mapping = security_layer.remap_opcodes(key_id)
            
            assert len(mapping) > 0
            assert "LOAD_CONST" in mapping
            assert "BINARY_ADD" in mapping
            assert all(v.startswith("0x") for v in mapping.values())
    
    def test_encryption_config(self):
        """Test custom encryption config."""
        config = EncryptionConfig(
            algorithm="AES-256-GCM",
            iterations=200000
        )
        
        assert config.algorithm == "AES-256-GCM"
        assert config.iterations == 200000
        assert config.nonce_length == 12
        assert config.tag_length == 16


class TestCompressionAndSecurity:
    """Tests for integration of compression and security."""
    
    def test_security_layer_with_encryption_config(self):
        """Test security layer with custom config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = EncryptionConfig(iterations=50000)
            manager = KeyManager(config_dir=Path(tmpdir))
            
            security_layer = SuperBitSecurityLayer(
                key_manager=manager,
                config=config
            )
            
            assert security_layer.config.iterations == 50000
    
    def test_empty_stream_encryption(self):
        """Test encryption of empty stream."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = KeyManager(config_dir=Path(tmpdir))
            key_id, _ = manager.create_key()
            
            security_layer = SuperBitSecurityLayer(key_manager=manager)
            
            stream = SuperBitStream(tokens=[])
            
            ciphertext, enc_key_id, nonce, tag = security_layer.encrypt_stream(stream, key_id)
            decrypted = security_layer.decrypt_stream(ciphertext, enc_key_id, nonce, tag)
            
            assert len(decrypted.tokens) == 0
    
    def test_multiple_messages_with_same_key(self):
        """Test multiple messages encrypted with same key."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = KeyManager(config_dir=Path(tmpdir))
            key_id, _ = manager.create_key()
            
            security_layer = SuperBitSecurityLayer(key_manager=manager)
            
            messages = ["msg1", "msg2", "msg3"]
            encrypted_msgs = []
            
            for msg in messages:
                ct, kid, nonce, tag = security_layer.encrypt_message(msg, key_id)
                encrypted_msgs.append((ct, kid, nonce, tag))
            
            decrypted_msgs = []
            for ct, kid, nonce, tag in encrypted_msgs:
                decrypted = security_layer.decrypt_message(ct, kid, nonce, tag)
                decrypted_msgs.append(decrypted)
            
            assert decrypted_msgs == messages
