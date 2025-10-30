---
title: ES|QL string functions
description: ES|QL supports these string functions: 
url: https://www.elastic.co/docs/reference/query-languages/esql/functions-operators/string-functions
---

# ES|QL string functions

ES|QL supports these string functions:
- [`BIT_LENGTH`](#esql-bit_length)
- [`BYTE_LENGTH`](#esql-byte_length)
- [`CONCAT`](#esql-concat)
- [`CONTAINS`](#esql-contains)
- [`ENDS_WITH`](#esql-ends_with)
- [`FROM_BASE64`](#esql-from_base64)
- [`HASH`](#esql-hash)
- [`LEFT`](#esql-left)
- [`LENGTH`](#esql-length)
- [`LOCATE`](#esql-locate)
- [`LTRIM`](#esql-ltrim)
- [`MD5`](#esql-md5)
- [`REPEAT`](#esql-repeat)
- [`REPLACE`](#esql-replace)
- [`REVERSE`](#esql-reverse)
- [`RIGHT`](#esql-right)
- [`RTRIM`](#esql-rtrim)
- [`SHA1`](#esql-sha1)
- [`SHA256`](#esql-sha256)
- [`SPACE`](#esql-space)
- [`SPLIT`](#esql-split)
- [`STARTS_WITH`](#esql-starts_with)
- [`SUBSTRING`](#esql-substring)
- [`TO_BASE64`](#esql-to_base64)
- [`TO_LOWER`](#esql-to_lower)
- [`TO_UPPER`](#esql-to_upper)
- [`TRIM`](#esql-trim)
- [`URL_ENCODE`](#esql-url_encode)
- [`URL_ENCODE_COMPONENT`](#esql-url_encode_component)
- [`URL_DECODE`](#esql-url_decode)


## `BIT_LENGTH`

**Syntax**
![Embedded](https://www.elastic.co/docs/reference/query-languages/esql/images/functions/bit_length.svg)

**Parameters**
<definitions>
  <definition term="string">
    String expression. If `null`, the function returns `null`.
  </definition>
</definitions>

**Description**
Returns the bit length of a string.
<note>
  All strings are in UTF-8, so a single character can use multiple bytes.
</note>

**Supported types**

| string  | result  |
|---------|---------|
| keyword | integer |
| text    | integer |

**Example**
```esql
FROM airports
| WHERE country == "India"
| KEEP city
| EVAL fn_length = LENGTH(city), fn_bit_length = BIT_LENGTH(city)
```


| city:keyword | fn_length:integer | fn_bit_length:integer |
|--------------|-------------------|-----------------------|
| Agwār        | 5                 | 48                    |
| Ahmedabad    | 9                 | 72                    |
| Bangalore    | 9                 | 72                    |


## `BYTE_LENGTH`

**Syntax**
![Embedded](https://www.elastic.co/docs/reference/query-languages/esql/images/functions/byte_length.svg)

**Parameters**
<definitions>
  <definition term="string">
    String expression. If `null`, the function returns `null`.
  </definition>
</definitions>

**Description**
Returns the byte length of a string.
<note>
  All strings are in UTF-8, so a single character can use multiple bytes.
</note>

**Supported types**

| string  | result  |
|---------|---------|
| keyword | integer |
| text    | integer |

**Example**
```esql
FROM airports
| WHERE country == "India"
| KEEP city
| EVAL fn_length = LENGTH(city), fn_byte_length = BYTE_LENGTH(city)
```


| city:keyword | fn_length:integer | fn_byte_length:integer |
|--------------|-------------------|------------------------|
| Agwār        | 5                 | 6                      |
| Ahmedabad    | 9                 | 9                      |
| Bangalore    | 9                 | 9                      |


## `CONCAT`

**Syntax**
![Embedded](https://www.elastic.co/docs/reference/query-languages/esql/images/functions/concat.svg)

**Parameters**
<definitions>
  <definition term="string1">
    Strings to concatenate.
  </definition>
  <definition term="string2">
    Strings to concatenate.
  </definition>
</definitions>

**Description**
Concatenates two or more strings.
**Supported types**

| string1 | string2 | result  |
|---------|---------|---------|
| keyword | keyword | keyword |
| keyword | text    | keyword |
| text    | keyword | keyword |
| text    | text    | keyword |

**Example**
```esql
FROM employees
| KEEP first_name, last_name
| EVAL fullname = CONCAT(first_name, " ", last_name)
```


| first_name:keyword | last_name:keyword | fullname:keyword   |
|--------------------|-------------------|--------------------|
| Alejandro          | McAlpine          | Alejandro McAlpine |
| Amabile            | Gomatam           | Amabile Gomatam    |
| Anneke             | Preusig           | Anneke Preusig     |


## `CONTAINS`

```
stack: ga 9.2.0
```

**Syntax**
![Embedded](https://www.elastic.co/docs/reference/query-languages/esql/images/functions/contains.svg)

**Parameters**
<definitions>
  <definition term="string">
    String expression: input string to check against. If `null`, the function returns `null`.
  </definition>
  <definition term="substring">
    String expression: A substring to find in the input string. If `null`, the function returns `null`.
  </definition>
</definitions>

**Description**
Returns a boolean that indicates whether a keyword substring is within another string. Returns `null` if either parameter is null.
**Supported types**

| string  | substring | result  |
|---------|-----------|---------|
| keyword | keyword   | boolean |
| keyword | text      | boolean |
| text    | keyword   | boolean |
| text    | text      | boolean |

**Example**
```esql
ROW a = "hello"
| EVAL has_ll = CONTAINS(a, "ll")
```


| a:keyword | has_ll:boolean |
|-----------|----------------|
| hello     | true           |


## `ENDS_WITH`

**Syntax**
![Embedded](https://www.elastic.co/docs/reference/query-languages/esql/images/functions/ends_with.svg)

**Parameters**
<definitions>
  <definition term="str">
    String expression. If `null`, the function returns `null`.
  </definition>
  <definition term="suffix">
    String expression. If `null`, the function returns `null`.
  </definition>
</definitions>

**Description**
Returns a boolean that indicates whether a keyword string ends with another string.
**Supported types**

| str     | suffix  | result  |
|---------|---------|---------|
| keyword | keyword | boolean |
| keyword | text    | boolean |
| text    | keyword | boolean |
| text    | text    | boolean |

**Example**
```esql
FROM employees
| KEEP last_name
| EVAL ln_E = ENDS_WITH(last_name, "d")
```


| last_name:keyword | ln_E:boolean |
|-------------------|--------------|
| Awdeh             | false        |
| Azuma             | false        |
| Baek              | false        |
| Bamford           | true         |
| Bernatsky         | false        |


## `FROM_BASE64`

**Syntax**
![Embedded](https://www.elastic.co/docs/reference/query-languages/esql/images/functions/from_base64.svg)

**Parameters**
<definitions>
  <definition term="string">
    A base64 string.
  </definition>
</definitions>

**Description**
Decode a base64 string.
**Supported types**

| string  | result  |
|---------|---------|
| keyword | keyword |
| text    | keyword |

**Example**
```esql
ROW a = "ZWxhc3RpYw=="
| EVAL d = FROM_BASE64(a)
```


| a:keyword    | d:keyword |
|--------------|-----------|
| ZWxhc3RpYw== | elastic   |


## `HASH`

**Syntax**
![Embedded](https://www.elastic.co/docs/reference/query-languages/esql/images/functions/hash.svg)

**Parameters**
<definitions>
  <definition term="algorithm">
    Hash algorithm to use.
  </definition>
  <definition term="input">
    Input to hash.
  </definition>
</definitions>

**Description**
Computes the hash of the input using various algorithms such as MD5, SHA, SHA-224, SHA-256, SHA-384, SHA-512.
**Supported types**

| algorithm | input   | result  |
|-----------|---------|---------|
| keyword   | keyword | keyword |
| keyword   | text    | keyword |
| text      | keyword | keyword |
| text      | text    | keyword |

**Example**
```esql
FROM sample_data
| WHERE message != "Connection error"
| EVAL md5 = hash("md5", message), sha256 = hash("sha256", message)
| KEEP message, md5, sha256
```


| message:keyword       | md5:keyword                      | sha256:keyword                                                   |
|-----------------------|----------------------------------|------------------------------------------------------------------|
| Connected to 10.1.0.1 | abd7d1ce2bb636842a29246b3512dcae | 6d8372129ad78770f7185554dd39864749a62690216460752d6c075fa38ad85c |
| Connected to 10.1.0.2 | 8f8f1cb60832d153f5b9ec6dc828b93f | b0db24720f15857091b3c99f4c4833586d0ea3229911b8777efb8d917cf27e9a |
| Connected to 10.1.0.3 | 912b6dc13503165a15de43304bb77c78 | 75b0480188db8acc4d5cc666a51227eb2bc5b989cd8ca912609f33e0846eff57 |
| Disconnected          | ef70e46fd3bbc21e3e1f0b6815e750c0 | 04dfac3671b494ad53fcd152f7a14511bfb35747278aad8ce254a0d6e4ba4718 |


## `LEFT`

**Syntax**
![Embedded](https://www.elastic.co/docs/reference/query-languages/esql/images/functions/left.svg)

**Parameters**
<definitions>
  <definition term="string">
    The string from which to return a substring.
  </definition>
  <definition term="length">
    The number of characters to return.
  </definition>
</definitions>

**Description**
Returns the substring that extracts *length* chars from *string* starting from the left.
**Supported types**

| string  | length  | result  |
|---------|---------|---------|
| keyword | integer | keyword |
| text    | integer | keyword |

**Example**
```esql
FROM employees
| KEEP last_name
| EVAL left = LEFT(last_name, 3)
```


| last_name:keyword | left:keyword |
|-------------------|--------------|
| Awdeh             | Awd          |
| Azuma             | Azu          |
| Baek              | Bae          |
| Bamford           | Bam          |
| Bernatsky         | Ber          |


## `LENGTH`

**Syntax**
![Embedded](https://www.elastic.co/docs/reference/query-languages/esql/images/functions/length.svg)

**Parameters**
<definitions>
  <definition term="string">
    String expression. If `null`, the function returns `null`.
  </definition>
</definitions>

**Description**
Returns the character length of a string.
<note>
  All strings are in UTF-8, so a single character can use multiple bytes.
</note>

**Supported types**

| string  | result  |
|---------|---------|
| keyword | integer |
| text    | integer |

**Example**
```esql
FROM airports
| WHERE country == "India"
| KEEP city
| EVAL fn_length = LENGTH(city)
```


| city:keyword | fn_length:integer |
|--------------|-------------------|
| Agwār        | 5                 |
| Ahmedabad    | 9                 |
| Bangalore    | 9                 |


## `LOCATE`

**Syntax**
![Embedded](https://www.elastic.co/docs/reference/query-languages/esql/images/functions/locate.svg)

**Parameters**
<definitions>
  <definition term="string">
    An input string
  </definition>
  <definition term="substring">
    A substring to locate in the input string
  </definition>
  <definition term="start">
    The start index
  </definition>
</definitions>

**Description**
Returns an integer that indicates the position of a keyword substring within another string. Returns `0` if the substring cannot be found. Note that string positions start from `1`.
**Supported types**

| string  | substring | start   | result  |
|---------|-----------|---------|---------|
| keyword | keyword   | integer | integer |
| keyword | keyword   |         | integer |
| keyword | text      | integer | integer |
| keyword | text      |         | integer |
| text    | keyword   | integer | integer |
| text    | keyword   |         | integer |
| text    | text      | integer | integer |
| text    | text      |         | integer |

**Example**
```esql
ROW a = "hello"
| EVAL a_ll = LOCATE(a, "ll")
```


| a:keyword | a_ll:integer |
|-----------|--------------|
| hello     | 3            |


## `LTRIM`

**Syntax**
![Embedded](https://www.elastic.co/docs/reference/query-languages/esql/images/functions/ltrim.svg)

**Parameters**
<definitions>
  <definition term="string">
    String expression. If `null`, the function returns `null`.
  </definition>
</definitions>

**Description**
Removes leading whitespaces from a string.
**Supported types**

| string  | result  |
|---------|---------|
| keyword | keyword |
| text    | keyword |

**Example**
```esql
ROW message = "   some text  ",  color = " red "
| EVAL message = LTRIM(message)
| EVAL color = LTRIM(color)
| EVAL message = CONCAT("'", message, "'")
| EVAL color = CONCAT("'", color, "'")
```


| message:keyword | color:keyword |
|-----------------|---------------|
| 'some text  '   | 'red '        |


## `MD5`

**Syntax**
![Embedded](https://www.elastic.co/docs/reference/query-languages/esql/images/functions/md5.svg)

**Parameters**
<definitions>
  <definition term="input">
    Input to hash.
  </definition>
</definitions>

**Description**
Computes the MD5 hash of the input (if the MD5 hash is available on the JVM).
**Supported types**

| input   | result  |
|---------|---------|
| keyword | keyword |
| text    | keyword |

**Example**
```esql
FROM sample_data
| WHERE message != "Connection error"
| EVAL md5 = md5(message)
| KEEP message, md5
```


| message:keyword       | md5:keyword                      |
|-----------------------|----------------------------------|
| Connected to 10.1.0.1 | abd7d1ce2bb636842a29246b3512dcae |
| Connected to 10.1.0.2 | 8f8f1cb60832d153f5b9ec6dc828b93f |
| Connected to 10.1.0.3 | 912b6dc13503165a15de43304bb77c78 |
| Disconnected          | ef70e46fd3bbc21e3e1f0b6815e750c0 |


## `REPEAT`

**Syntax**
![Embedded](https://www.elastic.co/docs/reference/query-languages/esql/images/functions/repeat.svg)

**Parameters**
<definitions>
  <definition term="string">
    String expression.
  </definition>
  <definition term="number">
    Number times to repeat.
  </definition>
</definitions>

**Description**
Returns a string constructed by concatenating `string` with itself the specified `number` of times.
**Supported types**

| string  | number  | result  |
|---------|---------|---------|
| keyword | integer | keyword |
| text    | integer | keyword |

**Example**
```esql
ROW a = "Hello!"
| EVAL triple_a = REPEAT(a, 3)
```


| a:keyword | triple_a:keyword   |
|-----------|--------------------|
| Hello!    | Hello!Hello!Hello! |


## `REPLACE`

**Syntax**
![Embedded](https://www.elastic.co/docs/reference/query-languages/esql/images/functions/replace.svg)

**Parameters**
<definitions>
  <definition term="string">
    String expression.
  </definition>
  <definition term="regex">
    Regular expression.
  </definition>
  <definition term="newString">
    Replacement string.
  </definition>
</definitions>

**Description**
The function substitutes in the string `str` any match of the regular expression `regex` with the replacement string `newStr`.
**Supported types**

| string  | regex   | newString | result  |
|---------|---------|-----------|---------|
| keyword | keyword | keyword   | keyword |
| keyword | keyword | text      | keyword |
| keyword | text    | keyword   | keyword |
| keyword | text    | text      | keyword |
| text    | keyword | keyword   | keyword |
| text    | keyword | text      | keyword |
| text    | text    | keyword   | keyword |
| text    | text    | text      | keyword |

**Examples**
This example replaces any occurrence of the word "World" with the word "Universe":
```esql
ROW str = "Hello World"
| EVAL str = REPLACE(str, "World", "Universe")
```


| str:keyword    |
|----------------|
| Hello Universe |

This example removes all spaces:
```esql
ROW str = "Hello World"
| EVAL str = REPLACE(str, "\\\\s+", "")
```


| str:keyword |
|-------------|
| HelloWorld  |


## `REVERSE`

**Syntax**
![Embedded](https://www.elastic.co/docs/reference/query-languages/esql/images/functions/reverse.svg)

**Parameters**
<definitions>
  <definition term="str">
    String expression. If `null`, the function returns `null`.
  </definition>
</definitions>

**Description**
Returns a new string representing the input string in reverse order.
**Supported types**

| str     | result  |
|---------|---------|
| keyword | keyword |
| text    | keyword |

**Examples**
```esql
ROW message = "Some Text" | EVAL message_reversed = REVERSE(message);
```


| message:keyword | message_reversed:keyword |
|-----------------|--------------------------|
| Some Text       | txeT emoS                |

`REVERSE` works with unicode, too! It keeps unicode grapheme clusters together during reversal.
```esql
ROW bending_arts = "💧🪨🔥💨" | EVAL bending_arts_reversed = REVERSE(bending_arts);
```


| bending_arts:keyword | bending_arts_reversed:keyword |
|----------------------|-------------------------------|
| 💧🪨🔥💨             | 💨🔥🪨💧                      |


## `RIGHT`

**Syntax**
![Embedded](https://www.elastic.co/docs/reference/query-languages/esql/images/functions/right.svg)

**Parameters**
<definitions>
  <definition term="string">
    The string from which to returns a substring.
  </definition>
  <definition term="length">
    The number of characters to return.
  </definition>
</definitions>

**Description**
Return the substring that extracts *length* chars from *str* starting from the right.
**Supported types**

| string  | length  | result  |
|---------|---------|---------|
| keyword | integer | keyword |
| text    | integer | keyword |

**Example**
```esql
FROM employees
| KEEP last_name
| EVAL right = RIGHT(last_name, 3)
```


| last_name:keyword | right:keyword |
|-------------------|---------------|
| Awdeh             | deh           |
| Azuma             | uma           |
| Baek              | aek           |
| Bamford           | ord           |
| Bernatsky         | sky           |


## `RTRIM`

**Syntax**
![Embedded](https://www.elastic.co/docs/reference/query-languages/esql/images/functions/rtrim.svg)

**Parameters**
<definitions>
  <definition term="string">
    String expression. If `null`, the function returns `null`.
  </definition>
</definitions>

**Description**
Removes trailing whitespaces from a string.
**Supported types**

| string  | result  |
|---------|---------|
| keyword | keyword |
| text    | keyword |

**Example**
```esql
ROW message = "   some text  ",  color = " red "
| EVAL message = RTRIM(message)
| EVAL color = RTRIM(color)
| EVAL message = CONCAT("'", message, "'")
| EVAL color = CONCAT("'", color, "'")
```


| message:keyword | color:keyword |
|-----------------|---------------|
| '   some text'  | ' red'        |


## `SHA1`

**Syntax**
![Embedded](https://www.elastic.co/docs/reference/query-languages/esql/images/functions/sha1.svg)

**Parameters**
<definitions>
  <definition term="input">
    Input to hash.
  </definition>
</definitions>

**Description**
Computes the SHA1 hash of the input.
**Supported types**

| input   | result  |
|---------|---------|
| keyword | keyword |
| text    | keyword |

**Example**
```esql
FROM sample_data
| WHERE message != "Connection error"
| EVAL sha1 = sha1(message)
| KEEP message, sha1
```


| message:keyword       | sha1:keyword                             |
|-----------------------|------------------------------------------|
| Connected to 10.1.0.1 | 42b85531a79088036a17759db7d2de292b92f57f |
| Connected to 10.1.0.2 | d30db445da2e9237c9718d0c7e4fb7cbbe9c2cb4 |
| Connected to 10.1.0.3 | 2733848d943809f0b10cad3e980763e88afb9853 |
| Disconnected          | 771e05f27b99fd59f638f41a7a4e977b1d4691fe |


## `SHA256`

**Syntax**
![Embedded](https://www.elastic.co/docs/reference/query-languages/esql/images/functions/sha256.svg)

**Parameters**
<definitions>
  <definition term="input">
    Input to hash.
  </definition>
</definitions>

**Description**
Computes the SHA256 hash of the input.
**Supported types**

| input   | result  |
|---------|---------|
| keyword | keyword |
| text    | keyword |

**Example**
```esql
FROM sample_data
| WHERE message != "Connection error"
| EVAL sha256 = sha256(message)
| KEEP message, sha256
```


| message:keyword       | sha256:keyword                                                   |
|-----------------------|------------------------------------------------------------------|
| Connected to 10.1.0.1 | 6d8372129ad78770f7185554dd39864749a62690216460752d6c075fa38ad85c |
| Connected to 10.1.0.2 | b0db24720f15857091b3c99f4c4833586d0ea3229911b8777efb8d917cf27e9a |
| Connected to 10.1.0.3 | 75b0480188db8acc4d5cc666a51227eb2bc5b989cd8ca912609f33e0846eff57 |
| Disconnected          | 04dfac3671b494ad53fcd152f7a14511bfb35747278aad8ce254a0d6e4ba4718 |


## `SPACE`

**Syntax**
![Embedded](https://www.elastic.co/docs/reference/query-languages/esql/images/functions/space.svg)

**Parameters**
<definitions>
  <definition term="number">
    Number of spaces in result.
  </definition>
</definitions>

**Description**
Returns a string made of `number` spaces.
**Supported types**

| number  | result  |
|---------|---------|
| integer | keyword |

**Example**
```esql
ROW message = CONCAT("Hello", SPACE(1), "World!");
```


| message:keyword |
|-----------------|
| Hello World!    |


## `SPLIT`

**Syntax**
![Embedded](https://www.elastic.co/docs/reference/query-languages/esql/images/functions/split.svg)

**Parameters**
<definitions>
  <definition term="string">
    String expression. If `null`, the function returns `null`.
  </definition>
  <definition term="delim">
    Delimiter. Only single byte delimiters are currently supported.
  </definition>
</definitions>

**Description**
Split a single valued string into multiple strings.
**Supported types**

| string  | delim   | result  |
|---------|---------|---------|
| keyword | keyword | keyword |
| keyword | text    | keyword |
| text    | keyword | keyword |
| text    | text    | keyword |

**Example**
```esql
ROW words="foo;bar;baz;qux;quux;corge"
| EVAL word = SPLIT(words, ";")
```


| words:keyword              | word:keyword                 |
|----------------------------|------------------------------|
| foo;bar;baz;qux;quux;corge | [foo,bar,baz,qux,quux,corge] |


## `STARTS_WITH`

**Syntax**
![Embedded](https://www.elastic.co/docs/reference/query-languages/esql/images/functions/starts_with.svg)

**Parameters**
<definitions>
  <definition term="str">
    String expression. If `null`, the function returns `null`.
  </definition>
  <definition term="prefix">
    String expression. If `null`, the function returns `null`.
  </definition>
</definitions>

**Description**
Returns a boolean that indicates whether a keyword string starts with another string.
**Supported types**

| str     | prefix  | result  |
|---------|---------|---------|
| keyword | keyword | boolean |
| keyword | text    | boolean |
| text    | keyword | boolean |
| text    | text    | boolean |

**Example**
```esql
FROM employees
| KEEP last_name
| EVAL ln_S = STARTS_WITH(last_name, "B")
```


| last_name:keyword | ln_S:boolean |
|-------------------|--------------|
| Awdeh             | false        |
| Azuma             | false        |
| Baek              | true         |
| Bamford           | true         |
| Bernatsky         | true         |


## `SUBSTRING`

**Syntax**
![Embedded](https://www.elastic.co/docs/reference/query-languages/esql/images/functions/substring.svg)

**Parameters**
<definitions>
  <definition term="string">
    String expression. If `null`, the function returns `null`.
  </definition>
  <definition term="start">
    Start position.
  </definition>
  <definition term="length">
    Length of the substring from the start position. Optional; if omitted, all positions after `start` are returned.
  </definition>
</definitions>

**Description**
Returns a substring of a string, specified by a start position and an optional length.
**Supported types**

| string  | start   | length  | result  |
|---------|---------|---------|---------|
| keyword | integer | integer | keyword |
| text    | integer | integer | keyword |

**Examples**
This example returns the first three characters of every last name:
```esql
FROM employees
| KEEP last_name
| EVAL ln_sub = SUBSTRING(last_name, 1, 3)
```


| last_name:keyword | ln_sub:keyword |
|-------------------|----------------|
| Awdeh             | Awd            |
| Azuma             | Azu            |
| Baek              | Bae            |
| Bamford           | Bam            |
| Bernatsky         | Ber            |

A negative start position is interpreted as being relative to the end of the string.
This example returns the last three characters of every last name:
```esql
FROM employees
| KEEP last_name
| EVAL ln_sub = SUBSTRING(last_name, -3, 3)
```


| last_name:keyword | ln_sub:keyword |
|-------------------|----------------|
| Awdeh             | deh            |
| Azuma             | uma            |
| Baek              | aek            |
| Bamford           | ord            |
| Bernatsky         | sky            |

If length is omitted, substring returns the remainder of the string.
This example returns all characters except for the first:
```esql
FROM employees
| KEEP last_name
| EVAL ln_sub = SUBSTRING(last_name, 2)
```


| last_name:keyword | ln_sub:keyword |
|-------------------|----------------|
| Awdeh             | wdeh           |
| Azuma             | zuma           |
| Baek              | aek            |
| Bamford           | amford         |
| Bernatsky         | ernatsky       |


## `TO_BASE64`

**Syntax**
![Embedded](https://www.elastic.co/docs/reference/query-languages/esql/images/functions/to_base64.svg)

**Parameters**
<definitions>
  <definition term="string">
    A string.
  </definition>
</definitions>

**Description**
Encode a string to a base64 string.
**Supported types**

| string  | result  |
|---------|---------|
| keyword | keyword |
| text    | keyword |

**Example**
```esql
ROW a = "elastic"
| EVAL e = TO_BASE64(a)
```


| a:keyword | e:keyword    |
|-----------|--------------|
| elastic   | ZWxhc3RpYw== |


## `TO_LOWER`

**Syntax**
![Embedded](https://www.elastic.co/docs/reference/query-languages/esql/images/functions/to_lower.svg)

**Parameters**
<definitions>
  <definition term="str">
    String expression. If `null`, the function returns `null`. The input can be a single-valued column or expression, or a multi-valued column or expression `stack: ga 9.1.0`.
  </definition>
</definitions>

**Description**
Returns a new string representing the input string converted to lower case.
**Supported types**

| str     | result  |
|---------|---------|
| keyword | keyword |
| text    | keyword |

**Examples**
```esql
ROW message = "Some Text"
| EVAL message_lower = TO_LOWER(message)
```


| message:keyword | message_lower:keyword |
|-----------------|-----------------------|
| Some Text       | some text             |

```
stack: ga 9.1.0
```

```esql
ROW v = TO_LOWER(["Some", "Text"])
```


| v:keyword        |
|------------------|
| ["some", "text"] |


## `TO_UPPER`

**Syntax**
![Embedded](https://www.elastic.co/docs/reference/query-languages/esql/images/functions/to_upper.svg)

**Parameters**
<definitions>
  <definition term="str">
    String expression. If `null`, the function returns `null`. The input can be a single-valued column or expression, or a multi-valued column or expression `stack: ga 9.1.0`.
  </definition>
</definitions>

**Description**
Returns a new string representing the input string converted to upper case.
**Supported types**

| str     | result  |
|---------|---------|
| keyword | keyword |
| text    | keyword |

**Example**
```esql
ROW message = "Some Text"
| EVAL message_upper = TO_UPPER(message)
```


| message:keyword | message_upper:keyword |
|-----------------|-----------------------|
| Some Text       | SOME TEXT             |


## `TRIM`

**Syntax**
![Embedded](https://www.elastic.co/docs/reference/query-languages/esql/images/functions/trim.svg)

**Parameters**
<definitions>
  <definition term="string">
    String expression. If `null`, the function returns `null`.
  </definition>
</definitions>

**Description**
Removes leading and trailing whitespaces from a string.
**Supported types**

| string  | result  |
|---------|---------|
| keyword | keyword |
| text    | keyword |

**Example**
```esql
ROW message = "   some text  ",  color = " red "
| EVAL message = TRIM(message)
| EVAL color = TRIM(color)
```


| message:s | color:s |
|-----------|---------|
| some text | red     |


## `URL_ENCODE`

```
stack: ga 9.2.0
```

**Syntax**
![Embedded](https://www.elastic.co/docs/reference/query-languages/esql/images/functions/url_encode.svg)

**Parameters**
<definitions>
  <definition term="string">
    The URL to encode.
  </definition>
</definitions>

**Description**
URL-encodes the input. All characters are [percent-encoded](https://en.wikipedia.org/wiki/Percent-encoding) except for alphanumerics, `.`, `-`, `_`, and `~`. Spaces are encoded as `+`.
**Supported types**

| string  | result  |
|---------|---------|
| keyword | keyword |
| text    | keyword |

**Example**
```esql
ROW u = "https://example.com/?x=foo bar&y=baz" | EVAL u = URL_ENCODE(u)
```


| u:keyword                                            |
|------------------------------------------------------|
| https%3A%2F%2Fexample.com%2F%3Fx%3Dfoo+bar%26y%3Dbaz |


## `URL_ENCODE_COMPONENT`

```
stack: ga 9.2.0
```

**Syntax**
![Embedded](https://www.elastic.co/docs/reference/query-languages/esql/images/functions/url_encode_component.svg)

**Parameters**
<definitions>
  <definition term="string">
    The URL to encode.
  </definition>
</definitions>

**Description**
URL-encodes the input. All characters are [percent-encoded](https://en.wikipedia.org/wiki/Percent-encoding) except for alphanumerics, `.`, `-`, `_`, and `~`. Spaces are encoded as `%20`.
**Supported types**

| string  | result  |
|---------|---------|
| keyword | keyword |
| text    | keyword |

**Example**
```esql
ROW u = "https://example.com/?x=foo bar&y=baz"
| EVAL u = URL_ENCODE_COMPONENT(u)
```


| u:keyword                                              |
|--------------------------------------------------------|
| https%3A%2F%2Fexample.com%2F%3Fx%3Dfoo%20bar%26y%3Dbaz |


## `URL_DECODE`

```
stack: ga 9.2.0
```

**Syntax**
![Embedded](https://www.elastic.co/docs/reference/query-languages/esql/images/functions/url_decode.svg)

**Parameters**
<definitions>
  <definition term="string">
    The URL-encoded string to decode.
  </definition>
</definitions>

**Description**
URL-decodes the input, or returns `null` and adds a warning header to the response if the input cannot be decoded.
**Supported types**

| string  | result  |
|---------|---------|
| keyword | keyword |
| text    | keyword |

**Example**
```esql
ROW u = "https%3A%2F%2Fexample.com%2F%3Fx%3Dfoo%20bar%26y%3Dbaz"
| EVAL u = URL_DECODE(u)
```


| u:keyword                            |
|--------------------------------------|
| https://example.com/?x=foo bar&y=baz |
