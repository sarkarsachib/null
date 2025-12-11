# Null-Lang Architecture

## Overview

The Null-Lang system is organized into five distinct architectural layers, each handling a specific aspect of language processing and representation. These layers form a complete pipeline from human-readable English-like syntax to optimized binary encoding.

## Five-Layer Architecture

### Layer 1: Lexical & Grammar (Lang)
**Location**: `src/null_system/lang/`

The foundational layer responsible for parsing English-like syntax into an Abstract Syntax Tree (AST).

**Components**:
- **grammar.lark**: Lark grammar definition for Null-Lang syntax
- **parser.py**: Transformer that converts parse trees into AST nodes
- **ast_nodes.py**: AST node class definitions (Commands, Expressions, Literals)
- **errors.py**: Error handling with source location tracking

**Key Features**:
- Lexical analysis (tokenization)
- Syntactic analysis (parsing)
- AST construction with span tracking for error reporting
- Support for comments, operators, and complex expressions

**Built-in Commands**: SET, ADD, IF/THEN/ELSE, SHOW, REPEAT, DEFINE

---

### Layer 2: Data Representation (Data)
**Location**: `src/null_system/data/`

Defines the fundamental data types and their runtime representations.

**Components**:
- **types.py**: Core data type classes (TEXT, NUM, BOOL, ARRAY, OBJECT)
- Serialization/deserialization helpers
- Type conversion utilities

**Supported Types**:
- `TEXT`: String values with encoding support
- `NUM`: Integer and floating-point numbers
- `BOOL`: Boolean values (TRUE/FALSE)
- `ARRAY`: Ordered collections
- `OBJECT`: Key-value mappings

**Key Responsibilities**:
- Provide runtime type representation
- Handle type conversions
- Support serialization to Super-Bit streams

---

### Layer 3: Super-Bit Encoding (Super-Bit)
**Location**: `src/null_system/superbit/`

Transforms high-level AST and data types into compact 4-8 bit grouped binary representations.

**Components**:
- **tokens.py**: `SuperBitToken` and `SuperBitGroup` data classes
- **registry.py**: Symbol and command registry with mapping tables
- **encoder.py**: Converts AST/data types to Super-Bit groups
- **decoder.py**: Reconstructs AST/data from Super-Bit groups

**Key Concepts**:
- **SuperBitToken**: Atomic unit representing a single symbol/command
- **SuperBitGroup**: 4-8 bit container for multiple tokens or packed data
- **Registry**: Central mapping between symbols and bit patterns
- **Encoder**: Transforms high-level constructs to bit groups
- **Decoder**: Reconstructs constructs from bit groups

**Features**:
- Efficient 4-8 bit encoding for commands and literals
- Extensible registry for custom symbols
- Support for compression hooks
- Support for encryption hooks
- Hooks for fuzzy-bit extensions

---

### Layer 4: Compression & Optimization
**Location**: `src/null_system/compress/` (future)

Applies compression algorithms to reduce encoded size.

**Planned Features**:
- Run-length encoding
- Dictionary-based compression
- Frequency analysis
- Huffman coding integration

---

### Layer 5: Security & Encryption
**Location**: `src/null_system/security/` (future)

Applies encryption and security mechanisms to protect encoded data.

**Planned Features**:
- Encryption hooks for Super-Bit streams
- Key management
- Digital signatures
- Fuzzy-bit extensions for obfuscation

---

## Data Flow

```
Source Code (Null-Lang)
       ↓
  [Layer 1: Lexical & Grammar]
       ↓
    AST Nodes
       ↓
  [Layer 2: Data Representation]
       ↓
   Data Types
       ↓
  [Layer 3: Super-Bit Encoding]
       ↓
  Super-Bit Groups (4-8 bits)
       ↓
  [Layer 4: Compression] (optional)
       ↓
  Compressed Data
       ↓
  [Layer 5: Security] (optional)
       ↓
  Encrypted Data
```

## Integration Points

### Lang ↔ Super-Bit
- AST nodes mapped to Super-Bit tokens
- Commands (SET, ADD, IF, etc.) have fixed bit patterns
- Literals encoded based on type and value

### Data ↔ Super-Bit
- Data types serialized to byte streams
- Super-Bit encoder handles type information
- Decoder reconstructs typed values with preservation of data

### Super-Bit ↔ Compression/Security
- Extensibility hooks for post-processing
- Registry-based system allows plugin architecture
- Stream-based encoding enables pipeline processing

## Symbol Registry

The Super-Bit layer maintains a comprehensive registry of:

**Keywords** (4-6 bits):
- Commands: SET, ADD, IF, THEN, ELSE, SHOW, REPEAT, DEFINE
- Keywords: AND, OR, NOT, TO, WITH, TIMES, END
- Type indicators: TEXT, NUM, BOOL, ARRAY, OBJECT

**Operators** (3-4 bits):
- Arithmetic: PLUS, MINUS, TIMES, DIVIDED_BY
- Comparison: IS, IS_NOT, GREATER, LESS, EQUAL
- Logical: AND, OR, NOT

**Special Symbols** (2-4 bits):
- Brackets, punctuation, delimiters
- Type markers, escape sequences
- Extensible custom symbols

## Encoding Strategy

### Commands (4-6 bits)
```
Example: SET command = 0b0001_01
         ADD command = 0b0001_10
         IF command  = 0b0010_00
```

### Literals (Variable bits)
```
TEXT:    Type (3 bits) + Length (variable) + Data
NUM:     Type (3 bits) + Value (32-64 bits)
BOOL:    Type (3 bits) + Value (1 bit)
ARRAY:   Type (3 bits) + Count (8 bits) + Elements
OBJECT:  Type (3 bits) + Count (8 bits) + Key-Value pairs
```

### Special Features
- **Fuzzy-Bit Extensions**: Allow bit groups to be reinterpreted under different contexts
- **Compression Hooks**: Register custom compression algorithms
- **Encryption Hooks**: Integrate encryption at the bit group level

## Extension Points

### Adding Custom Symbols
1. Register symbol in `registry.py`
2. Implement encoding logic in `encoder.py`
3. Implement decoding logic in `decoder.py`

### Compression Integration
1. Implement compression function
2. Register with `CompressionRegistry`
3. Chain in encoding pipeline

### Encryption Integration
1. Implement encryption function
2. Register with `EncryptionRegistry`
3. Apply during finalization

## Performance Considerations

- **Small Encoding**: 4-8 bit groups reduce size to ~10% of source
- **Fast Decoding**: Registry lookup provides O(1) symbol resolution
- **Stream Processing**: Encoder/decoder work with streams for memory efficiency
- **Extensibility**: Plugin architecture avoids monolithic design
