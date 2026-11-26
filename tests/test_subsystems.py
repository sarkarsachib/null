"""Tests for the formerly blocked subsystems (Phase 1-4 deliverables).

Covers:
- AI super-bit core (inference, IR optimisation, quantization, distributed runs)
- Debugger (breakpoints, conditions, stepping, frames)
- Visualizer (AST/execution diagrams, HTML, SVG export, snapshots)
- NLP/knowledge layer (semantics, graph, queries, cross references, search)
- Quantum simulator (gates, measurement, SuperBit encoding, hybrid execution)
- Secure compression (compression, AEAD roundtrip, KDF, analysis)
- Network storage (object API, locality, replication, snapshots, analytics)
- LSP (definition, references, debug start)
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

from null_system.ai import AIInferenceEngine
from null_system.ai.core import AIModelError
from null_system.compression.secure_compression import (
    SecureCompressionError,
    SecureCompressor,
)
from null_system.debugger import Debugger, DebuggerError
from null_system.lang.parser import parse
from null_system.lang.syntax_router import SyntaxMode
from null_system.lsp import NullLspServer
from null_system.nlp.layer import NLPLayer
from null_system.quantum import QuantumSimulator
from null_system.storage.network_store import NetworkStore, StorageError
from null_system.superbit.ir import SuperBitIRToken, SuperBitOpCode, SuperBitStream
from null_system.visualizer import Visualizer


# ---------------------------------------------------------------------------
# AI core
# ---------------------------------------------------------------------------
def _write_model(path: Path) -> Path:
    model = {
        "metadata": {"name": "tiny"},
        "layers": [
            {
                "type": "dense",
                "name": "hidden",
                "weights": [[1.0, -1.0], [0.5, 0.25]],
                "bias": [0.0, 0.1],
                "activation": "relu",
            },
            {
                "type": "dense",
                "name": "output",
                "weights": [[1.0, 2.0]],
                "bias": [0.0],
                "activation": "linear",
            },
        ],
    }
    path.write_text(json.dumps(model), encoding="utf-8")
    return path


class TestAICore:
    def test_load_and_infer(self, tmp_path: Path) -> None:
        engine = AIInferenceEngine(str(_write_model(tmp_path / "model.json")))
        output = engine.infer([1.0, 2.0])
        # hidden: [1*1 + (-1)*2, 0.5*1 + 0.25*2] + bias -> [-1, 1.1] -> relu [0, 1.1]
        # output: [1*0 + 2*1.1] = [2.2]
        assert output == pytest.approx([2.2])

    def test_batch_and_distributed_inference_match(self, tmp_path: Path) -> None:
        engine = AIInferenceEngine(str(_write_model(tmp_path / "model.json")))
        samples = [[1.0, 0.0], [0.0, 1.0], [1.0, 1.0], [2.0, 3.0]]
        sequential = engine.infer_batch(samples)
        distributed = engine.distributed_infer(samples, workers=3)
        assert len(distributed) == len(sequential) == len(samples)
        for left, right in zip(distributed, sequential):
            assert left == pytest.approx(right)

    def test_save_roundtrip(self, tmp_path: Path) -> None:
        engine = AIInferenceEngine(str(_write_model(tmp_path / "model.json")))
        target = tmp_path / "saved.json"
        engine.save_model(str(target))
        reloaded = AIInferenceEngine(str(target))
        assert reloaded.infer([1.0, 2.0]) == pytest.approx(engine.infer([1.0, 2.0]))

    def test_missing_model_raises(self, tmp_path: Path) -> None:
        with pytest.raises(AIModelError):
            AIInferenceEngine(str(tmp_path / "nope.json"))

    def test_quantization_roundtrip(self, tmp_path: Path) -> None:
        engine = AIInferenceEngine(str(_write_model(tmp_path / "model.json")))
        before = engine.infer([1.0, 2.0])
        engine.quantize(bits=8)
        assert engine.quantized
        quantized = engine.quantized_forward([1.0, 2.0])
        assert quantized == pytest.approx(before, abs=0.2)
        engine.dequantize()
        assert engine.infer([1.0, 2.0]) == pytest.approx(before)

    def test_prune_and_sparsity(self, tmp_path: Path) -> None:
        engine = AIInferenceEngine(str(_write_model(tmp_path / "model.json")))
        pruned = engine.prune(threshold=0.4)
        assert pruned >= 1
        assert engine.sparsity() > 0

    def test_optimize_ir_folds_constants(self, tmp_path: Path) -> None:
        engine = AIInferenceEngine(str(_write_model(tmp_path / "model.json")))
        stream = SuperBitStream(
            tokens=[
                SuperBitIRToken(SuperBitOpCode.LOAD_CONST, 2),
                SuperBitIRToken(SuperBitOpCode.LOAD_CONST, 3),
                SuperBitIRToken(SuperBitOpCode.BINARY_ADD),
                SuperBitIRToken(SuperBitOpCode.NOP),
            ]
        )
        optimized = engine.optimize_ir(stream)
        assert [token.opcode for token in optimized.tokens] == [SuperBitOpCode.LOAD_CONST]
        assert optimized.tokens[0].operand == 5

    def test_summary(self, tmp_path: Path) -> None:
        engine = AIInferenceEngine(str(_write_model(tmp_path / "model.json")))
        summary = engine.summary()
        assert summary["parameters"] > 0
        assert summary["layers"][0]["activation"] == "relu"


# ---------------------------------------------------------------------------
# Debugger
# ---------------------------------------------------------------------------
def _compile(source: str) -> SuperBitStream:
    from null_system.compiler import NullCompiler

    return NullCompiler().compile(source).superbit_stream


class TestDebugger:
    def test_breakpoint_stops_before_executing_line(self) -> None:
        source = "set x to 5\nprint x"
        debugger = Debugger(_compile(source), source=source)
        debugger.set_breakpoint(1)

        frame = debugger.continue_execution()
        assert frame is not None
        assert frame.line == 1
        assert debugger.get_output() == []

        debugger.step_into()  # LOAD_CONST 5
        debugger.step_into()  # STORE_VAR x
        assert debugger.get_locals().get("x") == 5

        debugger.set_breakpoint(2)
        frame = debugger.continue_execution()
        assert frame is not None and frame.line == 2
        debugger.step_into()  # LOAD_VAR x
        debugger.step_into()  # PRINT
        assert debugger.get_output() == ["5"]

    def test_step_into_advances_instruction(self) -> None:
        debugger = Debugger(_compile("set x to 5\nprint x"), source="set x to 5\nprint x")
        first = debugger.start()
        executed = debugger.step_into()
        second = debugger.step_into()
        assert first.pc == 0
        assert executed is not None and executed.pc == 0
        assert second is not None and second.pc == 1

    def test_conditional_breakpoint(self) -> None:
        source = "set x to 1\nset x to 2\nset x to 3"
        debugger = Debugger(_compile(source), source=source)
        debugger.set_breakpoint(3, "x == 2")

        frame = debugger.continue_execution()
        assert frame is not None
        assert frame.variables["x"] == 2

    def test_clear_breakpoints(self) -> None:
        debugger = Debugger(_compile("set x to 1"), source="set x to 1")
        debugger.set_breakpoint(1)
        debugger.clear_breakpoint(1)
        assert debugger.list_breakpoints() == []
        assert debugger.continue_execution() is None

    def test_invalid_condition_is_rejected(self) -> None:
        debugger = Debugger(_compile("set x to 1"), source="set x to 1")
        with pytest.raises(DebuggerError):
            debugger.set_breakpoint(1, "__import__('os')")

    def test_snapshot_contains_state(self) -> None:
        debugger = Debugger(_compile("set x to 1\nprint x"), source="set x to 1\nprint x")
        debugger.set_breakpoint(2)
        debugger.continue_execution()
        snapshot = debugger.snapshot()
        assert snapshot["frame"]["line"] == 2
        assert snapshot["breakpoints"][0]["line"] == 2


# ---------------------------------------------------------------------------
# Visualizer
# ---------------------------------------------------------------------------
class TestVisualizer:
    def setup_method(self) -> None:
        self.ast = parse("SET x TO 1\nSHOW x")
        self.visualizer = Visualizer()

    def test_ast_mermaid(self) -> None:
        diagram = self.visualizer.visualize_ast(self.ast)
        assert diagram.startswith("graph TD")
        assert "Program" in diagram

    def test_ast_dot(self) -> None:
        diagram = self.visualizer.visualize_ast(self.ast, format="dot")
        assert diagram.startswith("digraph AST")

    def test_ast_json(self) -> None:
        payload = json.loads(self.visualizer.visualize_ast(self.ast, format="json"))
        assert payload["nodes"]

    def test_unsupported_format(self) -> None:
        with pytest.raises(Exception):
            self.visualizer.visualize_ast(self.ast, format="nope")

    def test_execution_flow(self) -> None:
        trace = [
            {"step": 0, "opcode": "LOAD_CONST", "source_line": 1},
            {"step": 1, "opcode": "STORE_VAR", "source_line": 1},
        ]
        diagram = self.visualizer.visualize_execution_flow(trace)
        assert "LOAD_CONST" in diagram and "STORE_VAR" in diagram

    def test_render_html_and_export(self, tmp_path: Path) -> None:
        diagram = self.visualizer.visualize_ast(self.ast)
        html = self.visualizer.render_html(diagram)
        assert "<!DOCTYPE html>" in html and "mermaid" in html

        svg_path = tmp_path / "ast.svg"
        self.visualizer.export_image(diagram, "svg", str(svg_path))
        assert svg_path.read_text(encoding="utf-8").startswith("<svg")

        mmd_path = tmp_path / "ast.mmd"
        self.visualizer.export_image(diagram, "mmd", str(mmd_path))
        assert "graph TD" in mmd_path.read_text(encoding="utf-8")

    def test_state_snapshot(self) -> None:
        diagram = self.visualizer.create_state_snapshot({"x": 5}, [5])
        assert "x = 5" in diagram and "Stack" in diagram


# ---------------------------------------------------------------------------
# NLP / knowledge layer
# ---------------------------------------------------------------------------
class TestNLPLayer:
    def test_semantic_analysis(self) -> None:
        layer = NLPLayer()
        analysis = layer.analyze_semantic_meaning(
            "SET total TO 0\nREPEAT 3 TIMES\nSET total TO total PLUS 1\nEND REPEAT",
            comments="add three numbers to the total",
        )
        assert "total" in analysis.identifiers
        assert analysis.keywords["REPEAT"] >= 1
        assert analysis.cyclomatic_complexity >= 2
        assert analysis.summary

    def test_knowledge_graph_from_source(self) -> None:
        layer = NLPLayer()
        graph = layer.build_graph_from_source("DEFINE greet WITH name\nSHOW name\nEND DEFINE\nSET x TO greet")
        entities = graph.list_entities()
        assert entities
        types = {entity.type for entity in entities}
        assert {"program", "statement"} <= types

        functions = [e for e in entities if e.type == "function"]
        assert functions and functions[0].properties["name"] == "greet"

        results = layer.query_knowledge_graph("type:function")
        assert len(results) == 1

        results = layer.query_knowledge_graph("greet")
        assert results

    def test_cross_references(self) -> None:
        layer = NLPLayer()
        references = layer.cross_references("SET counter TO 0\nSET counter TO counter PLUS 1\nSHOW counter")
        assert references["counter"] == [2, 3]

    def test_semantic_search(self) -> None:
        layer = NLPLayer()
        codebase = {
            "math.null": "SET total TO 0\nADD total AND 5",
            "greeting.null": "SHOW \"hello world\"",
        }
        matches = layer.semantic_search("greeting hello world", codebase, limit=2)
        assert matches
        assert matches[0].path == "greeting.null"
        assert isinstance(matches[0].to_dict()["score"], float)


# ---------------------------------------------------------------------------
# Quantum simulator
# ---------------------------------------------------------------------------
class TestQuantum:
    def test_bell_pair_is_correlated(self) -> None:
        simulator = QuantumSimulator(seed=7)
        circuit = simulator.create_circuit(2).h(0).cx(0, 1).measure_all()
        results = simulator.execute_circuit(circuit, shots=200)
        assert set(results.counts) <= {"00", "11"}
        assert results.counts.get("00", 0) > 40
        assert results.counts.get("11", 0) > 40

    def test_x_gate_is_deterministic(self) -> None:
        simulator = QuantumSimulator(seed=1)
        circuit = simulator.create_circuit(1).x(0).measure_all()
        results = simulator.execute_circuit(circuit, shots=10)
        assert results.counts == {"1": 10}

    def test_probabilities(self) -> None:
        simulator = QuantumSimulator()
        circuit = simulator.create_circuit(1).h(0)
        probabilities = simulator.probabilities(circuit)
        assert probabilities["0"] == pytest.approx(0.5)
        assert probabilities["1"] == pytest.approx(0.5)

    def test_superbit_roundtrip(self) -> None:
        simulator = QuantumSimulator()
        circuit = simulator.create_circuit(2).h(0).cx(0, 1).rz(1, math.pi / 4).measure_all()
        stream = simulator.encode_to_superbit(circuit)
        decoded = simulator.decode_from_superbit(stream)
        assert decoded.qubits == circuit.qubits
        assert [op.name for op in decoded.operations] == [op.name for op in circuit.operations]
        assert stream.to_bytes()

    def test_invalid_qubit(self) -> None:
        simulator = QuantumSimulator()
        circuit = simulator.create_circuit(1)
        with pytest.raises(Exception):
            circuit.h(2)

    def test_hybrid_execute(self) -> None:
        simulator = QuantumSimulator(seed=3)
        circuit = simulator.create_circuit(1).h(0).measure_all()
        result = simulator.hybrid_execute("set x to 2\nshow x", circuit, shots=16)
        assert result["classical"]["success"] is True
        assert "2" in result["classical"]["output"]
        assert sum(result["quantum"]["counts"].values()) == 16
        assert result["dominant_outcome"] in {"0", "1"}


# ---------------------------------------------------------------------------
# Secure compression
# ---------------------------------------------------------------------------
class TestSecureCompression:
    def test_compress_roundtrip(self) -> None:
        compressor = SecureCompressor()
        payload = b"null-lang " * 500
        compressed = compressor.compress(payload)
        assert len(compressed) < len(payload)
        assert compressor.decompress(compressed) == payload

    def test_empty_payload(self) -> None:
        compressor = SecureCompressor()
        assert compressor.decompress(compressor.compress(b"")) == b""

    def test_encrypt_roundtrip(self) -> None:
        compressor = SecureCompressor()
        if not compressor.supports_encryption():
            pytest.skip("cryptography is not installed")
        payload = b"secret payload" * 100
        key = b"k" * 32
        blob = compressor.compress_and_encrypt(payload, key)
        assert compressor.decrypt_and_decompress(blob, key) == payload

    def test_wrong_key_fails(self) -> None:
        compressor = SecureCompressor()
        if not compressor.supports_encryption():
            pytest.skip("cryptography is not installed")
        blob = compressor.compress_and_encrypt(b"data", b"a" * 32)
        with pytest.raises(SecureCompressionError):
            compressor.decrypt_and_decompress(blob, b"b" * 32)

    def test_tampering_is_detected(self) -> None:
        compressor = SecureCompressor()
        if not compressor.supports_encryption():
            pytest.skip("cryptography is not installed")
        blob = bytearray(compressor.compress_and_encrypt(b"data" * 10, b"a" * 32))
        blob[-1] ^= 0x01
        with pytest.raises(SecureCompressionError):
            compressor.decrypt_and_decompress(bytes(blob), b"a" * 32)

    def test_key_derivation_is_deterministic(self) -> None:
        compressor = SecureCompressor()
        salt = b"0123456789abcdef"
        first = compressor.derive_key("hunter2", salt)
        second = compressor.derive_key("hunter2", salt)
        assert first == second and len(first) == 32
        assert compressor.derive_key("hunter3", salt) != first

    def test_ratio_estimation(self) -> None:
        compressor = SecureCompressor()
        assert compressor.estimate_compression_ratio(b"a" * 10_000) < 0.5
        assert compressor.estimate_compression_ratio(b"") == 1.0

    def test_corrupt_payload_raises(self) -> None:
        compressor = SecureCompressor()
        with pytest.raises(SecureCompressionError):
            compressor.decompress(b"NSC1garbage")


# ---------------------------------------------------------------------------
# Network storage
# ---------------------------------------------------------------------------
class TestNetworkStore:
    def test_memory_put_get_list_delete(self) -> None:
        store = NetworkStore("memory", "bucket")
        etag = store.put("a/b.txt", b"hello", {"kind": "text"})
        assert len(etag) == 64  # sha256 hex digest
        assert store.get("a/b.txt") == b"hello"

        listed = store.list("a/")
        assert [obj.key for obj in listed] == ["a/b.txt"]
        assert listed[0].metadata["kind"] == "text"

        store.delete("a/b.txt")
        with pytest.raises(FileNotFoundError):
            store.get("a/b.txt")

    def test_filesystem_backend(self, tmp_path: Path) -> None:
        store = NetworkStore(str(tmp_path), "bucket")
        store.put("x.null", b"SET x TO 1")
        assert store.get("x.null") == b"SET x TO 1"
        assert store.exists("x.null")
        assert [obj.key for obj in store.list()] == ["x.null"]

        snapshot = store.create_snapshot("x.null")
        store.put("x.null", b"SET x TO 2")
        store.restore_from_snapshot(snapshot)
        assert store.get("x.null") == b"SET x TO 1"

    def test_replication_and_recovery(self, tmp_path: Path) -> None:
        store = NetworkStore(str(tmp_path), "bucket", replicas=2)
        store.put("k", b"payload")
        assert store.replicate("k") == 2

        (tmp_path / "bucket" / "k").unlink()
        assert store.recover("k") is True
        assert store.get("k") == b"payload"

    def test_locality_cache_and_stats(self) -> None:
        store = NetworkStore("memory", "bucket", cache_size=2)
        for key in ("a", "b", "c"):
            store.put(key, b"value")
        for _ in range(3):
            store.get("a")
        store.get("b")

        cached = store.optimize_locality("hot")
        assert "a" in cached

        stats = store.stats()
        assert stats["objects"] == 3
        assert stats["gets"] == 4
        assert stats["cache_hit_rate"] > 0
        assert store.recommend(limit=1) == ["a"]

    def test_invalid_key_rejected(self) -> None:
        store = NetworkStore("memory", "bucket")
        with pytest.raises(ValueError):
            store.put("../escape", b"x")

    def test_unsupported_endpoint_backend(self) -> None:
        with pytest.raises((StorageError, ValueError)):
            NetworkStore("http://localhost", "bucket", backend="unknown")


# ---------------------------------------------------------------------------
# LSP
# ---------------------------------------------------------------------------
class TestLspFeatures:
    def _server(self, source: str) -> NullLspServer:
        from null_system.lsp.server import DocumentState, create_server

        server = create_server()
        server._documents["file:///test.null"] = DocumentState(
            uri="file:///test.null", text=source, mode=SyntaxMode.english
        )
        return server

    def test_definition_and_references(self) -> None:
        from lsprotocol.types import (
            DefinitionParams,
            Position,
            ReferenceContext,
            ReferenceParams,
            TextDocumentIdentifier,
        )

        from null_system.lsp.server import definition, references

        source = "SET total TO 0\nSET total TO total PLUS 1"
        server = self._server(source)

        def_params = DefinitionParams(
            text_document=TextDocumentIdentifier(uri="file:///test.null"),
            position=Position(line=1, character=5),
        )
        location = definition(server, def_params)
        assert location is not None
        assert location.range.start.line == 0

        ref_params = ReferenceParams(
            text_document=TextDocumentIdentifier(uri="file:///test.null"),
            position=Position(line=0, character=5),
            context=ReferenceContext(include_declaration=True),
        )
        locations = references(server, ref_params)
        assert {loc.range.start.line for loc in locations} == {0, 1}

    def test_debug_start(self) -> None:
        from null_system.lsp.server import debug_start

        server = self._server("set x to 1\nprint x")
        response = debug_start(
            server,
            {
                "uri": "file:///test.null",
                "breakpoints": [{"line": 2}],
            },
        )
        assert response["ok"] is True
        assert response["frame"]["line"] == 1
        assert response["snapshot"]["breakpoints"][0]["line"] == 2
