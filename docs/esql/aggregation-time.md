---
title: ES|QL time series aggregation functions
description: The first STATS under a TS source command supports the following time series aggregation functions: 
url: https://www.elastic.co/docs/reference/query-languages/esql/functions-operators/time-series-aggregation-functions
---

# ES|QL time series aggregation functions

The first [`STATS`](https://www.elastic.co/docs/reference/query-languages/esql/commands/stats-by) under
a [`TS`](https://www.elastic.co/docs/reference/query-languages/esql/commands/ts) source command
supports the following time series aggregation functions:
- [`ABSENT_OVER_TIME`](#esql-absent_over_time) `stack: preview 9.2` `serverless: preview`
- [`AVG_OVER_TIME`](#esql-avg_over_time) `stack: preview 9.2` `serverless: preview`
- [`COUNT_OVER_TIME`](#esql-count_over_time) `stack: preview 9.2` `serverless: preview`
- [`COUNT_DISTINCT_OVER_TIME`](#esql-count_distinct_over_time) `stack: preview 9.2` `serverless: preview`
- [`DELTA`](#esql-rate) `stack: preview 9.2` `serverless: preview`
- [`FIRST_OVER_TIME`](#esql-first_over_time) `stack: preview 9.2` `serverless: preview`
- [`IDELTA`](#esql-rate) `stack: preview 9.2` `serverless: preview`
- [`INCREASE`](#esql-rate) `stack: preview 9.2` `serverless: preview`
- [`IRATE`](#esql-rate) `stack: preview 9.2` `serverless: preview`
- [`LAST_OVER_TIME`](#esql-last_over_time) `stack: preview 9.2` `serverless: preview`
- [`MAX_OVER_TIME`](#esql-max_over_time) `stack: preview 9.2` `serverless: preview`
- [`MIN_OVER_TIME`](#esql-min_over_time) `stack: preview 9.2` `serverless: preview`
- [`PRESENT_OVER_TIME`](#esql-present_over_time) `stack: preview 9.2` `serverless: preview`
- [`RATE`](#esql-rate) `stack: preview 9.2` `serverless: preview`
- [`STDDEV_OVER_TIME`](#esql-stddev_over_time) `stack: preview 9.3` `serverless: preview`
- [`VARIANCE_OVER_TIME`](#esql-variance_over_time) `stack: preview 9.3` `serverless: preview`
- [`SUM_OVER_TIME`](#esql-sum_over_time) `stack: preview 9.2` `serverless: preview`


## `ABSENT_OVER_TIME`

```
stack: preview 9.2.0
serverless: preview
```

**Syntax**
![Embedded](https://www.elastic.co/docs/reference/query-languages/esql/images/functions/absent_over_time.svg)

**Parameters**
<definitions>
  <definition term="field">
  </definition>
</definitions>

**Description**
Calculates the absence of a field in the output result over time range.
**Supported types**

| field                   | result  |
|-------------------------|---------|
| aggregate_metric_double | boolean |
| boolean                 | boolean |
| cartesian_point         | boolean |
| cartesian_shape         | boolean |
| date                    | boolean |
| date_nanos              | boolean |
| double                  | boolean |
| geo_point               | boolean |
| geo_shape               | boolean |
| geohash                 | boolean |
| geohex                  | boolean |
| geotile                 | boolean |
| integer                 | boolean |
| ip                      | boolean |
| keyword                 | boolean |
| long                    | boolean |
| text                    | boolean |
| unsigned_long           | boolean |
| version                 | boolean |

**Example**
```esql
TS k8s
| WHERE cluster == "prod" AND pod == "two"
| STATS events_received = MAX(ABSENT_OVER_TIME(events_received)) BY pod, time_bucket = TBUCKET(2 minute)
```


| events_received:boolean | pod:keyword | time_bucket:datetime     |
|-------------------------|-------------|--------------------------|
| false                   | two         | 2024-05-10T00:02:00.000Z |
| false                   | two         | 2024-05-10T00:08:00.000Z |
| true                    | two         | 2024-05-10T00:10:00.000Z |
| true                    | two         | 2024-05-10T00:12:00.000Z |


## `AVG_OVER_TIME`

```
stack: preview 9.2.0
serverless: preview
```

**Syntax**
![Embedded](https://www.elastic.co/docs/reference/query-languages/esql/images/functions/avg_over_time.svg)

**Parameters**
<definitions>
  <definition term="number">
    Expression that outputs values to average.
  </definition>
</definitions>

**Description**
Calculates the average over time of a numeric field.
**Supported types**

| number                  | result |
|-------------------------|--------|
| aggregate_metric_double | double |
| double                  | double |
| integer                 | double |
| long                    | double |

**Example**
```esql
TS k8s
| STATS max_cost=MAX(AVG_OVER_TIME(network.cost)) BY cluster, time_bucket = TBUCKET(1minute)
```


| max_cost:double | cluster:keyword | time_bucket:datetime     |
|-----------------|-----------------|--------------------------|
| 12.375          | prod            | 2024-05-10T00:17:00.000Z |
| 12.375          | qa              | 2024-05-10T00:01:00.000Z |
| 12.25           | prod            | 2024-05-10T00:19:00.000Z |
| 12.0625         | qa              | 2024-05-10T00:06:00.000Z |


## `COUNT_OVER_TIME`

```
stack: preview 9.2.0
serverless: preview
```

**Syntax**
![Embedded](https://www.elastic.co/docs/reference/query-languages/esql/images/functions/count_over_time.svg)

**Parameters**
<definitions>
  <definition term="field">
  </definition>
</definitions>

**Description**
Calculates the count over time value of a field.
**Supported types**

| field                   | result |
|-------------------------|--------|
| aggregate_metric_double | long   |
| boolean                 | long   |
| cartesian_point         | long   |
| cartesian_shape         | long   |
| date                    | long   |
| date_nanos              | long   |
| double                  | long   |
| geo_point               | long   |
| geo_shape               | long   |
| geohash                 | long   |
| geohex                  | long   |
| geotile                 | long   |
| integer                 | long   |
| ip                      | long   |
| keyword                 | long   |
| long                    | long   |
| text                    | long   |
| unsigned_long           | long   |
| version                 | long   |

**Example**
```esql
TS k8s
| STATS count=COUNT(COUNT_OVER_TIME(network.cost))
  BY cluster, time_bucket = BUCKET(@timestamp,1minute)
```


| count:long | cluster:keyword | time_bucket:datetime     |
|------------|-----------------|--------------------------|
| 3          | staging         | 2024-05-10T00:22:00.000Z |
| 3          | prod            | 2024-05-10T00:20:00.000Z |
| 3          | prod            | 2024-05-10T00:19:00.000Z |


## `COUNT_DISTINCT_OVER_TIME`

```
stack: preview 9.2.0
serverless: preview
```

**Syntax**
![Embedded](https://www.elastic.co/docs/reference/query-languages/esql/images/functions/count_distinct_over_time.svg)

**Parameters**
<definitions>
  <definition term="field">
  </definition>
  <definition term="precision">
    Precision threshold. Refer to [`AGG-COUNT-DISTINCT-APPROXIMATE`](/docs/reference/query-languages/esql/functions-operators/aggregation-functions#esql-agg-count-distinct-approximate). The maximum supported value is 40000. Thresholds above this number will have the same effect as a threshold of 40000. The default value is 3000.
  </definition>
</definitions>

**Description**
Calculates the count of distinct values over time for a field.
**Supported types**

| field      | precision     | result |
|------------|---------------|--------|
| boolean    | integer       | long   |
| boolean    | long          | long   |
| boolean    | unsigned_long | long   |
| boolean    |               | long   |
| date       | integer       | long   |
| date       | long          | long   |
| date       | unsigned_long | long   |
| date       |               | long   |
| date_nanos | integer       | long   |
| date_nanos | long          | long   |
| date_nanos | unsigned_long | long   |
| date_nanos |               | long   |
| double     | integer       | long   |
| double     | long          | long   |
| double     | unsigned_long | long   |
| double     |               | long   |
| integer    | integer       | long   |
| integer    | long          | long   |
| integer    | unsigned_long | long   |
| integer    |               | long   |
| ip         | integer       | long   |
| ip         | long          | long   |
| ip         | unsigned_long | long   |
| ip         |               | long   |
| keyword    | integer       | long   |
| keyword    | long          | long   |
| keyword    | unsigned_long | long   |
| keyword    |               | long   |
| long       | integer       | long   |
| long       | long          | long   |
| long       | unsigned_long | long   |
| long       |               | long   |
| text       | integer       | long   |
| text       | long          | long   |
| text       | unsigned_long | long   |
| text       |               | long   |
| version    | integer       | long   |
| version    | long          | long   |
| version    | unsigned_long | long   |
| version    |               | long   |

**Example**
```esql
TS k8s
| STATS distincts=COUNT_DISTINCT(COUNT_DISTINCT_OVER_TIME(network.cost)),
        distincts_imprecise=COUNT_DISTINCT(COUNT_DISTINCT_OVER_TIME(network.cost, 100))
  BY cluster, time_bucket = TBUCKET(1minute)
```


| distincts:long | distincts_imprecise:long | cluster:keyword | time_bucket:datetime     |
|----------------|--------------------------|-----------------|--------------------------|
| 3              | 3                        | qa              | 2024-05-10T00:17:00.000Z |
| 3              | 3                        | qa              | 2024-05-10T00:15:00.000Z |
| 3              | 3                        | prod            | 2024-05-10T00:09:00.000Z |


## `DELTA`

```
stack: preview 9.2.0
serverless: preview
```

**Syntax**
![Embedded](https://www.elastic.co/docs/reference/query-languages/esql/images/functions/delta.svg)

**Parameters**
<definitions>
  <definition term="field">
  </definition>
</definitions>

**Description**
Calculates the absolute change of a gauge field in a time window.
**Supported types**

| field   | result |
|---------|--------|
| double  | double |
| integer | double |
| long    | double |

**Example**
```esql
TS k8s
| WHERE pod == "one"
| STATS tx = SUM(DELTA(network.bytes_in)) BY cluster, time_bucket = TBUCKET(10minute)
```


| tx:double | cluster:keyword | time_bucket:datetime     |
|-----------|-----------------|--------------------------|
| -351.0    | prod            | 2024-05-10T00:00:00.000Z |
| 552.0     | qa              | 2024-05-10T00:00:00.000Z |
| 127.0     | staging         | 2024-05-10T00:00:00.000Z |
| 280.0     | prod            | 2024-05-10T00:10:00.000Z |


## `FIRST_OVER_TIME`

```
stack: preview 9.2.0
serverless: preview
```

**Syntax**
![Embedded](https://www.elastic.co/docs/reference/query-languages/esql/images/functions/first_over_time.svg)

**Parameters**
<definitions>
  <definition term="field">
  </definition>
</definitions>

**Description**
Calculates the earliest value of a field, where recency determined by the `@timestamp` field.
**Supported types**

| field           | result  |
|-----------------|---------|
| counter_double  | double  |
| counter_integer | integer |
| counter_long    | long    |
| double          | double  |
| integer         | integer |
| long            | long    |

**Example**
```esql
TS k8s
| STATS max_cost=MAX(FIRST_OVER_TIME(network.cost)) BY cluster, time_bucket = TBUCKET(1minute)
```


| max_cost:double | cluster:keyword | time_bucket:datetime     |
|-----------------|-----------------|--------------------------|
| 12.375          | prod            | 2024-05-10T00:17:00.000Z |
| 12.375          | qa              | 2024-05-10T00:01:00.000Z |
| 12.25           | prod            | 2024-05-10T00:19:00.000Z |


## `IDELTA`

```
stack: preview 9.2.0
serverless: preview
```

**Syntax**
![Embedded](https://www.elastic.co/docs/reference/query-languages/esql/images/functions/idelta.svg)

**Parameters**
<definitions>
  <definition term="field">
  </definition>
</definitions>

**Description**
Calculates the idelta of a gauge. idelta is the absolute change between the last two data points (it ignores all but the last two data points in each time period). This function is very similar to delta, but is more responsive to recent changes.
**Supported types**

| field   | result |
|---------|--------|
| double  | double |
| integer | double |
| long    | double |

**Example**
```esql
TS k8s
| STATS events = SUM(IDELTA(events_received)) by pod, time_bucket = TBUCKET(10minute)
```


| events:double | pod:keyword | time_bucket:datetime     |
|---------------|-------------|--------------------------|
| 9.0           | one         | 2024-05-10T00:10:00.000Z |
| 7.0           | three       | 2024-05-10T00:10:00.000Z |
| 3.0           | two         | 2024-05-10T00:00:00.000Z |
| 0.0           | two         | 2024-05-10T00:20:00.000Z |


## `INCREASE`

```
stack: preview 9.2.0
serverless: preview
```

**Syntax**
![Embedded](https://www.elastic.co/docs/reference/query-languages/esql/images/functions/increase.svg)

**Parameters**
<definitions>
  <definition term="field">
  </definition>
</definitions>

**Description**
Calculates the absolute increase of a counter field in a time window.
**Supported types**

| field           | result |
|-----------------|--------|
| counter_double  | double |
| counter_integer | double |
| counter_long    | double |

**Example**
```esql
TS k8s
| WHERE pod == "one"
| STATS increase_bytes_in = SUM(INCREASE(network.total_bytes_in)) BY cluster, time_bucket = TBUCKET(10minute)
```


| increase_bytes_in:double | cluster:keyword | time_bucket:datetime     |
|--------------------------|-----------------|--------------------------|
| 2418.8749174917493       | prod            | 2024-05-10T00:00:00.000Z |
| 5973.5                   | qa              | 2024-05-10T00:00:00.000Z |
| 2545.467283950617        | staging         | 2024-05-10T00:00:00.000Z |


## `IRATE`

```
stack: preview 9.2.0
serverless: preview
```

**Syntax**
![Embedded](https://www.elastic.co/docs/reference/query-languages/esql/images/functions/irate.svg)

**Parameters**
<definitions>
  <definition term="field">
  </definition>
</definitions>

**Description**
Calculates the irate of a counter field. irate is the per-second rate of increase between the last two data points (it ignores all but the last two data points in each time period). This function is very similar to rate, but is more responsive to recent changes in the rate of increase.
**Supported types**

| field           | result |
|-----------------|--------|
| counter_double  | double |
| counter_integer | double |
| counter_long    | double |

**Example**
```esql
TS k8s | WHERE pod == "one"
| STATS irate_bytes_in = SUM(IRATE(network.total_bytes_in)) BY cluster, time_bucket = TBUCKET(10minute)
```


| irate_bytes_in:double | cluster:keyword | time_bucket:datetime     |
|-----------------------|-----------------|--------------------------|
| 0.07692307692307693   | prod            | 2024-05-10T00:00:00.000Z |
| 830.0                 | qa              | 2024-05-10T00:00:00.000Z |
| 31.375                | staging         | 2024-05-10T00:00:00.000Z |
| 9.854545454545454     | prod            | 2024-05-10T00:10:00.000Z |
| 18.700000000000003    | qa              | 2024-05-10T00:10:00.000Z |


## `LAST_OVER_TIME`

```
stack: preview 9.2.0
serverless: preview
```

**Syntax**
![Embedded](https://www.elastic.co/docs/reference/query-languages/esql/images/functions/last_over_time.svg)

**Parameters**
<definitions>
  <definition term="field">
  </definition>
</definitions>

**Description**
Calculates the latest value of a field, where recency determined by the `@timestamp` field.
**Supported types**

| field           | result  |
|-----------------|---------|
| counter_double  | double  |
| counter_integer | integer |
| counter_long    | long    |
| double          | double  |
| integer         | integer |
| long            | long    |

**Example**
```esql
TS k8s
| STATS max_cost=MAX(LAST_OVER_TIME(network.cost)) BY cluster, time_bucket = TBUCKET(1minute)
```


| max_cost:double | cluster:keyword | time_bucket:datetime     |
|-----------------|-----------------|--------------------------|
| 12.5            | staging         | 2024-05-10T00:09:00.000Z |
| 12.375          | prod            | 2024-05-10T00:17:00.000Z |
| 12.375          | qa              | 2024-05-10T00:06:00.000Z |
| 12.375          | qa              | 2024-05-10T00:01:00.000Z |


## `MAX_OVER_TIME`

```
stack: preview 9.2.0
serverless: preview
```

**Syntax**
![Embedded](https://www.elastic.co/docs/reference/query-languages/esql/images/functions/max_over_time.svg)

**Parameters**
<definitions>
  <definition term="field">
  </definition>
</definitions>

**Description**
Calculates the maximum over time value of a field.
**Supported types**

| field                           | result        |
|---------------------------------|---------------|
| aggregate_metric_double         | double        |
| boolean                         | boolean       |
| date                            | date          |
| date_nanos                      | date_nanos    |
| double                          | double        |
| integer                         | integer       |
| ip                              | ip            |
| keyword                         | keyword       |
| long                            | long          |
| text                            | keyword       |
| unsigned_long `stack: ga 9.2.0` | unsigned_long |
| version                         | version       |

**Example**
```esql
TS k8s
| STATS cost=SUM(MAX_OVER_TIME(network.cost)) BY cluster, time_bucket = TBUCKET(1minute)
```


| cost:double | cluster:keyword | time_bucket:datetime     |
|-------------|-----------------|--------------------------|
| 32.75       | qa              | 2024-05-10T00:17:00.000Z |
| 32.25       | staging         | 2024-05-10T00:09:00.000Z |
| 31.75       | qa              | 2024-05-10T00:06:00.000Z |
| 29.0        | prod            | 2024-05-10T00:19:00.000Z |


## `MIN_OVER_TIME`

```
stack: preview 9.2.0
serverless: preview
```

**Syntax**
![Embedded](https://www.elastic.co/docs/reference/query-languages/esql/images/functions/min_over_time.svg)

**Parameters**
<definitions>
  <definition term="field">
  </definition>
</definitions>

**Description**
Calculates the minimum over time value of a field.
**Supported types**

| field                           | result        |
|---------------------------------|---------------|
| aggregate_metric_double         | double        |
| boolean                         | boolean       |
| date                            | date          |
| date_nanos                      | date_nanos    |
| double                          | double        |
| integer                         | integer       |
| ip                              | ip            |
| keyword                         | keyword       |
| long                            | long          |
| text                            | keyword       |
| unsigned_long `stack: ga 9.2.0` | unsigned_long |
| version                         | version       |

**Example**
```esql
TS k8s
| STATS cost=SUM(MIN_OVER_TIME(network.cost)) BY cluster, time_bucket = TBUCKET(1minute)
```


| cost:double | cluster:keyword | time_bucket:datetime     |
|-------------|-----------------|--------------------------|
| 29.0        | prod            | 2024-05-10T00:19:00.000Z |
| 27.625      | qa              | 2024-05-10T00:06:00.000Z |
| 24.25       | qa              | 2024-05-10T00:09:00.000Z |


## `PRESENT_OVER_TIME`

```
stack: preview 9.2.0
serverless: preview
```

**Syntax**
![Embedded](https://www.elastic.co/docs/reference/query-languages/esql/images/functions/present_over_time.svg)

**Parameters**
<definitions>
  <definition term="field">
  </definition>
</definitions>

**Description**
Calculates the presence of a field in the output result over time range.
**Supported types**

| field                   | result  |
|-------------------------|---------|
| aggregate_metric_double | boolean |
| boolean                 | boolean |
| cartesian_point         | boolean |
| cartesian_shape         | boolean |
| date                    | boolean |
| date_nanos              | boolean |
| double                  | boolean |
| geo_point               | boolean |
| geo_shape               | boolean |
| geohash                 | boolean |
| geohex                  | boolean |
| geotile                 | boolean |
| integer                 | boolean |
| ip                      | boolean |
| keyword                 | boolean |
| long                    | boolean |
| text                    | boolean |
| unsigned_long           | boolean |
| version                 | boolean |

**Example**
```esql
TS k8s
| WHERE cluster == "prod" AND pod == "two"
| STATS events_received = MAX(PRESENT_OVER_TIME(events_received)) BY pod, time_bucket = TBUCKET(2 minute)
```


| events_received:boolean | pod:keyword | time_bucket:datetime     |
|-------------------------|-------------|--------------------------|
| true                    | two         | 2024-05-10T00:02:00.000Z |
| true                    | two         | 2024-05-10T00:08:00.000Z |
| false                   | two         | 2024-05-10T00:10:00.000Z |
| false                   | two         | 2024-05-10T00:12:00.000Z |


## `RATE`

```
stack: preview 9.2.0
serverless: preview
```

**Syntax**
![Embedded](https://www.elastic.co/docs/reference/query-languages/esql/images/functions/rate.svg)

**Parameters**
<definitions>
  <definition term="field">
  </definition>
</definitions>

**Description**
Calculates the per-second average rate of increase of a [counter](https://www.elastic.co/docs/manage-data/data-store/data-streams/time-series-data-stream-tsds#time-series-metric). Rate calculations account for breaks in monotonicity, such as counter resets when a service restarts, and extrapolate values within each bucketed time interval. Rate is the most appropriate aggregate function for counters. It is only allowed in a [STATS](https://www.elastic.co/docs/reference/query-languages/esql/commands/stats-by) command under a [`TS`](https://www.elastic.co/docs/reference/query-languages/esql/commands/ts) source command, to be properly applied per time series.
**Supported types**

| field           | result |
|-----------------|--------|
| counter_double  | double |
| counter_integer | double |
| counter_long    | double |

**Example**
```esql
TS k8s
| STATS max_rate=MAX(RATE(network.total_bytes_in)) BY time_bucket = TBUCKET(5minute)
```


| max_rate: double   | time_bucket:date         |
|--------------------|--------------------------|
| 6.980660660660663  | 2024-05-10T00:20:00.000Z |
| 23.702205882352942 | 2024-05-10T00:15:00.000Z |


## `STDDEV_OVER_TIME`

```
stack: preview 9.3.0
serverless: preview
```

**Syntax**
![Embedded](https://www.elastic.co/docs/reference/query-languages/esql/images/functions/stddev_over_time.svg)

**Parameters**
<definitions>
  <definition term="number">
    Expression that outputs values to calculate the standard deviation of.
  </definition>
</definitions>

**Description**
Calculates the population standard deviation over time of a numeric field.
**Supported types**

| number  | result |
|---------|--------|
| double  | double |
| integer | double |
| long    | double |

**Example**
```esql
TS k8s
| STATS max_stddev_cost=MAX(STDDEV_OVER_TIME(network.cost)) BY cluster, time_bucket = TBUCKET(1minute)
```


| cluster:keyword | time_bucket:datetime     | max_stddev_cost:double |
|-----------------|--------------------------|------------------------|
| staging         | 2024-05-10T00:03:00.000Z | 5.4375                 |
| staging         | 2024-05-10T00:09:00.000Z | 5.1875                 |
| qa              | 2024-05-10T00:18:00.000Z | 4.097764               |
| qa              | 2024-05-10T00:21:00.000Z | 4.0                    |
| staging         | 2024-05-10T00:20:00.000Z | 3.9375                 |


## `VARIANCE_OVER_TIME`

```
stack: preview 9.3.0
serverless: preview
```

**Syntax**
![Embedded](https://www.elastic.co/docs/reference/query-languages/esql/images/functions/variance_over_time.svg)

**Parameters**
<definitions>
  <definition term="number">
    Expression for which to calculate the variance over time.
  </definition>
</definitions>

**Description**
Calculates the population variance over time of a numeric field.
**Supported types**

| number  | result |
|---------|--------|
| double  | double |
| integer | double |
| long    | double |

**Example**
```esql
TS k8s
| STATS avg_var_cost=AVG(VARIANCE_OVER_TIME(network.cost)) BY cluster, time_bucket = TBUCKET(1minute)
```


| cluster:keyword | time_bucket:datetime     | avg_var_cost:double |
|-----------------|--------------------------|---------------------|
| staging         | 2024-05-10T00:03:00.000Z | 20.478516           |
| qa              | 2024-05-10T00:21:00.000Z | 16.0                |
| qa              | 2024-05-10T00:18:00.000Z | 11.192274           |
| staging         | 2024-05-10T00:09:00.000Z | 10.446904           |


## `SUM_OVER_TIME`

```
stack: preview 9.2.0
serverless: preview
```

**Syntax**
![Embedded](https://www.elastic.co/docs/reference/query-languages/esql/images/functions/sum_over_time.svg)

**Parameters**
<definitions>
  <definition term="field">
  </definition>
</definitions>

**Description**
Calculates the sum over time value of a field.
**Supported types**

| field                   | result |
|-------------------------|--------|
| aggregate_metric_double | double |
| double                  | double |
| integer                 | long   |
| long                    | long   |

**Example**
```esql
TS k8s
| STATS sum_cost=SUM(SUM_OVER_TIME(network.cost)) BY cluster, time_bucket = TBUCKET(1minute)
```


| sum_cost:double | cluster:keyword | time_bucket:datetime     |
|-----------------|-----------------|--------------------------|
| 67.625          | qa              | 2024-05-10T00:17:00.000Z |
| 65.75           | staging         | 2024-05-10T00:09:00.000Z |
