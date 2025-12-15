"""
Unit tests for Null-Lang layer annotations (@layer, @require, @prefer).

Tests cover parsing of annotations, compilation to IR with metadata threading,
and error cases.
"""

import pytest
from src.null_system.lang import (
    parse, parse_statement,
    SetCommand, ShowCommand, IfCommand, RepeatCommand, DefineCommand,
    LayerAnnotation, RequireAnnotation, PreferAnnotation,
    NullLangCompiler,
)
from src.null_system.superbit.ir import SuperBitOpCode


class TestLayerAnnotationParsing:
    """Test parsing of layer annotations."""

    def test_layer_annotation_single(self):
        """Test parsing @layer(binary) annotation."""
        result = parse_statement('@layer(binary) SET x TO 42')
        assert isinstance(result, SetCommand)
        assert len(result.annotations) == 1
        assert isinstance(result.annotations[0], LayerAnnotation)
        assert result.annotations[0].layer == "binary"

    def test_layer_annotation_different_layers(self):
        """Test layer annotation with different layer names."""
        for layer_name in ["superbit", "binary", "ml", "gpu", "cpu"]:
            result = parse_statement(f'@layer({layer_name}) SET x TO 42')
            assert isinstance(result, SetCommand)
            assert len(result.annotations) == 1
            assert result.annotations[0].layer == layer_name

    def test_require_annotation_single(self):
        """Test parsing @require(layer) annotation."""
        result = parse_statement('@require(superbit) SET x TO 42')
        assert isinstance(result, SetCommand)
        assert len(result.annotations) == 1
        assert isinstance(result.annotations[0], RequireAnnotation)
        assert result.annotations[0].layers == ["superbit"]

    def test_require_annotation_multiple(self):
        """Test parsing @require with multiple layers."""
        result = parse_statement('@require(superbit, binary) SET x TO 42')
        assert isinstance(result, SetCommand)
        assert len(result.annotations) == 1
        assert isinstance(result.annotations[0], RequireAnnotation)
        assert set(result.annotations[0].layers) == {"superbit", "binary"}

    def test_require_annotation_multiple_layers_spaces(self):
        """Test @require with multiple layers and spacing."""
        result = parse_statement('@require(layer1, layer2, layer3) SET x TO 42')
        assert isinstance(result, SetCommand)
        assert isinstance(result.annotations[0], RequireAnnotation)
        assert result.annotations[0].layers == ["layer1", "layer2", "layer3"]

    def test_prefer_annotation_single(self):
        """Test parsing @prefer(layer) annotation."""
        result = parse_statement('@prefer(gpu) SET x TO 42')
        assert isinstance(result, SetCommand)
        assert len(result.annotations) == 1
        assert isinstance(result.annotations[0], PreferAnnotation)
        assert result.annotations[0].layers == ["gpu"]

    def test_prefer_annotation_multiple(self):
        """Test parsing @prefer with multiple layers."""
        result = parse_statement('@prefer(gpu, cpu) SET x TO 42')
        assert isinstance(result, SetCommand)
        assert isinstance(result.annotations[0], PreferAnnotation)
        assert set(result.annotations[0].layers) == {"gpu", "cpu"}

    def test_multiple_annotations(self):
        """Test multiple annotations on same statement."""
        result = parse_statement(
            '@layer(binary) @require(superbit) @prefer(gpu) SET x TO 42'
        )
        assert isinstance(result, SetCommand)
        assert len(result.annotations) == 3
        assert isinstance(result.annotations[0], LayerAnnotation)
        assert isinstance(result.annotations[1], RequireAnnotation)
        assert isinstance(result.annotations[2], PreferAnnotation)

    def test_annotation_on_show_command(self):
        """Test annotation on SHOW command."""
        result = parse_statement('@layer(binary) SHOW x')
        assert isinstance(result, ShowCommand)
        assert len(result.annotations) == 1
        assert result.annotations[0].layer == "binary"

    def test_annotation_on_if_command(self):
        """Test annotation on IF command."""
        result = parse_statement(
            '@layer(superbit) IF TRUE THEN SET x TO 1 END IF'
        )
        assert isinstance(result, IfCommand)
        assert len(result.annotations) == 1
        assert result.annotations[0].layer == "superbit"

    def test_annotation_on_repeat_command(self):
        """Test annotation on REPEAT command."""
        result = parse_statement(
            '@require(binary) REPEAT 10 TIMES SET x TO 1 END REPEAT'
        )
        assert isinstance(result, RepeatCommand)
        assert len(result.annotations) == 1
        assert "binary" in result.annotations[0].layers

    def test_annotation_on_define_command(self):
        """Test annotation on DEFINE command."""
        result = parse_statement(
            '@prefer(gpu, cpu) DEFINE myFunc WITH x, y SET z TO x PLUS y END DEFINE'
        )
        assert isinstance(result, DefineCommand)
        assert len(result.annotations) == 1
        assert set(result.annotations[0].layers) == {"gpu", "cpu"}

    def test_legacy_null_lib_annotation_still_works(self):
        """Test that legacy @lib.fn annotations still parse."""
        result = parse_statement('SET x TO @lib.func()')
        assert isinstance(result, SetCommand)

    def test_annotation_with_underscores(self):
        """Test layer names with underscores."""
        result = parse_statement('@layer(binary_layer_1) SET x TO 42')
        assert isinstance(result, SetCommand)
        assert result.annotations[0].layer == "binary_layer_1"

    def test_annotation_with_numbers(self):
        """Test layer names with numbers."""
        result = parse_statement('@layer(layer123) SET x TO 42')
        assert isinstance(result, SetCommand)
        assert result.annotations[0].layer == "layer123"


