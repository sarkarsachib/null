# Null-Lang Standard Library Reference

This document describes all standard library functions available in Null-Lang.

## Math Functions

### Arithmetic Operations

#### `math.ADD(a: number, b: number) -> number`
Returns the sum of two numbers.

#### `math.SUB(a: number, b: number) -> number`
Returns the difference of two numbers.

#### `math.MUL(a: number, b: number) -> number`
Returns the product of two numbers.

#### `math.DIV(a: number, b: number) -> number`
Returns the quotient of two numbers. Raises error on division by zero.

### Comparison Operations

#### `math.GT(a: number, b: number) -> boolean`
Returns true if a is greater than b.

#### `math.LT(a: number, b: number) -> boolean`
Returns true if a is less than b.

#### `math.GTE(a: number, b: number) -> boolean`
Returns true if a is greater than or equal to b.

#### `math.LTE(a: number, b: number) -> boolean`
Returns true if a is less than or equal to b.

#### `math.EQ(a: number, b: number) -> boolean`
Returns true if a is equal to b.

#### `math.NEQ(a: number, b: number) -> boolean`
Returns true if a is not equal to b.

### Math Functions

#### `math.ABS(x: number) -> number`
Returns the absolute value of x.

#### `math.MIN(a: number, b: number) -> number`
Returns the smaller of two numbers.

#### `math.MAX(a: number, b: number) -> number`
Returns the larger of two numbers.

#### `math.SQRT(x: number) -> number`
Returns the square root of x. Raises error for negative numbers.

#### `math.POW(base: number, exp: number) -> number`
Returns base raised to the power of exp.

#### `math.SIN(x: number) -> number`
Returns the sine of x (in radians).

#### `math.COS(x: number) -> number`
Returns the cosine of x (in radians).

#### `math.FLOOR(x: number) -> number`
Returns the largest integer less than or equal to x.

#### `math.CEIL(x: number) -> number`
Returns the smallest integer greater than or equal to x.

#### `math.ROUND(x: number) -> number`
Returns x rounded to the nearest integer.

## Text Functions

### String Operations

#### `text.CONCAT(a: string, b: string) -> string`
Concatenates two strings.

#### `text.UPPERCASE(text: string) -> string`
Returns the uppercase version of the string.

#### `text.LOWERCASE(text: string) -> string`
Returns the lowercase version of the string.

#### `text.TRIM(text: string) -> string`
Removes whitespace from both ends of the string.

#### `text.LENGTH(text: string) -> number`
Returns the length of the string.

### String Query Functions

#### `text.CONTAINS(text: string, substr: string) -> boolean`
Returns true if text contains substr.

#### `text.STARTS_WITH(text: string, prefix: string) -> boolean`
Returns true if text starts with prefix.

#### `text.ENDS_WITH(text: string, suffix: string) -> boolean`
Returns true if text ends with suffix.

### String Manipulation

#### `text.SUBSTR(text: string, start: number, length: number) -> string`
Returns a substring starting at start with given length.

#### `text.SLICE(text: string, start: number, length: number) -> string`
Alias for SUBSTR.

#### `text.GET_CHAR(text: string, index: number) -> string`
Returns the character at the given index, or empty string if out of bounds.

#### `text.REPLACE(text: string, old: string, new: string) -> string`
Replaces all occurrences of old with new.

#### `text.REPEAT(text: string, count: number) -> string`
Repeats the text count times.

### Array-String Conversion

#### `text.SPLIT(text: string, delimiter: string) -> array<string>`
Splits text by delimiter and returns an array of strings.

#### `text.JOIN(array: array<string>, delimiter: string) -> string`
Joins array elements with delimiter between them.

## Array Functions

### Basic Operations

#### `array.PUSH(array: array<T>, value: T) -> array<T>`
Appends value to the array and returns the modified array.

#### `array.POP(array: array<T>) -> T`
Removes and returns the last element. Raises error on empty array.

#### `array.LENGTH(array: array<T>) -> number`
Returns the number of elements in the array.

### Array Manipulation

#### `array.SORT(array: array<T>) -> array<T>`
Returns a new sorted array (numbers and strings supported).

