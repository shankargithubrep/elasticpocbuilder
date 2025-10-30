---
title: ES|QL functions and operators
description: ES|QL provides a comprehensive set of functions and operators for working with data. The reference documentation is divided into the following categories:...
url: https://www.elastic.co/docs/reference/query-languages/esql/esql-functions-operators
---

# ES|QL functions and operators

ES|QL provides a comprehensive set of functions and operators for working with data. The reference documentation is divided into the following categories:

## Functions overview

<dropdown title="Aggregate functions">

  - [`ABSENT`](/docs/reference/query-languages/esql/functions-operators/aggregation-functions#esql-absent) `stack: ga 9.2`
  - [`AVG`](/docs/reference/query-languages/esql/functions-operators/aggregation-functions#esql-avg)
  - [`COUNT`](/docs/reference/query-languages/esql/functions-operators/aggregation-functions#esql-count)
  - [`COUNT_DISTINCT`](/docs/reference/query-languages/esql/functions-operators/aggregation-functions#esql-count_distinct)
  - [`MAX`](/docs/reference/query-languages/esql/functions-operators/aggregation-functions#esql-max)
  - [`MEDIAN`](/docs/reference/query-languages/esql/functions-operators/aggregation-functions#esql-median)
  - [`MEDIAN_ABSOLUTE_DEVIATION`](/docs/reference/query-languages/esql/functions-operators/aggregation-functions#esql-median_absolute_deviation)
  - [`MIN`](/docs/reference/query-languages/esql/functions-operators/aggregation-functions#esql-min)
  - [`PERCENTILE`](/docs/reference/query-languages/esql/functions-operators/aggregation-functions#esql-percentile)
  - [`PRESENT`](/docs/reference/query-languages/esql/functions-operators/aggregation-functions#esql-present) `stack: ga 9.2`
  - [`SAMPLE`](/docs/reference/query-languages/esql/functions-operators/aggregation-functions#esql-sample)
  - [`ST_CENTROID_AGG`](/docs/reference/query-languages/esql/functions-operators/aggregation-functions#esql-st_centroid_agg) `stack: preview` `serverless: preview`
  - [`ST_EXTENT_AGG`](/docs/reference/query-languages/esql/functions-operators/aggregation-functions#esql-st_extent_agg) `stack: preview` `serverless: preview`
  - [`STD_DEV`](/docs/reference/query-languages/esql/functions-operators/aggregation-functions#esql-std_dev)
  - [`SUM`](/docs/reference/query-languages/esql/functions-operators/aggregation-functions#esql-sum)
  - [`TOP`](/docs/reference/query-languages/esql/functions-operators/aggregation-functions#esql-top)
  - [`VALUES`](/docs/reference/query-languages/esql/functions-operators/aggregation-functions#esql-values) `stack: preview` `serverless: preview`
  - [`VARIANCE`](/docs/reference/query-languages/esql/functions-operators/aggregation-functions#esql-variance)
  - [`WEIGHTED_AVG`](/docs/reference/query-languages/esql/functions-operators/aggregation-functions#esql-weighted_avg)
</dropdown>

<dropdown title="Time-series aggregate functions">

  - [`ABSENT_OVER_TIME`](/docs/reference/query-languages/esql/functions-operators/time-series-aggregation-functions#esql-absent_over_time) `stack: preview 9.2` `serverless: preview`
  - [`AVG_OVER_TIME`](/docs/reference/query-languages/esql/functions-operators/time-series-aggregation-functions#esql-avg_over_time) `stack: preview 9.2` `serverless: preview`
  - [`COUNT_OVER_TIME`](/docs/reference/query-languages/esql/functions-operators/time-series-aggregation-functions#esql-count_over_time) `stack: preview 9.2` `serverless: preview`
  - [`COUNT_DISTINCT_OVER_TIME`](/docs/reference/query-languages/esql/functions-operators/time-series-aggregation-functions#esql-count_distinct_over_time) `stack: preview 9.2` `serverless: preview`
  - [`DELTA`](/docs/reference/query-languages/esql/functions-operators/time-series-aggregation-functions#esql-rate) `stack: preview 9.2` `serverless: preview`
  - [`FIRST_OVER_TIME`](/docs/reference/query-languages/esql/functions-operators/time-series-aggregation-functions#esql-first_over_time) `stack: preview 9.2` `serverless: preview`
  - [`IDELTA`](/docs/reference/query-languages/esql/functions-operators/time-series-aggregation-functions#esql-rate) `stack: preview 9.2` `serverless: preview`
  - [`INCREASE`](/docs/reference/query-languages/esql/functions-operators/time-series-aggregation-functions#esql-rate) `stack: preview 9.2` `serverless: preview`
  - [`IRATE`](/docs/reference/query-languages/esql/functions-operators/time-series-aggregation-functions#esql-rate) `stack: preview 9.2` `serverless: preview`
  - [`LAST_OVER_TIME`](/docs/reference/query-languages/esql/functions-operators/time-series-aggregation-functions#esql-last_over_time) `stack: preview 9.2` `serverless: preview`
  - [`MAX_OVER_TIME`](/docs/reference/query-languages/esql/functions-operators/time-series-aggregation-functions#esql-max_over_time) `stack: preview 9.2` `serverless: preview`
  - [`MIN_OVER_TIME`](/docs/reference/query-languages/esql/functions-operators/time-series-aggregation-functions#esql-min_over_time) `stack: preview 9.2` `serverless: preview`
  - [`PRESENT_OVER_TIME`](/docs/reference/query-languages/esql/functions-operators/time-series-aggregation-functions#esql-present_over_time) `stack: preview 9.2` `serverless: preview`
  - [`RATE`](/docs/reference/query-languages/esql/functions-operators/time-series-aggregation-functions#esql-rate) `stack: preview 9.2` `serverless: preview`
  - [`STDDEV_OVER_TIME`](/docs/reference/query-languages/esql/functions-operators/time-series-aggregation-functions#esql-stddev_over_time) `stack: preview 9.3` `serverless: preview`
  - [`VARIANCE_OVER_TIME`](/docs/reference/query-languages/esql/functions-operators/time-series-aggregation-functions#esql-variance_over_time) `stack: preview 9.3` `serverless: preview`
  - [`SUM_OVER_TIME`](/docs/reference/query-languages/esql/functions-operators/time-series-aggregation-functions#esql-sum_over_time) `stack: preview 9.2` `serverless: preview`
</dropdown>

<dropdown title="Grouping functions">

  - [`BUCKET`](/docs/reference/query-languages/esql/functions-operators/grouping-functions#esql-bucket)
  - [`TBUCKET`](/docs/reference/query-languages/esql/functions-operators/grouping-functions#esql-tbucket)
  - [`CATEGORIZE`](/docs/reference/query-languages/esql/functions-operators/grouping-functions#esql-categorize)
</dropdown>

<dropdown title="Conditional functions and expressions">

  - [`CASE`](/docs/reference/query-languages/esql/functions-operators/conditional-functions-and-expressions#esql-case)
  - [`COALESCE`](/docs/reference/query-languages/esql/functions-operators/conditional-functions-and-expressions#esql-coalesce)
  - [`GREATEST`](/docs/reference/query-languages/esql/functions-operators/conditional-functions-and-expressions#esql-greatest)
  - [`LEAST`](/docs/reference/query-languages/esql/functions-operators/conditional-functions-and-expressions#esql-least)
</dropdown>

<dropdown title="Date and time functions">

  - [`DATE_DIFF`](/docs/reference/query-languages/esql/functions-operators/date-time-functions#esql-date_diff)
  - [`DATE_EXTRACT`](/docs/reference/query-languages/esql/functions-operators/date-time-functions#esql-date_extract)
  - [`DATE_FORMAT`](/docs/reference/query-languages/esql/functions-operators/date-time-functions#esql-date_format)
  - [`DATE_PARSE`](/docs/reference/query-languages/esql/functions-operators/date-time-functions#esql-date_parse)
  - [`DATE_TRUNC`](/docs/reference/query-languages/esql/functions-operators/date-time-functions#esql-date_trunc)
  - [`DAY_NAME`](/docs/reference/query-languages/esql/functions-operators/date-time-functions#esql-day_name)
  - [`MONTH_NAME`](/docs/reference/query-languages/esql/functions-operators/date-time-functions#esql-month_name)
  - [`NOW`](/docs/reference/query-languages/esql/functions-operators/date-time-functions#esql-now)
  - [`TRANGE`](/docs/reference/query-languages/esql/functions-operators/date-time-functions#esql-trange)
</dropdown>

<dropdown title="IP functions">

  - [`CIDR_MATCH`](/docs/reference/query-languages/esql/functions-operators/ip-functions#esql-cidr_match)
  - [`IP_PREFIX`](/docs/reference/query-languages/esql/functions-operators/ip-functions#esql-ip_prefix)
</dropdown>

<dropdown title="Math functions">

  - [`ABS`](/docs/reference/query-languages/esql/functions-operators/math-functions#esql-abs)
  - [`ACOS`](/docs/reference/query-languages/esql/functions-operators/math-functions#esql-acos)
  - [`ASIN`](/docs/reference/query-languages/esql/functions-operators/math-functions#esql-asin)
  - [`ATAN`](/docs/reference/query-languages/esql/functions-operators/math-functions#esql-atan)
  - [`ATAN2`](/docs/reference/query-languages/esql/functions-operators/math-functions#esql-atan2)
  - [`CBRT`](/docs/reference/query-languages/esql/functions-operators/math-functions#esql-cbrt)
  - [`CEIL`](/docs/reference/query-languages/esql/functions-operators/math-functions#esql-ceil)
  - [`COPY_SIGN`](/docs/reference/query-languages/esql/functions-operators/math-functions#esql-copy_sign)
  - [`COS`](/docs/reference/query-languages/esql/functions-operators/math-functions#esql-cos)
  - [`COSH`](/docs/reference/query-languages/esql/functions-operators/math-functions#esql-cosh)
  - [`E`](/docs/reference/query-languages/esql/functions-operators/math-functions#esql-e)
  - [`EXP`](/docs/reference/query-languages/esql/functions-operators/math-functions#esql-exp)
  - [`FLOOR`](/docs/reference/query-languages/esql/functions-operators/math-functions#esql-floor)
  - [`HYPOT`](/docs/reference/query-languages/esql/functions-operators/math-functions#esql-hypot)
  - [`LOG`](/docs/reference/query-languages/esql/functions-operators/math-functions#esql-log)
  - [`LOG10`](/docs/reference/query-languages/esql/functions-operators/math-functions#esql-log10)
  - [`PI`](/docs/reference/query-languages/esql/functions-operators/math-functions#esql-pi)
  - [`POW`](/docs/reference/query-languages/esql/functions-operators/math-functions#esql-pow)
  - [`ROUND`](/docs/reference/query-languages/esql/functions-operators/math-functions#esql-round)
  - [`ROUND_TO`](/docs/reference/query-languages/esql/functions-operators/math-functions#esql-round_to)
  - [`SCALB`](/docs/reference/query-languages/esql/functions-operators/math-functions#esql-scalb)
  - [`SIGNUM`](/docs/reference/query-languages/esql/functions-operators/math-functions#esql-signum)
  - [`SIN`](/docs/reference/query-languages/esql/functions-operators/math-functions#esql-sin)
  - [`SINH`](/docs/reference/query-languages/esql/functions-operators/math-functions#esql-sinh)
  - [`SQRT`](/docs/reference/query-languages/esql/functions-operators/math-functions#esql-sqrt)
  - [`TAN`](/docs/reference/query-languages/esql/functions-operators/math-functions#esql-tan)
  - [`TANH`](/docs/reference/query-languages/esql/functions-operators/math-functions#esql-tanh)
  - [`TAU`](/docs/reference/query-languages/esql/functions-operators/math-functions#esql-tau)
</dropdown>

<dropdown title="Search functions">

  - [`KQL`](/docs/reference/query-languages/esql/functions-operators/search-functions#esql-kql)
  - [`MATCH`](/docs/reference/query-languages/esql/functions-operators/search-functions#esql-match)
  - [`MATCH_PHRASE`](/docs/reference/query-languages/esql/functions-operators/search-functions#esql-match_phrase)
  - [`QSTR`](/docs/reference/query-languages/esql/functions-operators/search-functions#esql-qstr)
</dropdown>

<dropdown title="Spatial functions">

  - [`ST_DISTANCE`](/docs/reference/query-languages/esql/functions-operators/spatial-functions#esql-st_distance)
  - [`ST_INTERSECTS`](/docs/reference/query-languages/esql/functions-operators/spatial-functions#esql-st_intersects)
  - [`ST_DISJOINT`](/docs/reference/query-languages/esql/functions-operators/spatial-functions#esql-st_disjoint)
  - [`ST_CONTAINS`](/docs/reference/query-languages/esql/functions-operators/spatial-functions#esql-st_contains)
  - [`ST_WITHIN`](/docs/reference/query-languages/esql/functions-operators/spatial-functions#esql-st_within)
  - [`ST_X`](/docs/reference/query-languages/esql/functions-operators/spatial-functions#esql-st_x)
  - [`ST_Y`](/docs/reference/query-languages/esql/functions-operators/spatial-functions#esql-st_y)
  - [`ST_ENVELOPE`](/docs/reference/query-languages/esql/functions-operators/spatial-functions#esql-st_envelope) `stack: preview` `serverless: preview`  
    - [`ST_XMAX`](/docs/reference/query-languages/esql/functions-operators/spatial-functions#esql-st_xmax) `stack: preview` `serverless: preview`
    - [`ST_XMIN`](/docs/reference/query-languages/esql/functions-operators/spatial-functions#esql-st_xmin) `stack: preview` `serverless: preview`
    - [`ST_YMAX`](/docs/reference/query-languages/esql/functions-operators/spatial-functions#esql-st_ymax) `stack: preview` `serverless: preview`
    - [`ST_YMIN`](/docs/reference/query-languages/esql/functions-operators/spatial-functions#esql-st_ymin) `stack: preview` `serverless: preview`
  - [`ST_GEOTILE`](/docs/reference/query-languages/esql/functions-operators/spatial-functions#esql-st_geotile) `stack: preview` `serverless: preview`
  - [`ST_GEOHEX`](/docs/reference/query-languages/esql/functions-operators/spatial-functions#esql-st_geohex) `stack: preview` `serverless: preview`
  - [`ST_GEOHASH`](/docs/reference/query-languages/esql/functions-operators/spatial-functions#esql-st_geohash) `stack: preview` `serverless: preview`
</dropdown>

<dropdown title="String functions">

  - [`BIT_LENGTH`](/docs/reference/query-languages/esql/functions-operators/string-functions#esql-bit_length)
  - [`BYTE_LENGTH`](/docs/reference/query-languages/esql/functions-operators/string-functions#esql-byte_length)
  - [`CONCAT`](/docs/reference/query-languages/esql/functions-operators/string-functions#esql-concat)
  - [`CONTAINS`](/docs/reference/query-languages/esql/functions-operators/string-functions#esql-contains)
  - [`ENDS_WITH`](/docs/reference/query-languages/esql/functions-operators/string-functions#esql-ends_with)
  - [`FROM_BASE64`](/docs/reference/query-languages/esql/functions-operators/string-functions#esql-from_base64)
  - [`HASH`](/docs/reference/query-languages/esql/functions-operators/string-functions#esql-hash)
  - [`LEFT`](/docs/reference/query-languages/esql/functions-operators/string-functions#esql-left)
  - [`LENGTH`](/docs/reference/query-languages/esql/functions-operators/string-functions#esql-length)
  - [`LOCATE`](/docs/reference/query-languages/esql/functions-operators/string-functions#esql-locate)
  - [`LTRIM`](/docs/reference/query-languages/esql/functions-operators/string-functions#esql-ltrim)
  - [`MD5`](/docs/reference/query-languages/esql/functions-operators/string-functions#esql-md5)
  - [`REPEAT`](/docs/reference/query-languages/esql/functions-operators/string-functions#esql-repeat)
  - [`REPLACE`](/docs/reference/query-languages/esql/functions-operators/string-functions#esql-replace)
  - [`REVERSE`](/docs/reference/query-languages/esql/functions-operators/string-functions#esql-reverse)
  - [`RIGHT`](/docs/reference/query-languages/esql/functions-operators/string-functions#esql-right)
  - [`RTRIM`](/docs/reference/query-languages/esql/functions-operators/string-functions#esql-rtrim)
  - [`SHA1`](/docs/reference/query-languages/esql/functions-operators/string-functions#esql-sha1)
  - [`SHA256`](/docs/reference/query-languages/esql/functions-operators/string-functions#esql-sha256)
  - [`SPACE`](/docs/reference/query-languages/esql/functions-operators/string-functions#esql-space)
  - [`SPLIT`](/docs/reference/query-languages/esql/functions-operators/string-functions#esql-split)
  - [`STARTS_WITH`](/docs/reference/query-languages/esql/functions-operators/string-functions#esql-starts_with)
  - [`SUBSTRING`](/docs/reference/query-languages/esql/functions-operators/string-functions#esql-substring)
  - [`TO_BASE64`](/docs/reference/query-languages/esql/functions-operators/string-functions#esql-to_base64)
  - [`TO_LOWER`](/docs/reference/query-languages/esql/functions-operators/string-functions#esql-to_lower)
  - [`TO_UPPER`](/docs/reference/query-languages/esql/functions-operators/string-functions#esql-to_upper)
  - [`TRIM`](/docs/reference/query-languages/esql/functions-operators/string-functions#esql-trim)
  - [`URL_ENCODE`](/docs/reference/query-languages/esql/functions-operators/string-functions#esql-url_encode)
  - [`URL_ENCODE_COMPONENT`](/docs/reference/query-languages/esql/functions-operators/string-functions#esql-url_encode_component)
  - [`URL_DECODE`](/docs/reference/query-languages/esql/functions-operators/string-functions#esql-url_decode)
</dropdown>

<dropdown title="Type conversion functions">

  - [`TO_BOOLEAN`](/docs/reference/query-languages/esql/functions-operators/type-conversion-functions#esql-to_boolean)
  - [`TO_CARTESIANPOINT`](/docs/reference/query-languages/esql/functions-operators/type-conversion-functions#esql-to_cartesianpoint)
  - [`TO_CARTESIANSHAPE`](/docs/reference/query-languages/esql/functions-operators/type-conversion-functions#esql-to_cartesianshape)
  - [`TO_DATEPERIOD`](/docs/reference/query-languages/esql/functions-operators/type-conversion-functions#esql-to_dateperiod)
  - [`TO_DATETIME`](/docs/reference/query-languages/esql/functions-operators/type-conversion-functions#esql-to_datetime)
  - [`TO_DATE_NANOS`](/docs/reference/query-languages/esql/functions-operators/type-conversion-functions#esql-to_date_nanos)
  - [`TO_DEGREES`](/docs/reference/query-languages/esql/functions-operators/type-conversion-functions#esql-to_degrees)
  - [`TO_DOUBLE`](/docs/reference/query-languages/esql/functions-operators/type-conversion-functions#esql-to_double)
  - [`TO_GEOHASH`](/docs/reference/query-languages/esql/functions-operators/type-conversion-functions#esql-to_geohash) `stack: preview` `serverless: preview`
  - [`TO_GEOHEX`](/docs/reference/query-languages/esql/functions-operators/type-conversion-functions#esql-to_geohex) `stack: preview` `serverless: preview`
  - [`TO_GEOPOINT`](/docs/reference/query-languages/esql/functions-operators/type-conversion-functions#esql-to_geopoint)
  - [`TO_GEOSHAPE`](/docs/reference/query-languages/esql/functions-operators/type-conversion-functions#esql-to_geoshape)
  - [`TO_GEOTILE`](/docs/reference/query-languages/esql/functions-operators/type-conversion-functions#esql-to_geotile) `stack: preview` `serverless: preview`
  - [`TO_INTEGER`](/docs/reference/query-languages/esql/functions-operators/type-conversion-functions#esql-to_integer)
  - [`TO_IP`](/docs/reference/query-languages/esql/functions-operators/type-conversion-functions#esql-to_ip)
  - [`TO_LONG`](/docs/reference/query-languages/esql/functions-operators/type-conversion-functions#esql-to_long)
  - [`TO_RADIANS`](/docs/reference/query-languages/esql/functions-operators/type-conversion-functions#esql-to_radians)
  - [`TO_STRING`](/docs/reference/query-languages/esql/functions-operators/type-conversion-functions#esql-to_string)
  - [`TO_TIMEDURATION`](/docs/reference/query-languages/esql/functions-operators/type-conversion-functions#esql-to_timeduration)
  - [`TO_UNSIGNED_LONG`](/docs/reference/query-languages/esql/functions-operators/type-conversion-functions#esql-to_unsigned_long) `stack: preview` `serverless: preview`
  - [`TO_VERSION`](/docs/reference/query-languages/esql/functions-operators/type-conversion-functions#esql-to_version)
</dropdown>

<dropdown title="Dense vector functions">

  - [`KNN`](/docs/reference/query-languages/esql/functions-operators/dense-vector-functions#esql-knn) `stack: preview 9.2` `serverless: preview`
  - [`TEXT_EMBEDDING`](/docs/reference/query-languages/esql/functions-operators/dense-vector-functions#esql-text_embedding) `stack: preview 9.3` `serverless: preview`
</dropdown>

<dropdown title="Multi value functions">

  - [`MV_APPEND`](/docs/reference/query-languages/esql/functions-operators/mv-functions#esql-mv_append)
  - [`MV_AVG`](/docs/reference/query-languages/esql/functions-operators/mv-functions#esql-mv_avg)
  - [`MV_CONCAT`](/docs/reference/query-languages/esql/functions-operators/mv-functions#esql-mv_concat)
  - [`MV_CONTAINS`](/docs/reference/query-languages/esql/functions-operators/mv-functions#esql-mv_contains) `stack: preview` `serverless: preview`
  - [`MV_COUNT`](/docs/reference/query-languages/esql/functions-operators/mv-functions#esql-mv_count)
  - [`MV_DEDUPE`](/docs/reference/query-languages/esql/functions-operators/mv-functions#esql-mv_dedupe)
  - [`MV_FIRST`](/docs/reference/query-languages/esql/functions-operators/mv-functions#esql-mv_first)
  - [`MV_LAST`](/docs/reference/query-languages/esql/functions-operators/mv-functions#esql-mv_last)
  - [`MV_MAX`](/docs/reference/query-languages/esql/functions-operators/mv-functions#esql-mv_max)
  - [`MV_MEDIAN`](/docs/reference/query-languages/esql/functions-operators/mv-functions#esql-mv_median)
  - [`MV_MEDIAN_ABSOLUTE_DEVIATION`](/docs/reference/query-languages/esql/functions-operators/mv-functions#esql-mv_median_absolute_deviation)
  - [`MV_MIN`](/docs/reference/query-languages/esql/functions-operators/mv-functions#esql-mv_min)
  - [`MV_PERCENTILE`](/docs/reference/query-languages/esql/functions-operators/mv-functions#esql-mv_percentile)
  - [`MV_PSERIES_WEIGHTED_SUM`](/docs/reference/query-languages/esql/functions-operators/mv-functions#esql-mv_pseries_weighted_sum)
  - [`MV_SORT`](/docs/reference/query-languages/esql/functions-operators/mv-functions#esql-mv_sort)
  - [`MV_SLICE`](/docs/reference/query-languages/esql/functions-operators/mv-functions#esql-mv_slice)
  - [`MV_SUM`](/docs/reference/query-languages/esql/functions-operators/mv-functions#esql-mv_sum)
  - [`MV_ZIP`](/docs/reference/query-languages/esql/functions-operators/mv-functions#esql-mv_zip)
</dropdown>


## Operators overview

<dropdown title="Operators">

  - [Binary operators](/docs/reference/query-languages/esql/functions-operators/operators#esql-binary-operators)
  - [Unary operators](/docs/reference/query-languages/esql/functions-operators/operators#esql-unary-operators)
  - [Logical operators](/docs/reference/query-languages/esql/functions-operators/operators#esql-logical-operators)
  - [suffix operators](/docs/reference/query-languages/esql/functions-operators/operators#esql-suffix-operators)
  - [infix operators](/docs/reference/query-languages/esql/functions-operators/operators#esql-infix-operators)
</dropdown>