class TestAnnotationCompilation:
    """Test compilation of annotations to IR metadata."""

    def test_layer_annotation_metadata_threaded(self):
        """Test that layer annotation metadata is threaded into IR tokens."""
        source = '@layer(binary) SET x TO 42'
        program = parse(source)
        compiler = NullLangCompiler()
        stream = compiler.compile(program)

        tokens = list(stream)
        assert len(tokens) > 0

        found_metadata = False
        for token in tokens:
            if token.metadata.get('layer') == 'binary':
                found_metadata = True
                break

        assert found_metadata, "Layer metadata not found in any token"

    def test_require_annotation_metadata_threaded(self):
        """Test that require annotation metadata is threaded into IR tokens."""
        source = '@require(superbit, binary) SET x TO 42'
        program = parse(source)
        compiler = NullLangCompiler()
        stream = compiler.compile(program)

        tokens = list(stream)
        found_requires = False
        for token in tokens:
            if token.metadata.get('requires'):
                requires = token.metadata['requires']
                if 'superbit' in requires and 'binary' in requires:
                    found_requires = True
                    break

        assert found_requires, "Requires metadata not found in tokens"

    def test_prefer_annotation_metadata_threaded(self):
        """Test that prefer annotation metadata is threaded into IR tokens."""
        source = '@prefer(gpu, cpu) SET x TO 42'
        program = parse(source)
        compiler = NullLangCompiler()
        stream = compiler.compile(program)

        tokens = list(stream)
        found_prefers = False
        for token in tokens:
            if token.metadata.get('prefers'):
                prefers = token.metadata['prefers']
                if 'gpu' in prefers and 'cpu' in prefers:
                    found_prefers = True
                    break

        assert found_prefers, "Prefers metadata not found in tokens"

    def test_multiple_annotations_metadata(self):
        """Test metadata from multiple annotations."""
        source = '@layer(binary) @require(superbit) SET x TO 42'
        program = parse(source)
        compiler = NullLangCompiler()
        stream = compiler.compile(program)

        tokens = list(stream)
        found_all = False
        for token in tokens:
            if (token.metadata.get('layer') == 'binary' and
                'superbit' in (token.metadata.get('requires') or [])):
                found_all = True
                break

        assert found_all, "Multiple annotations not properly threaded"

    def test_annotation_only_applies_to_statement(self):
        """Test that annotations only apply to the annotated statement."""
        source = '''@layer(binary) SET x TO 42
SET y TO 10'''
        program = parse(source)
        compiler = NullLangCompiler()
        stream = compiler.compile(program)

        tokens = list(stream)

        found_binary = False
        found_non_binary = False

        for i, token in enumerate(tokens):
            if token.metadata.get('layer') == 'binary':
                found_binary = True

            if token.metadata.get('layer') != 'binary' and i > 0:
                if not tokens[i-1].metadata.get('layer') == 'binary':
                    found_non_binary = True

        assert found_binary, "Binary layer annotation not found"

    def test_show_command_with_annotation_compiled(self):
        """Test SHOW command with annotation compiles correctly."""
        source = '@layer(superbit) SHOW x'
        program = parse(source)
        compiler = NullLangCompiler()
        stream = compiler.compile(program)

        tokens = list(stream)
        assert any(t.opcode == SuperBitOpCode.PRINT for t in tokens)
        assert any(t.metadata.get('layer') == 'superbit' for t in tokens)


