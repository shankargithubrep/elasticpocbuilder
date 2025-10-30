---
title: ES|QL type conversion functions
description: ES|QL supports these type conversion functions: 
url: https://www.elastic.co/docs/reference/query-languages/esql/functions-operators/type-conversion-functions
---

# ES|QL type conversion functions

<tip>
  ES|QL supports implicit casting from string literals to certain data types. Refer to [implicit casting](https://www.elastic.co/docs/reference/query-languages/esql/esql-implicit-casting) for details.
</tip>

ES|QL supports these type conversion functions:
- [`TO_BOOLEAN`](#esql-to_boolean)
- [`TO_CARTESIANPOINT`](#esql-to_cartesianpoint)
- [`TO_CARTESIANSHAPE`](#esql-to_cartesianshape)
- [`TO_DATEPERIOD`](#esql-to_dateperiod)
- [`TO_DATETIME`](#esql-to_datetime)
- [`TO_DATE_NANOS`](#esql-to_date_nanos)
- [`TO_DEGREES`](#esql-to_degrees)
- [`TO_DOUBLE`](#esql-to_double)
- [`TO_GEOHASH`](#esql-to_geohash) `stack: preview` `serverless: preview`
- [`TO_GEOHEX`](#esql-to_geohex) `stack: preview` `serverless: preview`
- [`TO_GEOPOINT`](#esql-to_geopoint)
- [`TO_GEOSHAPE`](#esql-to_geoshape)
- [`TO_GEOTILE`](#esql-to_geotile) `stack: preview` `serverless: preview`
- [`TO_INTEGER`](#esql-to_integer)
- [`TO_IP`](#esql-to_ip)
- [`TO_LONG`](#esql-to_long)
- [`TO_RADIANS`](#esql-to_radians)
- [`TO_STRING`](#esql-to_string)
- [`TO_TIMEDURATION`](#esql-to_timeduration)
- [`TO_UNSIGNED_LONG`](#esql-to_unsigned_long) `stack: preview` `serverless: preview`
- [`TO_VERSION`](#esql-to_version)


## `TO_BOOLEAN`

**Syntax**
![Embedded](https://www.elastic.co/docs/reference/query-languages/esql/images/functions/to_boolean.svg)

**Parameters**
<definitions>
  <definition term="field">
    Input value. The input can be a single- or multi-valued column or an expression.
  </definition>
</definitions>

**Description**
Converts an input value to a boolean value. A string value of `true` will be case-insensitive converted to the Boolean `true`. For anything else, including the empty string, the function will return `false`. The numerical value of `0` will be converted to `false`, anything else will be converted to `true`.
**Supported types**

| field         | result  |
|---------------|---------|
| boolean       | boolean |
| double        | boolean |
| integer       | boolean |
| keyword       | boolean |
| long          | boolean |
| text          | boolean |
| unsigned_long | boolean |

**Example**
```esql
ROW str = ["true", "TRuE", "false", "", "yes", "1"]
| EVAL bool = TO_BOOLEAN(str)
```


| str:keyword                               | bool:boolean                             |
|-------------------------------------------|------------------------------------------|
| ["true", "TRuE", "false", "", "yes", "1"] | [true, true, false, false, false, false] |


## `TO_CARTESIANPOINT`

**Syntax**
![Embedded](https://www.elastic.co/docs/reference/query-languages/esql/images/functions/to_cartesianpoint.svg)

**Parameters**
<definitions>
  <definition term="field">
    Input value. The input can be a single- or multi-valued column or an expression.
  </definition>
</definitions>

**Description**
Converts an input value to a `cartesian_point` value. A string will only be successfully converted if it respects the [WKT Point](https://en.wikipedia.org/wiki/Well-known_text_representation_of_geometry) format.
**Supported types**

| field           | result          |
|-----------------|-----------------|
| cartesian_point | cartesian_point |
| keyword         | cartesian_point |
| text            | cartesian_point |

**Example**
```esql
ROW wkt = ["POINT(4297.11 -1475.53)", "POINT(7580.93 2272.77)"]
| MV_EXPAND wkt
| EVAL pt = TO_CARTESIANPOINT(wkt)
```


| wkt:keyword               | pt:cartesian_point      |
|---------------------------|-------------------------|
| "POINT(4297.11 -1475.53)" | POINT(4297.11 -1475.53) |
| "POINT(7580.93 2272.77)"  | POINT(7580.93 2272.77)  |


## `TO_CARTESIANSHAPE`

**Syntax**
![Embedded](https://www.elastic.co/docs/reference/query-languages/esql/images/functions/to_cartesianshape.svg)

**Parameters**
<definitions>
  <definition term="field">
    Input value. The input can be a single- or multi-valued column or an expression.
  </definition>
</definitions>

**Description**
Converts an input value to a `cartesian_shape` value. A string will only be successfully converted if it respects the [WKT](https://en.wikipedia.org/wiki/Well-known_text_representation_of_geometry) format.
**Supported types**

| field           | result          |
|-----------------|-----------------|
| cartesian_point | cartesian_shape |
| cartesian_shape | cartesian_shape |
| keyword         | cartesian_shape |
| text            | cartesian_shape |

**Example**
```esql
ROW wkt = ["POINT(4297.11 -1475.53)", "POLYGON ((3339584.72 1118889.97, 4452779.63 4865942.27, 2226389.81 4865942.27, 1113194.90 2273030.92, 3339584.72 1118889.97))"]
| MV_EXPAND wkt
| EVAL geom = TO_CARTESIANSHAPE(wkt)
```


| wkt:keyword                                                                                                                     | geom:cartesian_shape                                                                                                          |
|---------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------|
| "POINT(4297.11 -1475.53)"                                                                                                       | POINT(4297.11 -1475.53)                                                                                                       |
| "POLYGON ((3339584.72 1118889.97, 4452779.63 4865942.27, 2226389.81 4865942.27, 1113194.90 2273030.92, 3339584.72 1118889.97))" | POLYGON ((3339584.72 1118889.97, 4452779.63 4865942.27, 2226389.81 4865942.27, 1113194.90 2273030.92, 3339584.72 1118889.97)) |


## `TO_DATEPERIOD`

**Syntax**
![Embedded](https://www.elastic.co/docs/reference/query-languages/esql/images/functions/to_dateperiod.svg)

**Parameters**
<definitions>
  <definition term="field">
    Input value. The input is a valid constant date period expression.
  </definition>
</definitions>

**Description**
Converts an input value into a `date_period` value.
**Supported types**

| field       | result      |
|-------------|-------------|
| date_period | date_period |
| keyword     | date_period |
| text        | date_period |

**Example**
```esql
ROW x = "2024-01-01"::datetime
| EVAL y = x + "3 DAYS"::date_period, z = x - TO_DATEPERIOD("3 days");
```


| x:datetime | y:datetime | z:datetime |
|------------|------------|------------|
| 2024-01-01 | 2024-01-04 | 2023-12-29 |


## `TO_DATETIME`

**Syntax**
![Embedded](https://www.elastic.co/docs/reference/query-languages/esql/images/functions/to_datetime.svg)

**Parameters**
<definitions>
  <definition term="field">
    Input value. The input can be a single- or multi-valued column or an expression.
  </definition>
</definitions>

**Description**
Converts an input value to a date value. A string will only be successfully converted if it’s respecting the format `yyyy-MM-dd'T'HH:mm:ss.SSS'Z'`. To convert dates in other formats, use [`DATE_PARSE`](/docs/reference/query-languages/esql/functions-operators/date-time-functions#esql-date_parse).
<note>
  Note that when converting from nanosecond resolution to millisecond resolution with this function, the nanosecond date is truncated, not rounded.
</note>

**Supported types**

| field         | result |
|---------------|--------|
| date          | date   |
| date_nanos    | date   |
| double        | date   |
| integer       | date   |
| keyword       | date   |
| long          | date   |
| text          | date   |
| unsigned_long | date   |

**Examples**
```esql
ROW string = ["1953-09-02T00:00:00.000Z", "1964-06-02T00:00:00.000Z", "1964-06-02 00:00:00"]
| EVAL datetime = TO_DATETIME(string)
```


| string:keyword                                                                  | datetime:date                                        |
|---------------------------------------------------------------------------------|------------------------------------------------------|
| ["1953-09-02T00:00:00.000Z", "1964-06-02T00:00:00.000Z", "1964-06-02 00:00:00"] | [1953-09-02T00:00:00.000Z, 1964-06-02T00:00:00.000Z] |

Note that in this example, the last value in the source multi-valued field has not been converted.
The reason being that if the date format is not respected, the conversion will result in a `null` value.
When this happens a _Warning_ header is added to the response.
The header will provide information on the source of the failure:
`"Line 1:112: evaluation of [TO_DATETIME(string)] failed, treating result as null. "Only first 20 failures recorded."`
A following header will contain the failure reason and the offending value:
`"java.lang.IllegalArgumentException: failed to parse date field [1964-06-02 00:00:00] with format [yyyy-MM-dd'T'HH:mm:ss.SSS'Z']"`
If the input parameter is of a numeric type,
its value will be interpreted as milliseconds since the [Unix epoch](https://en.wikipedia.org/wiki/Unix_time). For example:
```esql
ROW int = [0, 1]
| EVAL dt = TO_DATETIME(int)
```


| int:integer | dt:date                                              |
|-------------|------------------------------------------------------|
| [0, 1]      | [1970-01-01T00:00:00.000Z, 1970-01-01T00:00:00.001Z] |


## `TO_DATE_NANOS`

**Syntax**
![Embedded](https://www.elastic.co/docs/reference/query-languages/esql/images/functions/to_date_nanos.svg)

**Parameters**
<definitions>
  <definition term="field">
    Input value. The input can be a single- or multi-valued column or an expression.
  </definition>
</definitions>

**Description**
Converts an input to a nanosecond-resolution date value (aka date_nanos).
<note>
  The range for date nanos is 1970-01-01T00:00:00.000000000Z to 2262-04-11T23:47:16.854775807Z, attempting to convert values outside of that range will result in null with a warning.  Additionally, integers cannot be converted into date nanos, as the range of integer nanoseconds only covers about 2 seconds after epoch.
</note>

**Supported types**

| field         | result     |
|---------------|------------|
| date          | date_nanos |
| date_nanos    | date_nanos |
| double        | date_nanos |
| keyword       | date_nanos |
| long          | date_nanos |
| text          | date_nanos |
| unsigned_long | date_nanos |

**Example**
```esql
FROM date_nanos
| WHERE MV_MIN(nanos) < TO_DATE_NANOS("2023-10-23T12:27:28.948Z")
    AND millis > "2000-01-01"
| SORT nanos DESC
```


| millis:date              | nanos:date_nanos               | num:long            |
|--------------------------|--------------------------------|---------------------|
| 2023-10-23T12:15:03.360Z | 2023-10-23T12:15:03.360103847Z | 1698063303360103847 |
| 2023-10-23T12:15:03.360Z | 2023-10-23T12:15:03.360103847Z | 1698063303360103847 |


## `TO_DEGREES`

**Syntax**
![Embedded](https://www.elastic.co/docs/reference/query-languages/esql/images/functions/to_degrees.svg)

**Parameters**
<definitions>
  <definition term="number">
    Input value. The input can be a single- or multi-valued column or an expression.
  </definition>
</definitions>

**Description**
Converts a number in [radians](https://en.wikipedia.org/wiki/Radian) to [degrees](https://en.wikipedia.org/wiki/Degree_(angle)).
**Supported types**

| number        | result |
|---------------|--------|
| double        | double |
| integer       | double |
| long          | double |
| unsigned_long | double |

**Example**
```esql
ROW rad = [1.57, 3.14, 4.71]
| EVAL deg = TO_DEGREES(rad)
```


| rad:double         | deg:double                                                 |
|--------------------|------------------------------------------------------------|
| [1.57, 3.14, 4.71] | [89.95437383553924, 179.9087476710785, 269.86312150661774] |


## `TO_DOUBLE`

**Syntax**
![Embedded](https://www.elastic.co/docs/reference/query-languages/esql/images/functions/to_double.svg)

**Parameters**
<definitions>
  <definition term="field">
    Input value. The input can be a single- or multi-valued column or an expression.
  </definition>
</definitions>

**Description**
Converts an input value to a double value. If the input parameter is of a date type, its value will be interpreted as milliseconds since the [Unix epoch](https://en.wikipedia.org/wiki/Unix_time), converted to double. Boolean `true` will be converted to double `1.0`, `false` to `0.0`.
**Supported types**

| field           | result |
|-----------------|--------|
| boolean         | double |
| counter_double  | double |
| counter_integer | double |
| counter_long    | double |
| date            | double |
| double          | double |
| integer         | double |
| keyword         | double |
| long            | double |
| text            | double |
| unsigned_long   | double |

**Example**
```esql
ROW str1 = "5.20128E11", str2 = "foo"
| EVAL dbl = TO_DOUBLE("520128000000"), dbl1 = TO_DOUBLE(str1), dbl2 = TO_DOUBLE(str2)
```


| str1:keyword | str2:keyword | dbl:double | dbl1:double | dbl2:double |
|--------------|--------------|------------|-------------|-------------|
| 5.20128E11   | foo          | 5.20128E11 | 5.20128E11  | null        |

Note that in this example, the last conversion of the string isn’t possible.
When this happens, the result is a `null` value. In this case a _Warning_ header is added to the response.
The header will provide information on the source of the failure:
`"Line 1:115: evaluation of [TO_DOUBLE(str2)] failed, treating result as null. Only first 20 failures recorded."`
A following header will contain the failure reason and the offending value:
`"java.lang.NumberFormatException: For input string: "foo""`

## `TO_GEOHASH`

```
stack: preview
serverless: preview
```

**Syntax**
![Embedded](https://www.elastic.co/docs/reference/query-languages/esql/images/functions/to_geohash.svg)

**Parameters**
<definitions>
  <definition term="field">
    Input value. The input can be a single- or multi-valued column or an expression.
  </definition>
</definitions>

**Description**
Converts an input value to a `geohash` value. A string will only be successfully converted if it respects the `geohash` format, as described for the [geohash grid aggregation](https://www.elastic.co/docs/reference/aggregations/search-aggregations-bucket-geohashgrid-aggregation).
**Supported types**

| field   | result  |
|---------|---------|
| geohash | geohash |
| keyword | geohash |
| long    | geohash |
| text    | geohash |

**Example**
```esql
ROW string = "u3bu"
| EVAL geohash = TO_GEOHASH(string)
```


| string:keyword | geohash:geohash |
|----------------|-----------------|
| u3bu           | u3bu            |


## `TO_GEOHEX`

```
stack: preview
serverless: preview
```

**Syntax**
![Embedded](https://www.elastic.co/docs/reference/query-languages/esql/images/functions/to_geohex.svg)

**Parameters**
<definitions>
  <definition term="field">
    Input value. The input can be a single- or multi-valued column or an expression.
  </definition>
</definitions>

**Description**
Converts an input value to a `geohex` value. A string will only be successfully converted if it respects the `geohex` format, as described for the [geohex grid aggregation](https://www.elastic.co/docs/reference/aggregations/search-aggregations-bucket-geohexgrid-aggregation).
**Supported types**

| field   | result |
|---------|--------|
| geohex  | geohex |
| keyword | geohex |
| long    | geohex |
| text    | geohex |

**Example**
```esql
ROW string = "841f059ffffffff"
| EVAL geohex = TO_GEOHEX(string)
```


| string:keyword  | geohex:geohex   |
|-----------------|-----------------|
| 841f059ffffffff | 841f059ffffffff |


## `TO_GEOPOINT`

**Syntax**
![Embedded](https://www.elastic.co/docs/reference/query-languages/esql/images/functions/to_geopoint.svg)

**Parameters**
<definitions>
  <definition term="field">
    Input value. The input can be a single- or multi-valued column or an expression.
  </definition>
</definitions>

**Description**
Converts an input value to a `geo_point` value. A string will only be successfully converted if it respects the [WKT Point](https://en.wikipedia.org/wiki/Well-known_text_representation_of_geometry) format.
**Supported types**

| field     | result    |
|-----------|-----------|
| geo_point | geo_point |
| keyword   | geo_point |
| text      | geo_point |

**Example**
```esql
ROW wkt = "POINT(42.97109630194 14.7552534413725)"
| EVAL pt = TO_GEOPOINT(wkt)
```


| wkt:keyword                              | pt:geo_point                           |
|------------------------------------------|----------------------------------------|
| "POINT(42.97109630194 14.7552534413725)" | POINT(42.97109630194 14.7552534413725) |


## `TO_GEOSHAPE`

**Syntax**
![Embedded](https://www.elastic.co/docs/reference/query-languages/esql/images/functions/to_geoshape.svg)

**Parameters**
<definitions>
  <definition term="field">
    Input value. The input can be a single- or multi-valued column or an expression.
  </definition>
</definitions>

**Description**
Converts an input value to a `geo_shape` value. A string will only be successfully converted if it respects the [WKT](https://en.wikipedia.org/wiki/Well-known_text_representation_of_geometry) format.
**Supported types**

| field     | result    |
|-----------|-----------|
| geo_point | geo_shape |
| geo_shape | geo_shape |
| geohash   | geo_shape |
| geohex    | geo_shape |
| geotile   | geo_shape |
| keyword   | geo_shape |
| text      | geo_shape |

**Example**
```esql
ROW wkt = "POLYGON ((30 10, 40 40, 20 40, 10 20, 30 10))"
| EVAL geom = TO_GEOSHAPE(wkt)
```


| wkt:keyword                                     | geom:geo_shape                                |
|-------------------------------------------------|-----------------------------------------------|
| "POLYGON ((30 10, 40 40, 20 40, 10 20, 30 10))" | POLYGON ((30 10, 40 40, 20 40, 10 20, 30 10)) |


## `TO_GEOTILE`

```
stack: preview
serverless: preview
```

**Syntax**
![Embedded](https://www.elastic.co/docs/reference/query-languages/esql/images/functions/to_geotile.svg)

**Parameters**
<definitions>
  <definition term="field">
    Input value. The input can be a single- or multi-valued column or an expression.
  </definition>
</definitions>

**Description**
Converts an input value to a `geotile` value. A string will only be successfully converted if it respects the `geotile` format, as described for the [geotile grid aggregation](https://www.elastic.co/docs/reference/aggregations/search-aggregations-bucket-geotilegrid-aggregation).
**Supported types**

| field   | result  |
|---------|---------|
| geotile | geotile |
| keyword | geotile |
| long    | geotile |
| text    | geotile |

**Example**
```esql
ROW string = "4/8/5"
| EVAL geotile = TO_GEOTILE(string)
```


| string:keyword | geotile:geotile |
|----------------|-----------------|
| 4/8/5          | 4/8/5           |


## `TO_INTEGER`

**Syntax**
![Embedded](https://www.elastic.co/docs/reference/query-languages/esql/images/functions/to_integer.svg)

**Parameters**
<definitions>
  <definition term="field">
    Input value. The input can be a single- or multi-valued column or an expression.
  </definition>
</definitions>

**Description**
Converts an input value to an integer value. If the input parameter is of a date type, its value will be interpreted as milliseconds since the [Unix epoch](https://en.wikipedia.org/wiki/Unix_time), converted to integer. Boolean `true` will be converted to integer `1`, `false` to `0`.
**Supported types**

| field           | result  |
|-----------------|---------|
| boolean         | integer |
| counter_integer | integer |
| date            | integer |
| double          | integer |
| integer         | integer |
| keyword         | integer |
| long            | integer |
| text            | integer |
| unsigned_long   | integer |

**Example**
```esql
ROW long = [5013792, 2147483647, 501379200000]
| EVAL int = TO_INTEGER(long)
```


| long:long                           | int:integer           |
|-------------------------------------|-----------------------|
| [5013792, 2147483647, 501379200000] | [5013792, 2147483647] |

Note that in this example, the last value of the multi-valued field cannot be converted as an integer.
When this happens, the result is a `null` value. In this case a _Warning_ header is added to the response.
The header will provide information on the source of the failure:
`"Line 1:61: evaluation of [TO_INTEGER(long)] failed, treating result as null. Only first 20 failures recorded."`
A following header will contain the failure reason and the offending value:
`"org.elasticsearch.xpack.esql.core.InvalidArgumentException: [501379200000] out of [integer] range"`

## `TO_IP`

**Syntax**
![Embedded](https://www.elastic.co/docs/reference/query-languages/esql/images/functions/to_ip.svg)

**Parameters**
<definitions>
  <definition term="field">
    Input value. The input can be a single- or multi-valued column or an expression.
  </definition>
  <definition term="options">
    (Optional) Additional options.
  </definition>
</definitions>

**Description**
Converts an input string to an IP value.
**Supported types**

| field   | options | result |
|---------|---------|--------|
| ip      |         | ip     |
| keyword |         | ip     |
| text    |         | ip     |

**Supported function named parameters**
<definitions>
  <definition term="leading_zeros">
    (keyword) What to do with leading 0s in IPv4 addresses.
  </definition>
</definitions>

**Examples**
```esql
ROW str1 = "1.1.1.1", str2 = "foo"
| EVAL ip1 = TO_IP(str1), ip2 = TO_IP(str2)
| WHERE CIDR_MATCH(ip1, "1.0.0.0/8")
```


| str1:keyword | str2:keyword | ip1:ip  | ip2:ip |
|--------------|--------------|---------|--------|
| 1.1.1.1      | foo          | 1.1.1.1 | null   |

Note that in this example, the last conversion of the string isn’t possible.
When this happens, the result is a `null` value. In this case a _Warning_ header is added to the response.
The header will provide information on the source of the failure:
`"Line 1:68: evaluation of [TO_IP(str2)] failed, treating result as null. Only first 20 failures recorded."`
A following header will contain the failure reason and the offending value:
`"java.lang.IllegalArgumentException: 'foo' is not an IP string literal."`
```esql
ROW s = "1.1.010.1" | EVAL ip = TO_IP(s, {"leading_zeros":"octal"})
```


| s:keyword | ip:ip   |
|-----------|---------|
| 1.1.010.1 | 1.1.8.1 |

Parse v4 addresses with leading zeros as octal. Like `ping` or `ftp`.
```esql
ROW s = "1.1.010.1" | EVAL ip = TO_IP(s, {"leading_zeros":"decimal"})
```


| s:keyword | ip:ip    |
|-----------|----------|
| 1.1.010.1 | 1.1.10.1 |

Parse v4 addresses with leading zeros as decimal. Java's `InetAddress.getByName`.

## `TO_LONG`

**Syntax**
![Embedded](https://www.elastic.co/docs/reference/query-languages/esql/images/functions/to_long.svg)

**Parameters**
<definitions>
  <definition term="field">
    Input value. The input can be a single- or multi-valued column or an expression.
  </definition>
</definitions>

**Description**
Converts an input value to a long value. If the input parameter is of a date type, its value will be interpreted as milliseconds since the [Unix epoch](https://en.wikipedia.org/wiki/Unix_time), converted to long. Boolean `true` will be converted to long `1`, `false` to `0`.
**Supported types**

| field           | result |
|-----------------|--------|
| boolean         | long   |
| counter_integer | long   |
| counter_long    | long   |
| date            | long   |
| date_nanos      | long   |
| double          | long   |
| geohash         | long   |
| geohex          | long   |
| geotile         | long   |
| integer         | long   |
| keyword         | long   |
| long            | long   |
| text            | long   |
| unsigned_long   | long   |

**Example**
```esql
ROW str1 = "2147483648", str2 = "2147483648.2", str3 = "foo"
| EVAL long1 = TO_LONG(str1), long2 = TO_LONG(str2), long3 = TO_LONG(str3)
```


| str1:keyword | str2:keyword | str3:keyword | long1:long | long2:long | long3:long |
|--------------|--------------|--------------|------------|------------|------------|
| 2147483648   | 2147483648.2 | foo          | 2147483648 | 2147483648 | null       |

Note that in this example, the last conversion of the string isn’t possible.
When this happens, the result is a `null` value. In this case a _Warning_ header is added to the response.
The header will provide information on the source of the failure:
`"Line 1:113: evaluation of [TO_LONG(str3)] failed, treating result as null. Only first 20 failures recorded."`
A following header will contain the failure reason and the offending value:
`"java.lang.NumberFormatException: For input string: "foo""`

## `TO_RADIANS`

**Syntax**
![Embedded](https://www.elastic.co/docs/reference/query-languages/esql/images/functions/to_radians.svg)

**Parameters**
<definitions>
  <definition term="number">
    Input value. The input can be a single- or multi-valued column or an expression.
  </definition>
</definitions>

**Description**
Converts a number in [degrees](https://en.wikipedia.org/wiki/Degree_(angle)) to [radians](https://en.wikipedia.org/wiki/Radian).
**Supported types**

| number        | result |
|---------------|--------|
| double        | double |
| integer       | double |
| long          | double |
| unsigned_long | double |

**Example**
```esql
ROW deg = [90.0, 180.0, 270.0]
| EVAL rad = TO_RADIANS(deg)
```


| deg:double           | rad:double                                                |
|----------------------|-----------------------------------------------------------|
| [90.0, 180.0, 270.0] | [1.5707963267948966, 3.141592653589793, 4.71238898038469] |


## `TO_STRING`

**Syntax**
![Embedded](https://www.elastic.co/docs/reference/query-languages/esql/images/functions/to_string.svg)

**Parameters**
<definitions>
  <definition term="field">
    Input value. The input can be a single- or multi-valued column or an expression.
  </definition>
</definitions>

**Description**
Converts an input value into a string.
**Supported types**

| field                   | result  |
|-------------------------|---------|
| aggregate_metric_double | keyword |
| boolean                 | keyword |
| cartesian_point         | keyword |
| cartesian_shape         | keyword |
| date                    | keyword |
| date_nanos              | keyword |
| dense_vector            | keyword |
| double                  | keyword |
| geo_point               | keyword |
| geo_shape               | keyword |
| geohash                 | keyword |
| geohex                  | keyword |
| geotile                 | keyword |
| integer                 | keyword |
| ip                      | keyword |
| keyword                 | keyword |
| long                    | keyword |
| text                    | keyword |
| unsigned_long           | keyword |
| version                 | keyword |

**Examples**
```esql
ROW a=10
| EVAL j = TO_STRING(a)
```


| a:integer | j:keyword |
|-----------|-----------|
| 10        | "10"      |

It also works fine on multivalued fields:
```esql
ROW a=[10, 9, 8]
| EVAL j = TO_STRING(a)
```


| a:integer  | j:keyword        |
|------------|------------------|
| [10, 9, 8] | ["10", "9", "8"] |


## `TO_TIMEDURATION`

**Syntax**
![Embedded](https://www.elastic.co/docs/reference/query-languages/esql/images/functions/to_timeduration.svg)

**Parameters**
<definitions>
  <definition term="field">
    Input value. The input is a valid constant time duration expression.
  </definition>
</definitions>

**Description**
Converts an input value into a `time_duration` value.
**Supported types**

| field         | result        |
|---------------|---------------|
| keyword       | time_duration |
| text          | time_duration |
| time_duration | time_duration |

**Example**
```esql
ROW x = "2024-01-01"::datetime
| EVAL y = x + "3 hours"::time_duration, z = x - TO_TIMEDURATION("3 hours");
```


| x:datetime | y:datetime               | z:datetime               |
|------------|--------------------------|--------------------------|
| 2024-01-01 | 2024-01-01T03:00:00.000Z | 2023-12-31T21:00:00.000Z |


## `TO_UNSIGNED_LONG`

```
stack: preview
serverless: preview
```

**Syntax**
![Embedded](https://www.elastic.co/docs/reference/query-languages/esql/images/functions/to_unsigned_long.svg)

**Parameters**
<definitions>
  <definition term="field">
    Input value. The input can be a single- or multi-valued column or an expression.
  </definition>
</definitions>

**Description**
Converts an input value to an unsigned long value. If the input parameter is of a date type, its value will be interpreted as milliseconds since the [Unix epoch](https://en.wikipedia.org/wiki/Unix_time), converted to unsigned long. Boolean `true` will be converted to unsigned long `1`, `false` to `0`.
**Supported types**

| field         | result        |
|---------------|---------------|
| boolean       | unsigned_long |
| date          | unsigned_long |
| double        | unsigned_long |
| integer       | unsigned_long |
| keyword       | unsigned_long |
| long          | unsigned_long |
| text          | unsigned_long |
| unsigned_long | unsigned_long |

**Example**
```esql
ROW str1 = "2147483648", str2 = "2147483648.2", str3 = "foo"
| EVAL long1 = TO_UNSIGNED_LONG(str1), long2 = TO_ULONG(str2), long3 = TO_UL(str3)
```


| str1:keyword | str2:keyword | str3:keyword | long1:unsigned_long | long2:unsigned_long | long3:unsigned_long |
|--------------|--------------|--------------|---------------------|---------------------|---------------------|
| 2147483648   | 2147483648.2 | foo          | 2147483648          | 2147483648          | null                |

Note that in this example, the last conversion of the string isn’t possible.
When this happens, the result is a `null` value. In this case a _Warning_ header is added to the response.
The header will provide information on the source of the failure:
`"Line 1:133: evaluation of [TO_UL(str3)] failed, treating result as null. Only first 20 failures recorded."`
A following header will contain the failure reason and the offending value:
`"java.lang.NumberFormatException: Character f is neither a decimal digit number, decimal point,
- "nor "e" notation exponential mark."`


## `TO_VERSION`

**Syntax**
![Embedded](https://www.elastic.co/docs/reference/query-languages/esql/images/functions/to_version.svg)

**Parameters**
<definitions>
  <definition term="field">
    Input value. The input can be a single- or multi-valued column or an expression.
  </definition>
</definitions>

**Description**
Converts an input string to a version value.
**Supported types**

| field   | result  |
|---------|---------|
| keyword | version |
| text    | version |
| version | version |

**Example**
```esql
ROW v = TO_VERSION("1.2.3")
```


| v:version |
|-----------|
| 1.2.3     |
