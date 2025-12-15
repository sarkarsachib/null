import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from null_system.types import (
    NullNumber, NullString, NullArray, NullObject,
    NullOption, NullResult, none_val, some_val, ok_val, err_val
)
from null_system.lib.registry import default_registry
from null_system.runtime import NullCallContext, NullIO
from null_system.errors import NullTypeError


class BufferIO(NullIO):
    def __init__(self, inputs=None):
        self._inputs = list(inputs or [])
        self.outputs = []

    def read_line(self) -> str:
        if not self._inputs:
            return ""
        return self._inputs.pop(0)

    def write(self, text: str) -> None:
        self.outputs.append(text)


class PatternMatchingTests(unittest.TestCase):

    def test_option_some_creation(self):
        value = some_val(NullNumber(42.0))
        self.assertEqual(value.tag, "Some")
        self.assertEqual(value.value.as_number(), 42.0)
        self.assertTrue(value.is_some())
        self.assertFalse(value.is_none())

    def test_option_none_creation(self):
        value = none_val()
        self.assertEqual(value.tag, "None")
        self.assertFalse(value.is_some())
        self.assertTrue(value.is_none())

    def test_option_some_unwrap(self):
        value = some_val(NullNumber(42.0))
        result = value.unwrap()
        self.assertEqual(result.as_number(), 42.0)

    def test_option_none_unwrap_raises(self):
        value = none_val()
        with self.assertRaises(NullTypeError):
            value.unwrap()

    def test_result_ok_creation(self):
        value = ok_val(NullNumber(42.0))
        self.assertEqual(value.tag, "Ok")
        self.assertEqual(value.value.as_number(), 42.0)
        self.assertTrue(value.is_ok())
        self.assertFalse(value.is_err())

    def test_result_err_creation(self):
        value = err_val(NullString("error"))
        self.assertEqual(value.tag, "Err")
        self.assertEqual(value.value.as_string(), "error")
        self.assertFalse(value.is_ok())
        self.assertTrue(value.is_err())

    def test_result_ok_unwrap(self):
        value = ok_val(NullNumber(42.0))
        result = value.unwrap()
        self.assertEqual(result.as_number(), 42.0)

    def test_result_ok_unwrap_err_raises(self):
        value = ok_val(NullNumber(42.0))
        with self.assertRaises(NullTypeError):
            value.unwrap_err()

    def test_result_err_unwrap_raises(self):
        value = err_val(NullString("error"))
        with self.assertRaises(NullTypeError):
            value.unwrap()

    def test_result_err_unwrap_err(self):
        value = err_val(NullString("error"))
        result = value.unwrap_err()
        self.assertEqual(result.as_string(), "error")

    def test_option_some_lib_function(self):
        registry = default_registry()
        fn = registry.resolve("option.SOME")
        ctx = NullCallContext(registry=registry, io=BufferIO())
        result = fn.impl(ctx, [NullNumber(42.0)])
        self.assertTrue(isinstance(result, NullOption))
        self.assertEqual(result.tag, "Some")
        self.assertEqual(result.value.as_number(), 42.0)

    def test_option_none_lib_function(self):
        registry = default_registry()
        fn = registry.resolve("option.NONE")
        ctx = NullCallContext(registry=registry, io=BufferIO())
        result = fn.impl(ctx, [])
        self.assertTrue(isinstance(result, NullOption))
        self.assertEqual(result.tag, "None")

    def test_option_is_some_lib_function(self):
        registry = default_registry()
        fn = registry.resolve("option.IS_SOME")
        ctx = NullCallContext(registry=registry, io=BufferIO())
        
        some_val_inst = some_val(NullNumber(42.0))
        result = fn.impl(ctx, [some_val_inst])
        self.assertEqual(result.as_number(), 1.0)
        
        none_val_inst = none_val()
        result = fn.impl(ctx, [none_val_inst])
        self.assertEqual(result.as_number(), 0.0)

    def test_option_is_none_lib_function(self):
        registry = default_registry()
        fn = registry.resolve("option.IS_NONE")
        ctx = NullCallContext(registry=registry, io=BufferIO())
        
        none_val_inst = none_val()
        result = fn.impl(ctx, [none_val_inst])
        self.assertEqual(result.as_number(), 1.0)
        
        some_val_inst = some_val(NullNumber(42.0))
        result = fn.impl(ctx, [some_val_inst])
        self.assertEqual(result.as_number(), 0.0)

    def test_result_ok_lib_function(self):
        registry = default_registry()
        fn = registry.resolve("result.OK")
        ctx = NullCallContext(registry=registry, io=BufferIO())
        result = fn.impl(ctx, [NullNumber(42.0)])
        self.assertTrue(isinstance(result, NullResult))
        self.assertEqual(result.tag, "Ok")
        self.assertEqual(result.value.as_number(), 42.0)

    def test_result_err_lib_function(self):
        registry = default_registry()
        fn = registry.resolve("result.ERR")
        ctx = NullCallContext(registry=registry, io=BufferIO())
        result = fn.impl(ctx, [NullString("error")])
        self.assertTrue(isinstance(result, NullResult))
        self.assertEqual(result.tag, "Err")
        self.assertEqual(result.value.as_string(), "error")

    def test_result_is_ok_lib_function(self):
        registry = default_registry()
        fn = registry.resolve("result.IS_OK")
        ctx = NullCallContext(registry=registry, io=BufferIO())
        
        ok_val_inst = ok_val(NullNumber(42.0))
        result = fn.impl(ctx, [ok_val_inst])
        self.assertEqual(result.as_number(), 1.0)
        
        err_val_inst = err_val(NullString("error"))
        result = fn.impl(ctx, [err_val_inst])
        self.assertEqual(result.as_number(), 0.0)

    def test_result_is_err_lib_function(self):
        registry = default_registry()
        fn = registry.resolve("result.IS_ERR")
        ctx = NullCallContext(registry=registry, io=BufferIO())
        
        err_val_inst = err_val(NullString("error"))
        result = fn.impl(ctx, [err_val_inst])
        self.assertEqual(result.as_number(), 1.0)
        
        ok_val_inst = ok_val(NullNumber(42.0))
        result = fn.impl(ctx, [ok_val_inst])
        self.assertEqual(result.as_number(), 0.0)

    def test_result_unwrap_lib_function(self):
        registry = default_registry()
        fn = registry.resolve("result.UNWRAP")
        ctx = NullCallContext(registry=registry, io=BufferIO())
        
        ok_val_inst = ok_val(NullNumber(42.0))
        result = fn.impl(ctx, [ok_val_inst])
        self.assertEqual(result.as_number(), 42.0)

    def test_result_unwrap_err_lib_function(self):
        registry = default_registry()
        fn = registry.resolve("result.UNWRAP_ERR")
        ctx = NullCallContext(registry=registry, io=BufferIO())
        
        err_val_inst = err_val(NullString("error"))
        result = fn.impl(ctx, [err_val_inst])
        self.assertEqual(result.as_string(), "error")

    def test_union_display(self):
        some_val_inst = some_val(NullNumber(42.0))
        self.assertEqual(str(some_val_inst), "Some(42)")
        
        none_val_inst = none_val()
        self.assertEqual(str(none_val_inst), "None")
        
        ok_val_inst = ok_val(NullNumber(42.0))
        self.assertEqual(str(ok_val_inst), "Ok(42)")
        
        err_val_inst = err_val(NullString("error"))
        self.assertEqual(str(err_val_inst), "Err(error)")


if __name__ == "__main__":
    unittest.main()
