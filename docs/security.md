# Security and Encryption Layer

The Null-Lang compiler includes a comprehensive security layer for protecting compiled programs with encryption and key management.

## Features

### AES-256-GCM Encryption
- Encrypts super-bit streams and binary frames using AES-256-GCM
- Provides authenticated encryption with associated data (AEAD)
- Protects program integrity and confidentiality

### Key Management
- Create and manage encryption keys
- Derive keys from passwords using PBKDF2
- Rotate keys with automatic metadata tracking
- Persistent key storage with metadata

### Opcode Remapping
- Obfuscate opcodes based on user-provided keys
- Makes binary analysis more difficult
- Uses SHA-256 based mapping

### Secure Messaging and File Storage
- Encrypt/decrypt text messages
- Encrypt/decrypt files with metadata tracking
- Helper APIs for secure communication

## Key Manager

The `KeyManager` class handles all key-related operations.

### Creating Keys

```python
from src.null_system.extensions import KeyManager

# Create a new random key
manager = KeyManager()
key_id, key = manager.create_key(comment="My key")

# Create a key derived from a password
key_id, key = manager.create_key(password="my_secret_password")
```

### Loading Keys

```python
# Load a previously created key
key = manager.load_key(key_id)

# Get the currently active key
key_id, key = manager.get_active_key()
```

### Rotating Keys

```python
# Rotate a key (marks old as inactive, creates new)
new_key_id, new_key = manager.rotate_key(old_key_id)
```

### Listing Keys

```python
# List all available keys with metadata
keys = manager.list_keys()
for key_meta in keys:
    print(f"Key {key_meta.key_id}: created {key_meta.created_at}, active={key_meta.is_active}")
```

## Security Layer

The `SuperBitSecurityLayer` class provides encryption and decryption operations.

### Encrypting Streams

```python
from src.null_system.extensions import SuperBitSecurityLayer

security = SuperBitSecurityLayer(key_manager=manager)

# Encrypt a super-bit stream
ciphertext, key_id, nonce, tag = security.encrypt_stream(stream, key_id="key-123")

# Store encrypted data
metadata = {
    "key_id": key_id,
    "nonce": nonce.hex(),
    "tag": tag.hex()
}
```

### Decrypting Streams

```python
# Decrypt a stream
stream = security.decrypt_stream(ciphertext, key_id, nonce, tag)
```

### Secure Messaging

```python
# Encrypt a message
message = "Secret message"
ciphertext, key_id, nonce, tag = security.encrypt_message(message)

# Decrypt a message
message = security.decrypt_message(ciphertext, key_id, nonce, tag)
```

### File Encryption

```python
from pathlib import Path

# Encrypt a file
input_file = Path("program.null")
encrypted_file = Path("program.encrypted")
metadata = security.encrypt_file(input_file, encrypted_file, key_id="key-123")

# Decrypt a file
output_file = Path("program.decrypted")
security.decrypt_file(encrypted_file, output_file, metadata)
```

## Opcode Remapping

```python
# Generate opcode mapping from a key
mapping = security.remap_opcodes(key_id="key-123")

# Mapping example:
# {
#     "LOAD_CONST": "0x1234567890abcdef",
#     "BINARY_ADD": "0xfedcba0987654321",
#     ...
# }
```

## CLI Usage

### Compile with Encryption

```bash
# Compile with production security profile
nullc compile --security-profile prod program.null -o program.bin

# Compile with specific key ID
nullc compile --security-profile prod --key-id key-123 program.null

# Create key if one doesn't exist
# (automatically done with prod profile)
```

### Run with Encryption

```bash
# Run with production profile (auto-decrypts)
nullc run --security-profile prod program.null

# Specify key ID
nullc run --security-profile prod --key-id key-123 program.null
```

### Key Management Commands

```bash
# List all keys
nullc keys list

# Create a new key
nullc keys create --password my_secret_password

# Rotate a key
nullc keys rotate key-123

# Show key info
nullc keys show key-123
```

## Configuration

### Key Storage Location

By default, keys are stored in `~/.null_security/`. You can customize this:

```python
from pathlib import Path
from src.null_system.extensions import KeyManager

manager = KeyManager(config_dir=Path("/custom/path"))
```

### Encryption Config

Customize encryption parameters:

```python
from src.null_system.extensions import EncryptionConfig, SuperBitSecurityLayer

config = EncryptionConfig(
    algorithm="AES-256-GCM",
    key_derivation="PBKDF2",
    iterations=200000,  # PBKDF2 iterations
    salt_length=16,
    nonce_length=12,
    tag_length=16
)

security = SuperBitSecurityLayer(key_manager=manager, config=config)
```

## Security Considerations

### Key Protection
- Keys are stored as plain files in `~/.null_security/`
- Use file system permissions to protect the directory
- Consider using full-disk encryption for sensitive systems
- Password-derived keys use PBKDF2 with 100,000 iterations by default

### Nonce Management
- Each encryption operation generates a unique nonce
- Never reuse the same nonce with the same key
- The system automatically generates new nonces

### Authentication
- AES-GCM provides authenticated encryption
- Authentication tag is stored and verified during decryption
- Tampering with encrypted data will cause decryption to fail

### Key Rotation
- Regularly rotate keys for production systems
- Old keys are marked inactive but retained for decryption of old data
- Plan rotation schedules carefully

## Best Practices

1. **Use Strong Passwords**: If deriving keys from passwords, use long, random passwords
2. **Secure Key Storage**: Protect the `.null_security` directory with appropriate file permissions
3. **Regular Rotation**: Implement a key rotation schedule for production systems
4. **Separate Keys**: Use different keys for different environments (dev, staging, prod)
5. **Backup Keys**: Maintain secure backups of encryption keys
6. **Monitor Access**: Log and monitor who creates, rotates, or uses keys

## Integration with Compression

Security and compression can be used together:

```bash
# Compile with both compression and encryption
nullc compile --compress high --security-profile prod program.null -o program.bin

# Run with both (transparently decompresses and decrypts)
nullc run --compress high --security-profile prod program.null
```

The metadata stored with each binary includes information about both compression and encryption, allowing the runtime to transparently handle both operations.

## Examples

### Complete Workflow

```python
from pathlib import Path
from src.null_system.extensions import KeyManager, SuperBitSecurityLayer
from src.null_system.compiler import NullCompiler

# 1. Create key manager
manager = KeyManager()

# 2. Create a new encryption key
key_id, _ = manager.create_key(password="production_key")

# 3. Compile program
compiler = NullCompiler()
artifact = compiler.compile(open("program.null").read())

# 4. Encrypt the binary
security = SuperBitSecurityLayer(key_manager=manager)
ciphertext, key_id, nonce, tag = security.encrypt_stream(
    artifact.superbit_stream,
    key_id=key_id
)

# 5. Store encrypted program
import json
metadata = {
    "key_id": key_id,
    "nonce": nonce.hex(),
    "tag": tag.hex(),
    "algorithm": "AES-256-GCM"
}

binary_file = Path("program.encrypted")
binary_file.write_bytes(ciphertext)

metadata_file = Path("program.metadata.json")
metadata_file.write_text(json.dumps(metadata))

# 6. Later: decrypt and run
import json
metadata = json.load(open("program.metadata.json"))
ciphertext = Path("program.encrypted").read_bytes()

decrypted_stream = security.decrypt_stream(
    ciphertext,
    metadata["key_id"],
    bytes.fromhex(metadata["nonce"]),
    bytes.fromhex(metadata["tag"])
)

# 7. Execute
vm = NullVM()
result = vm.execute(decrypted_stream)
```