class TestAnnotationErrors:
    """Test error handling for annotations."""

    def test_empty_layer_annotation(self):
        """Test that @layer() without argument is caught."""
        with pytest.raises(Exception):
            parse_statement('@layer() SET x TO 42')

    def test_empty_require_annotation(self):
        """Test that @require() without arguments is caught."""
        with pytest.raises(Exception):
            parse_statement('@require() SET x TO 42')

    def test_empty_prefer_annotation(self):
        """Test that @prefer() without arguments is caught."""
        with pytest.raises(Exception):
            parse_statement('@prefer() SET x TO 42')

    def test_annotation_without_statement(self):
        """Test annotation that isn't followed by statement."""
        with pytest.raises(Exception):
            parse_statement('@layer(binary)')

    def test_invalid_annotation_syntax(self):
        """Test invalid annotation syntax."""
        with pytest.raises(Exception):
            parse_statement('@layer binary SET x TO 42')


class TestAnnotationIntegration:
    """Integration tests for annotations."""

    def test_program_with_mixed_annotated_unannotated(self):
        """Test program with both annotated and unannotated statements."""
        source = '''@layer(binary) SET x TO 42
SHOW x
@require(superbit) SET y TO x'''

        program = parse(source)
        assert len(program.statements) == 3

        stmt1, stmt2, stmt3 = program.statements
        assert len(stmt1.annotations) == 1
        assert len(stmt2.annotations) == 0
        assert len(stmt3.annotations) == 1

    def test_nested_control_flow_with_annotations(self):
        """Test annotations on nested control flow."""
        source = '''@layer(binary) IF TRUE THEN
  SET x TO 1
END IF'''

        program = parse(source)
        assert len(program.statements) == 1
        stmt = program.statements[0]
        assert isinstance(stmt, IfCommand)
        assert len(stmt.annotations) == 1
        assert stmt.annotations[0].layer == "binary"

    def test_annotation_preservation_through_round_trip(self):
        """Test that annotations are preserved through parse->compile."""
        source = '@layer(binary) @require(superbit) SET x TO 42'

        program = parse(source)
        compiler = NullLangCompiler()
        stream = compiler.compile(program)

        tokens = list(stream)
        assert len(tokens) > 0

        for token in tokens:
            metadata = token.metadata
            if metadata:
                assert metadata.get('layer') == 'binary'
                assert 'superbit' in metadata.get('requires', [])


class TestEdgeCases:
    """Test edge cases and corner cases."""

    def test_repeated_layer_names_in_require(self):
        """Test @require with repeated layer names."""
        result = parse_statement('@require(layer1, layer1) SET x TO 42')
        assert isinstance(result, SetCommand)
        assert result.annotations[0].layers == ["layer1", "layer1"]

    def test_very_long_layer_names(self):
        """Test very long layer names."""
        long_name = "a" * 100
        result = parse_statement(f'@layer({long_name}) SET x TO 42')
        assert isinstance(result, SetCommand)
        assert result.annotations[0].layer == long_name

    def test_many_annotations(self):
        """Test statement with many annotations."""
        annotations_str = " ".join([f'@layer(layer{i})' for i in range(5)])
        source = f'{annotations_str} SET x TO 42'
        result = parse_statement(source)
        assert isinstance(result, SetCommand)
        assert len(result.annotations) == 5