#### `array.REVERSE(array: array<T>) -> array<T>`
Returns a new array with elements in reverse order.

#### `array.SLICE(array: array<T>, start: number, length: number) -> array<T>`
Returns a subarray starting at start with given length.

### Functional Operations

#### `array.MAP(array: array<T>, fn: function, bound_arg) -> array<U>`
Maps each element through the function. Function should have arity 2.

#### `array.FILTER(array: array<T>, fn: function, bound_arg) -> array<T>`
Filters elements using the function. Function should return boolean and have arity 2.

#### `array.REDUCE(array: array<T>, fn: function, initial: U) -> U`
Reduces array to single value using function. Function should have arity 2.

#### `array.FOR_EACH(array: array<T>, fn: function, bound_arg) -> null`
Calls function for each element. Function should have arity 2.

## I/O Functions

#### `io.SHOW(value: any) -> null`
Prints value to stdout.

#### `io.READ() -> string`
Reads a line from stdin and returns it (without trailing newline).

## Object Functions

#### `object.READ(obj: object, key: string) -> any`
Returns the value for key from the object.

#### `object.WRITE(obj: object, key: string, value: any) -> null`
Sets key to value in the object.

## Option Type Functions

### Creating Options

#### `option.SOME(value: T) -> Option<T>`
Creates a Some variant containing a value.

#### `option.NONE() -> Option<T>`
Creates a None variant.

### Querying Options

#### `option.IS_SOME(opt: Option<T>) -> boolean`
Returns true if opt is Some.

#### `option.IS_NONE(opt: Option<T>) -> boolean`
Returns true if opt is None.

#### `option.UNWRAP(opt: Option<T>) -> T`
Extracts the value from Some. Raises error if None.

## Result Type Functions

### Creating Results

#### `result.OK(value: T) -> Result<T, E>`
Creates an Ok variant.

#### `result.ERR(error: E) -> Result<T, E>`
Creates an Err variant.

### Querying Results

#### `result.IS_OK(result: Result<T, E>) -> boolean`
Returns true if result is Ok.

#### `result.IS_ERR(result: Result<T, E>) -> boolean`
Returns true if result is Err.

#### `result.UNWRAP(result: Result<T, E>) -> T`
Extracts the value from Ok. Raises error if Err.

#### `result.UNWRAP_ERR(result: Result<T, E>) -> E`
Extracts the error from Err. Raises error if Ok.

## Usage Examples

### Math Operations
```null
SET sum TO math.ADD(5, 3)
SET diff TO math.SUB(10, 4)
SET product TO math.MUL(6, 7)
SET quotient TO math.DIV(20, 4)
SET absolute TO math.ABS(-15)
SET squared TO math.POW(3, 2)
SET rounded TO math.ROUND(3.7)
```

### String Manipulation
```null
SET text TO "Hello, World!"
SET upper TO text.UPPERCASE(text)
SET lower TO text.LOWERCASE(text)
SET trimmed TO text.TRIM("  spaces  ")
SET length TO text.LENGTH(text)
SET has_hello TO text.CONTAINS(text, "Hello")
SET parts TO text.SPLIT("a,b,c", ",")
SET joined TO text.JOIN(parts, "-")
```

### Array Operations
```null
SET arr TO ARRAY [3, 1, 4, 1, 5]
SET length TO array.LENGTH(arr)
SET sorted TO array.SORT(arr)
SET reversed TO array.REVERSE(arr)
SET sliced TO array.SLICE(arr, 1, 3)
```

### Functional Array Operations
```null
SET doubled TO array.MAP(arr, math.MUL, 2)
SET filtered TO array.FILTER(arr, math.GT, 2)
SET sum TO array.REDUCE(arr, math.ADD, 0)
```

### I/O Operations
```null
io.SHOW("Enter your name:")
SET name TO io.READ()
io.SHOW("Hello, " + name)
```

## Future Enhancements

- [ ] Collections module (dictionaries/maps)
- [ ] Date/time functions
- [ ] Regular expressions
- [ ] Base64 encoding/decoding
- [ ] Hash functions
- [ ] JSON serialization/deserialization
