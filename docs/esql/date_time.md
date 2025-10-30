---
title: ES|QL date-time functions
description: ES|QL supports these date-time functions: 
url: https://www.elastic.co/docs/reference/query-languages/esql/functions-operators/date-time-functions
---

# ES|QL date-time functions

ES|QL supports these date-time functions:
- [`DATE_DIFF`](#esql-date_diff)
- [`DATE_EXTRACT`](#esql-date_extract)
- [`DATE_FORMAT`](#esql-date_format)
- [`DATE_PARSE`](#esql-date_parse)
- [`DATE_TRUNC`](#esql-date_trunc)
- [`DAY_NAME`](#esql-day_name)
- [`MONTH_NAME`](#esql-month_name)
- [`NOW`](#esql-now)
- [`TRANGE`](#esql-trange)


## `DATE_DIFF`

**Syntax**
![Embedded](https://www.elastic.co/docs/reference/query-languages/esql/images/functions/date_diff.svg)

**Parameters**
<definitions>
  <definition term="unit">
    Time difference unit
  </definition>
  <definition term="startTimestamp">
    A string representing a start timestamp
  </definition>
  <definition term="endTimestamp">
    A string representing an end timestamp
  </definition>
</definitions>

**Description**
Subtracts the `startTimestamp` from the `endTimestamp` and returns the difference in multiples of `unit`. If `startTimestamp` is later than the `endTimestamp`, negative values are returned.
**Datetime difference units**

| unit        | abbreviations     |
|-------------|-------------------|
| year        | years, yy, yyyy   |
| quarter     | quarters, qq, q   |
| month       | months, mm, m     |
| dayofyear   | dy, y             |
| day         | days, dd, d       |
| week        | weeks, wk, ww     |
| weekday     | weekdays, dw      |
| hour        | hours, hh         |
| minute      | minutes, mi, n    |
| second      | seconds, ss, s    |
| millisecond | milliseconds, ms  |
| microsecond | microseconds, mcs |
| nanosecond  | nanoseconds, ns   |

Note that while there is an overlap between the function’s supported units and
ES|QL’s supported time span literals, these sets are distinct and not
interchangeable. Similarly, the supported abbreviations are conveniently shared
with implementations of this function in other established products and not
necessarily common with the date-time nomenclature used by Elasticsearch.
**Supported types**

| unit    | startTimestamp | endTimestamp | result  |
|---------|----------------|--------------|---------|
| keyword | date           | date         | integer |
| keyword | date           | date_nanos   | integer |
| keyword | date_nanos     | date         | integer |
| keyword | date_nanos     | date_nanos   | integer |
| text    | date           | date         | integer |
| text    | date           | date_nanos   | integer |
| text    | date_nanos     | date         | integer |
| text    | date_nanos     | date_nanos   | integer |

**Examples**
```esql
ROW date1 = TO_DATETIME("2023-12-02T11:00:00.000Z"),
    date2 = TO_DATETIME("2023-12-02T11:00:00.001Z")
| EVAL dd_ms = DATE_DIFF("microseconds", date1, date2)
```


| date1:date               | date2:date               | dd_ms:integer |
|--------------------------|--------------------------|---------------|
| 2023-12-02T11:00:00.000Z | 2023-12-02T11:00:00.001Z | 1000          |

When subtracting in calendar units - like year, month a.s.o. - only the fully elapsed units are counted.
To avoid this and obtain also remainders, simply switch to the next smaller unit and do the date math accordingly.
```esql
ROW end_23 = TO_DATETIME("2023-12-31T23:59:59.999Z"),
  start_24 = TO_DATETIME("2024-01-01T00:00:00.000Z"),
    end_24 = TO_DATETIME("2024-12-31T23:59:59.999")
| EVAL end23_to_start24 = DATE_DIFF("year", end_23, start_24)
| EVAL end23_to_end24   = DATE_DIFF("year", end_23, end_24)
| EVAL start_to_end_24  = DATE_DIFF("year", start_24, end_24)
```


| end_23:date              | start_24:date            | end_24:date              | end23_to_start24:integer | end23_to_end24:integer | start_to_end_24:integer |
|--------------------------|--------------------------|--------------------------|--------------------------|------------------------|-------------------------|
| 2023-12-31T23:59:59.999Z | 2024-01-01T00:00:00.000Z | 2024-12-31T23:59:59.999Z | 0                        | 1                      | 0                       |


## `DATE_EXTRACT`

**Syntax**
![Embedded](https://www.elastic.co/docs/reference/query-languages/esql/images/functions/date_extract.svg)

**Parameters**
<definitions>
  <definition term="datePart">
    Part of the date to extract.  Can be: `aligned_day_of_week_in_month`, `aligned_day_of_week_in_year`, `aligned_week_of_month`, `aligned_week_of_year`, `ampm_of_day`, `clock_hour_of_ampm`, `clock_hour_of_day`, `day_of_month`, `day_of_week`, `day_of_year`, `epoch_day`, `era`, `hour_of_ampm`, `hour_of_day`, `instant_seconds`, `micro_of_day`, `micro_of_second`, `milli_of_day`, `milli_of_second`, `minute_of_day`, `minute_of_hour`, `month_of_year`, `nano_of_day`, `nano_of_second`, `offset_seconds`, `proleptic_month`, `second_of_day`, `second_of_minute`, `year`, or `year_of_era`. Refer to [java.time.temporal.ChronoField](https://docs.oracle.com/javase/8/docs/api/java/time/temporal/ChronoField.html) for a description of these values.  If `null`, the function returns `null`.
  </definition>
  <definition term="date">
    Date expression. If `null`, the function returns `null`.
  </definition>
</definitions>

**Description**
Extracts parts of a date, like year, month, day, hour.
**Supported types**

| datePart | date       | result |
|----------|------------|--------|
| keyword  | date       | long   |
| keyword  | date_nanos | long   |
| text     | date       | long   |
| text     | date_nanos | long   |

**Examples**
```esql
ROW date = DATE_PARSE("yyyy-MM-dd", "2022-05-06")
| EVAL year = DATE_EXTRACT("year", date)
```


| date:date                | year:long |
|--------------------------|-----------|
| 2022-05-06T00:00:00.000Z | 2022      |

Find all events that occurred outside of business hours (before 9 AM or after 5PM), on any given date:
```esql
FROM sample_data
| WHERE DATE_EXTRACT("hour_of_day", @timestamp) < 9
    AND DATE_EXTRACT("hour_of_day", @timestamp) >= 17
```


| @timestamp:date | client_ip:ip | event_duration:long | message:keyword |
|-----------------|--------------|---------------------|-----------------|


## `DATE_FORMAT`

**Syntax**
![Embedded](https://www.elastic.co/docs/reference/query-languages/esql/images/functions/date_format.svg)

**Parameters**
<definitions>
  <definition term="dateFormat">
    Date format (optional).  If no format is specified, the `yyyy-MM-dd'T'HH:mm:ss.SSSZ` format is used. If `null`, the function returns `null`.
  </definition>
  <definition term="date">
    Date expression. If `null`, the function returns `null`.
  </definition>
</definitions>

**Description**
Returns a string representation of a date, in the provided format.
**Supported types**

| dateFormat | date       | result  |
|------------|------------|---------|
| date       |            | keyword |
| date_nanos |            | keyword |
| keyword    | date       | keyword |
| keyword    | date_nanos | keyword |
| text       | date       | keyword |
| text       | date_nanos | keyword |

**Example**
```esql
FROM employees
| KEEP first_name, last_name, hire_date
| EVAL hired = DATE_FORMAT("yyyy-MM-dd", hire_date)
```


| first_name:keyword | last_name:keyword | hire_date:date           | hired:keyword |
|--------------------|-------------------|--------------------------|---------------|
| Alejandro          | McAlpine          | 1991-06-26T00:00:00.000Z | 1991-06-26    |
| Amabile            | Gomatam           | 1992-11-18T00:00:00.000Z | 1992-11-18    |
| Anneke             | Preusig           | 1989-06-02T00:00:00.000Z | 1989-06-02    |


## `DATE_PARSE`

**Syntax**
![Embedded](https://www.elastic.co/docs/reference/query-languages/esql/images/functions/date_parse.svg)

**Parameters**
<definitions>
  <definition term="datePattern">
    The date format. Refer to the [`DateTimeFormatter` documentation](https://docs.oracle.com/en/java/javase/14/docs/api/java.base/java/time/format/DateTimeFormatter.html) for the syntax. If `null`, the function returns `null`.
  </definition>
  <definition term="dateString">
    Date expression as a string. If `null` or an empty string, the function returns `null`.
  </definition>
  <definition term="options">
    (Optional) Additional options for date parsing, specifying time zone and locale as [function named parameters](/docs/reference/query-languages/esql/esql-syntax#esql-function-named-params).
  </definition>
</definitions>

**Description**
Returns a date by parsing the second argument using the format specified in the first argument.
**Supported types**

| datePattern | dateString | options          | result |
|-------------|------------|------------------|--------|
| keyword     | keyword    | named parameters | date   |
| keyword     | keyword    |                  | date   |
| keyword     | text       |                  | date   |
| text        | keyword    |                  | date   |
| text        | text       |                  | date   |

**Supported function named parameters**
<definitions>
  <definition term="time_zone">
    (keyword) Coordinated Universal Time (UTC) offset or IANA time zone used to convert date values in the query string to UTC.
  </definition>
  <definition term="locale">
    (keyword) The locale to use when parsing the date, relevant when parsing month names or week days.
  </definition>
</definitions>

**Example**
```esql
ROW date_string = "2022-05-06"
| EVAL date = DATE_PARSE("yyyy-MM-dd", date_string)
```


| date_string:keyword | date:date                |
|---------------------|--------------------------|
| 2022-05-06          | 2022-05-06T00:00:00.000Z |


## `DATE_TRUNC`

**Syntax**
![Embedded](https://www.elastic.co/docs/reference/query-languages/esql/images/functions/date_trunc.svg)

**Parameters**
<definitions>
  <definition term="interval">
    Interval; expressed using the timespan literal syntax.
  </definition>
  <definition term="date">
    Date expression
  </definition>
</definitions>

**Description**
Rounds down a date to the closest interval since epoch, which starts at `0001-01-01T00:00:00Z`.
**Supported types**

| interval      | date       | result     |
|---------------|------------|------------|
| date_period   | date       | date       |
| date_period   | date_nanos | date_nanos |
| time_duration | date       | date       |
| time_duration | date_nanos | date_nanos |

**Examples**
```esql
FROM employees
| KEEP first_name, last_name, hire_date
| EVAL year_hired = DATE_TRUNC(1 year, hire_date)
```


| first_name:keyword | last_name:keyword | hire_date:date           | year_hired:date          |
|--------------------|-------------------|--------------------------|--------------------------|
| Alejandro          | McAlpine          | 1991-06-26T00:00:00.000Z | 1991-01-01T00:00:00.000Z |
| Amabile            | Gomatam           | 1992-11-18T00:00:00.000Z | 1992-01-01T00:00:00.000Z |
| Anneke             | Preusig           | 1989-06-02T00:00:00.000Z | 1989-01-01T00:00:00.000Z |

Combine `DATE_TRUNC` with [`STATS`](https://www.elastic.co/docs/reference/query-languages/esql/commands/stats-by) to create date histograms. For example, the number of hires per year:
```esql
FROM employees
| EVAL year = DATE_TRUNC(1 year, hire_date)
| STATS hires = COUNT(emp_no) BY year
| SORT year
```


| hires:long | year:date                |
|------------|--------------------------|
| 11         | 1985-01-01T00:00:00.000Z |
| 11         | 1986-01-01T00:00:00.000Z |
| 15         | 1987-01-01T00:00:00.000Z |
| 9          | 1988-01-01T00:00:00.000Z |
| 13         | 1989-01-01T00:00:00.000Z |
| 12         | 1990-01-01T00:00:00.000Z |
| 6          | 1991-01-01T00:00:00.000Z |
| 8          | 1992-01-01T00:00:00.000Z |
| 3          | 1993-01-01T00:00:00.000Z |
| 4          | 1994-01-01T00:00:00.000Z |
| 5          | 1995-01-01T00:00:00.000Z |
| 1          | 1996-01-01T00:00:00.000Z |
| 1          | 1997-01-01T00:00:00.000Z |
| 1          | 1999-01-01T00:00:00.000Z |

Or an hourly error rate:
```esql
FROM sample_data
| EVAL error = CASE(message LIKE "*error*", 1, 0)
| EVAL hour = DATE_TRUNC(1 hour, @timestamp)
| STATS error_rate = AVG(error) by hour
| SORT hour
```


| error_rate:double | hour:date                |
|-------------------|--------------------------|
| 0.0               | 2023-10-23T12:00:00.000Z |
| 0.6               | 2023-10-23T13:00:00.000Z |


## `DAY_NAME`

```
stack: ga 9.2.0
```

**Syntax**
![Embedded](https://www.elastic.co/docs/reference/query-languages/esql/images/functions/day_name.svg)

**Parameters**
<definitions>
  <definition term="date">
    Date expression. If `null`, the function returns `null`.
  </definition>
</definitions>

**Description**
Returns the name of the weekday for date based on the configured Locale.
**Supported types**

| date       | result  |
|------------|---------|
| date       | keyword |
| date_nanos | keyword |

**Example**
```esql
ROW dt = to_datetime("1953-09-02T00:00:00.000Z")
| EVAL weekday = DAY_NAME(dt);
```


## `MONTH_NAME`

```
stack: ga 9.2.0
```

**Syntax**
![Embedded](https://www.elastic.co/docs/reference/query-languages/esql/images/functions/month_name.svg)

**Parameters**
<definitions>
  <definition term="date">
    Date expression. If `null`, the function returns `null`.
  </definition>
</definitions>

**Description**
Returns the month name for the provided date based on the configured Locale.
**Supported types**

| date       | result  |
|------------|---------|
| date       | keyword |
| date_nanos | keyword |

**Example**
```esql
ROW dt = to_datetime("1996-03-21T00:00:00.000Z")
| EVAL monthName = MONTH_NAME(dt);
```


## `NOW`

**Syntax**
![Embedded](https://www.elastic.co/docs/reference/query-languages/esql/images/functions/now.svg)

**Parameters**
**Description**
Returns current date and time.
**Supported types**

| result |
|--------|
| date   |

**Examples**
```esql
ROW current_date = NOW()
```


| y:keyword |
|-----------|
| 20        |

To retrieve logs from the last hour:
```esql
FROM sample_data
| WHERE @timestamp > NOW() - 1 hour
```


## `TRANGE`

**Syntax**
![Embedded](https://www.elastic.co/docs/reference/query-languages/esql/images/functions/trange.svg)

**Parameters**
<definitions>
  <definition term="start_time_or_offset">
    Offset from NOW for the single parameter mode. Start time for two parameter mode.  In two parameter mode, the start time value can be a date string, date, date_nanos or epoch milliseconds.
  </definition>
  <definition term="end_time">
    Explicit end time that can be a date string, date, date_nanos or epoch milliseconds.
  </definition>
</definitions>

**Description**
Filters data for the given time range using the @timestamp attribute.
**Supported types**

| start_time_or_offset | end_time   | result  |
|----------------------|------------|---------|
| date                 | date       | boolean |
| date_nanos           | date_nanos | boolean |
| date_period          |            | boolean |
| keyword              | keyword    | boolean |
| long                 | long       | boolean |
| time_duration        |            | boolean |

**Examples**
```esql
FROM k8s
| WHERE TRANGE(1h)
| KEEP @timestamp
```

```esql
FROM k8s
| WHERE TRANGE("2024-05-10T00:17:14.000Z", "2024-05-10T00:18:33.000Z")
| SORT @timestamp
| KEEP @timestamp
| LIMIT 10
```


| @timestamp:datetime      |
|--------------------------|
| 2024-05-10T00:17:16.000Z |
| 2024-05-10T00:17:20.000Z |
| 2024-05-10T00:17:30.000Z |
| 2024-05-10T00:17:30.000Z |
| 2024-05-10T00:17:39.000Z |
| 2024-05-10T00:17:39.000Z |
| 2024-05-10T00:17:55.000Z |
| 2024-05-10T00:18:02.000Z |
| 2024-05-10T00:18:02.000Z |
| 2024-05-10T00:18:02.000Z |

```esql
FROM k8s
| WHERE TRANGE(to_datetime("2024-05-10T00:17:14Z"), to_datetime("2024-05-10T00:18:33Z"))
| SORT @timestamp
| KEEP @timestamp
| LIMIT 10
```


| @timestamp:datetime      |
|--------------------------|
| 2024-05-10T00:17:16.000Z |
| 2024-05-10T00:17:20.000Z |
| 2024-05-10T00:17:30.000Z |
| 2024-05-10T00:17:30.000Z |
| 2024-05-10T00:17:39.000Z |
| 2024-05-10T00:17:39.000Z |
| 2024-05-10T00:17:55.000Z |
| 2024-05-10T00:18:02.000Z |
| 2024-05-10T00:18:02.000Z |
| 2024-05-10T00:18:02.000Z |

```esql
FROM k8s
| WHERE TRANGE(to_datetime("2024-05-10T00:17:14.000Z"), to_datetime("2024-05-10T00:18:33.000Z"))
| SORT @timestamp
| KEEP @timestamp
| LIMIT 10
```


| @timestamp:datetime      |
|--------------------------|
| 2024-05-10T00:17:16.000Z |
| 2024-05-10T00:17:20.000Z |
| 2024-05-10T00:17:30.000Z |
| 2024-05-10T00:17:30.000Z |
| 2024-05-10T00:17:39.000Z |
| 2024-05-10T00:17:39.000Z |
| 2024-05-10T00:17:55.000Z |
| 2024-05-10T00:18:02.000Z |
| 2024-05-10T00:18:02.000Z |
| 2024-05-10T00:18:02.000Z |

```esql
FROM k8s
| WHERE TRANGE(1715300236000, 1715300282000)
| SORT @timestamp
| KEEP @timestamp
| LIMIT 10
```


| @timestamp:datetime      |
|--------------------------|
| 2024-05-10T00:17:20.000Z |
| 2024-05-10T00:17:30.000Z |
| 2024-05-10T00:17:30.000Z |
| 2024-05-10T00:17:39.000Z |
| 2024-05-10T00:17:39.000Z |
| 2024-05-10T00:17:55.000Z |
| 2024-05-10T00:18:02.000Z |
| 2024-05-10T00:18:02.000Z |
| 2024-05-10T00:18:02.000Z |
