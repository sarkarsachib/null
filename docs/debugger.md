# Null-Lang Debugger

The Null-Lang debugger provides interactive debugging capabilities with multi-layer visibility into program execution, allowing you to see the correspondence between English source code, super-bit opcodes, and binary frames.

## Features

- **Breakpoint Management**: Set and remove breakpoints by source line number
- **Stepping**: Execute one instruction at a time
- **Multi-Layer State View**: See English code, super-bit opcodes, binary offsets, and VM state simultaneously
- **Watch Expressions**: Evaluate expressions in the current execution context
- **JSON Mode**: Programmatic debugging via JSON streaming

## Quick Start

### Launch the Debugger

```bash
nullc debug examples/conditional.null
```

This will start an interactive debugging session with the specified source file.

### Basic Workflow

1. **Set a breakpoint** at line 4:
   ```
   debug> b 4
   ```

2. **Run the program** until the breakpoint is hit:
   ```
   debug> r
   ```

3. **Step through** instructions one at a time:
   ```
   debug> s
   ```

4. **Print variable values**:
   ```
   debug> p age
   ```

5. **Continue execution**:
   ```
   debug> c
   ```

## Commands

| Command | Aliases | Description |
|---------|---------|-------------|
| `run` | `r` | Run the program until a breakpoint or end |
| `continue` | `c`, `cont` | Continue execution from current position |
| `step` | `s` | Execute a single instruction |
| `next` | `n` | Step over (currently same as step) |
| `break [line]` | `b`, `breakpoint` | Set breakpoint or list breakpoints |
| `delete <line>` | `d` | Delete breakpoint at line |
| `print <expr>` | `p` | Evaluate and print expression |
| `list` | `l` | Show source code context |
| `info` | `i` | Show detailed execution state |
| `help` | `h` | Show help |
| `quit` | `q`, `exit` | Exit debugger |

## Multi-Layer State View

When execution is paused, the debugger displays:

### 1. Source Context
Shows the current line with surrounding context:
```
Source:
    2 | set age to 25
    3 |
→   4 | if age is greater than 18 then print 'adult' else print 'minor'
    5 |
```

### 2. Execution State
Shows the current instruction and VM state:
```
┌─ Execution State ──────────────┐
│ Component         │ Value       │
├───────────────────┼─────────────┤
│ PC (Instruction)  │ 6           │
│ Source Line       │ 4           │
│ Current OpCode    │ COMPARE_GT  │
│ Binary Offset     │ 0x0024      │
└───────────────────┴─────────────┘
```

### 3. Stack and Variables
Shows the current stack contents and variable values:
```
Stack: [25, 18]

┌─ Variables ──────┐
│ Name  │ Value    │
├───────┼──────────┤
│ age   │ 25       │
└───────┴──────────┘
```

## Breakpoints

### Setting Breakpoints

Set a breakpoint at a specific line:
```
debug> b 10
✓ Breakpoint set: Breakpoint(examples/conditional.null:10, enabled, hits=0)
```

### Listing Breakpoints

View all breakpoints:
```
debug> b
┌─ Breakpoints ──────────────────────────────┐
│ Line │ Instruction │ Status  │ Hits       │
├──────┼─────────────┼─────────┼────────────┤
│ 4    │ 6           │ enabled │ 1          │
│ 10   │ 12          │ enabled │ 0          │
└──────┴─────────────┴─────────┴────────────┘
```

### Deleting Breakpoints

Remove a breakpoint:
```
debug> d 10
✓ Breakpoint removed at line 10
```

## Watch Expressions

Evaluate expressions to inspect values:

```
debug> p age
age = 25

debug> p age is greater than 18
age is greater than 18 = True
```

Watch expressions support:
- Variable names
- Simple expressions (parsed through the Null-Lang parser)
- Access to current VM variable context

## JSON Mode

For programmatic debugging (e.g., IDE integration), use JSON mode:

```bash
nullc debug examples/conditional.null --json
```

### JSON Protocol

Send commands as JSON objects:

```json
{"command": "run"}
{"command": "step"}
{"command": "set_breakpoint", "line": 4}
{"command": "evaluate", "expression": "age"}
{"command": "exit"}
```

Receive state updates as JSON:

```json
{
  "pc": 6,
  "line": 4,
  "stack": [25, 18],
  "variables": {"age": 25},
  "output": [],
  "is_finished": false
}
```

## Example Debugging Session

Given `examples/conditional.null`:
```null
# Conditional logic example
set age to 25

if age is greater than 18 then print 'adult' else print 'minor'
```

### Session Transcript

```
$ nullc debug examples/conditional.null

Null Debugger - examples/conditional.null
Type 'help' for commands

✓ Program loaded successfully

debug> b 4
✓ Breakpoint set: Breakpoint(examples/conditional.null:4, enabled, hits=0)

debug> r

⚠ Breakpoint hit: Breakpoint(examples/conditional.null:4, enabled, hits=1)

Source:
    2 | set age to 25
    3 |
→   4 | if age is greater than 18 then print 'adult' else print 'minor'

┌─ Execution State ──────────────┐
│ Component         │ Value       │
├───────────────────┼─────────────┤
│ PC (Instruction)  │ 2           │
│ Source Line       │ 4           │
│ Current OpCode    │ LOAD_VAR    │
│ Operand           │ age         │
│ Binary Offset     │ 0x0010      │
└───────────────────┴─────────────┘

┌─ Variables ──────┐
│ Name  │ Value    │
├───────┼──────────┤
│ age   │ 25       │
└───────┴──────────┘

debug> p age
age = 25

debug> s

Source:
    2 | set age to 25
    3 |
→   4 | if age is greater than 18 then print 'adult' else print 'minor'

Stack: [25]

debug> c
✓ Program finished

Output:
  adult

debug> q
Exiting debugger
```

## Architecture

### Debugger Components

1. **Breakpoint**: Represents a breakpoint with file/line information and hit tracking
2. **InstructionDebugInfo**: Maps instructions to source locations and binary offsets
3. **NullDebuggerSession**: Main debugger session managing execution and state

### Source-to-Binary Mapping

The debugger maintains mappings at multiple levels:

```
English Source Line 4
    ↓
Super-bit Tokens [2..6]
    ↓
Binary Offsets 0x0010..0x0024
```

Each super-bit token carries a `SourceSpan` with:
- Filename
- Line number
- Column (optional)

This enables precise navigation between layers during debugging.

### VM Integration

The `NullVM` has been extended with:
- `step()`: Execute a single instruction
- `get_state()`: Snapshot current execution state
- `set_pc_moved_callback()`: Event notification when PC changes
- `load_program()`: Prepare program for debugging

## Best Practices

### Effective Debugging

1. **Set breakpoints early**: Place breakpoints before complex logic
2. **Use watch expressions**: Monitor variable changes between steps
3. **Check the stack**: Understand intermediate computation results
4. **View source context**: Always use `list` to see where you are

### Common Patterns

**Debug a conditional branch:**
```
debug> b 4
debug> r
debug> p condition_var
debug> s
```

**Track variable changes:**
```
debug> b 5
debug> r
debug> p x
debug> s
debug> p x
```

**Find where a variable is set:**
```
debug> b 10
debug> r
debug> i
```

## Limitations

Current limitations:
- No step-over/step-out for function calls (treated as step)
- Conditional breakpoints not yet supported
- No reverse debugging
- Watch expressions limited to simple expressions

## Future Enhancements

Planned features:
- Conditional breakpoints
- Watch points (break on variable change)
- Call stack navigation for functions
- Time-travel debugging
- Remote debugging support
