import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from null_system.ast.nodes import (
    Pattern, MatchExpression, MatchCase, WhenGuard,
    Identifier, Literal, Program
)
from null_system.superbit.emitter import SuperBitEmitter
from null_system.superbit.ir import SuperBitOpCode
from null_system.vm.vm import NullVM


class PatternMatchingIntegrationTests(unittest.TestCase):

    def test_match_expression_emits_opcodes(self):
        pattern = Pattern(pattern_type="tag", tag="Some")
        case = MatchCase(
            pattern=pattern,
            body=[Literal(value="matched")]
        )
        match_expr = MatchExpression(
            expr=Identifier(name="opt"),
            cases=[case]
        )
        program = Program(statements=[match_expr])

        emitter = SuperBitEmitter()
        stream = emitter.emit(program)

        tokens = list(stream)
        self.assertTrue(len(tokens) > 0)
        self.assertIn(SuperBitOpCode.LOAD_VAR, [t.opcode for t in tokens])
        self.assertIn(SuperBitOpCode.MATCH_TAG, [t.opcode for t in tokens])

    def test_pattern_with_binding_emits_store_var(self):
        pattern = Pattern(
            pattern_type="tag",
            tag="Some",
            binding_name="value"
        )
        case = MatchCase(
            pattern=pattern,
            body=[Literal(value="ok")]
        )
        match_expr = MatchExpression(
            expr=Identifier(name="opt"),
            cases=[case]
        )
        program = Program(statements=[match_expr])

        emitter = SuperBitEmitter()
        stream = emitter.emit(program)

        tokens = list(stream)
        store_vars = [t for t in tokens if t.opcode == SuperBitOpCode.STORE_VAR]
        self.assertTrue(any(t.operand == "value" for t in store_vars))

    def test_match_with_guard_emits_conditional_jump(self):
        pattern = Pattern(pattern_type="tag", tag="Ok")
        guard = WhenGuard(condition=Identifier(name="x"))
        case = MatchCase(
            pattern=pattern,
            guard=guard,
            body=[Literal(value="true")]
        )
        match_expr = MatchExpression(
            expr=Identifier(name="result"),
            cases=[case]
        )
        program = Program(statements=[match_expr])

        emitter = SuperBitEmitter()
        stream = emitter.emit(program)

        tokens = list(stream)
        jumps = [t for t in tokens if t.opcode == SuperBitOpCode.JUMP_IF_FALSE]
        self.assertTrue(len(jumps) > 0)

    def test_multiple_match_cases(self):
        pattern1 = Pattern(pattern_type="tag", tag="Some")
        case1 = MatchCase(pattern=pattern1, body=[Literal(value="some")])
        
        pattern2 = Pattern(pattern_type="tag", tag="None")
        case2 = MatchCase(pattern=pattern2, body=[Literal(value="none")])
        
        match_expr = MatchExpression(
            expr=Identifier(name="opt"),
            cases=[case1, case2]
        )
        program = Program(statements=[match_expr])

        emitter = SuperBitEmitter()
        stream = emitter.emit(program)

        tokens = list(stream)
        match_tags = [t for t in tokens if t.opcode == SuperBitOpCode.MATCH_TAG]
        self.assertEqual(len(match_tags), 2)
        self.assertEqual(match_tags[0].operand, "Some")
        self.assertEqual(match_tags[1].operand, "None")

    def test_vm_executes_match_tag_opcode(self):
        from null_system.superbit.ir import SuperBitIRToken, SuperBitStream
        from null_system.types import some_val, NullNumber

        tokens = [
            SuperBitIRToken(opcode=SuperBitOpCode.LOAD_CONST, operand=some_val(NullNumber(42.0))),
            SuperBitIRToken(opcode=SuperBitOpCode.MATCH_TAG, operand="Some"),
        ]
        stream = SuperBitStream(tokens=tokens)

        vm = NullVM()
        result = vm.execute(stream)

        self.assertTrue(result.success)
        self.assertEqual(len(vm.stack), 1)
        self.assertTrue(vm.stack[0])

    def test_vm_executes_match_tag_false(self):
        from null_system.superbit.ir import SuperBitIRToken, SuperBitStream
        from null_system.types import some_val, NullNumber

        tokens = [
            SuperBitIRToken(opcode=SuperBitOpCode.LOAD_CONST, operand=some_val(NullNumber(42.0))),
            SuperBitIRToken(opcode=SuperBitOpCode.MATCH_TAG, operand="None"),
        ]
        stream = SuperBitStream(tokens=tokens)

        vm = NullVM()
        result = vm.execute(stream)

        self.assertTrue(result.success)
        self.assertEqual(len(vm.stack), 1)
        self.assertFalse(vm.stack[0])

    def test_vm_executes_unwrap_union(self):
        from null_system.superbit.ir import SuperBitIRToken, SuperBitStream
        from null_system.types import some_val, NullNumber

        tokens = [
            SuperBitIRToken(opcode=SuperBitOpCode.LOAD_CONST, operand=some_val(NullNumber(42.0))),
            SuperBitIRToken(opcode=SuperBitOpCode.UNWRAP_UNION, operand=None),
        ]
        stream = SuperBitStream(tokens=tokens)

        vm = NullVM()
        result = vm.execute(stream)

        self.assertTrue(result.success)
        self.assertEqual(len(vm.stack), 1)
        self.assertEqual(vm.stack[0].as_number(), 42.0)

    def test_vm_match_pattern_opcode(self):
        from null_system.superbit.ir import SuperBitIRToken, SuperBitStream
        from null_system.types import ok_val, NullNumber

        tokens = [
            SuperBitIRToken(opcode=SuperBitOpCode.LOAD_CONST, operand=ok_val(NullNumber(42.0))),
            SuperBitIRToken(opcode=SuperBitOpCode.MATCH_PATTERN, operand="Ok"),
        ]
        stream = SuperBitStream(tokens=tokens)

        vm = NullVM()
        result = vm.execute(stream)

        self.assertTrue(result.success)
        self.assertEqual(len(vm.stack), 1)
        self.assertTrue(vm.stack[0])


if __name__ == "__main__":
    unittest.main()
