---
title: Use the ES|QL REST API
description: The _query API accepts an ES|QL query string in the query parameter, runs it, and returns the results. For example: Which returns: We recommend using...
url: https://www.elastic.co/docs/reference/query-languages/esql/esql-rest
products:
  - Elasticsearch
---

# Use the ES|QL REST API

<tip>
  The [Search and filter with ES|QL](https://www.elastic.co/docs/reference/query-languages/esql/esql-search-tutorial) tutorial provides a hands-on introduction to the ES|QL `_query` API.
</tip>


## Overview

The [`_query` API](https://www.elastic.co/docs/api/doc/elasticsearch/group/endpoint-esql) accepts an ES|QL query string in the `query` parameter, runs it, and returns the results. For example:
```json

{
  "query": "FROM library | KEEP author, name, page_count, release_date | SORT page_count DESC | LIMIT 5"
}
```

Which returns:
```text
     author      |        name        |  page_count   | release_date
-----------------+--------------------+---------------+------------------------
Peter F. Hamilton|Pandora's Star      |768            |2004-03-02T00:00:00.000Z
Vernor Vinge     |A Fire Upon the Deep|613            |1992-06-01T00:00:00.000Z
Frank Herbert    |Dune                |604            |1965-06-01T00:00:00.000Z
Alastair Reynolds|Revelation Space    |585            |2000-03-15T00:00:00.000Z
James S.A. Corey |Leviathan Wakes     |561            |2011-06-02T00:00:00.000Z
```


### Run the ES|QL query API in Console

We recommend using [Console](https://www.elastic.co/docs/explore-analyze/query-filter/tools/console) to run the ES|QL query API, because of its rich autocomplete features.
When creating the query, using triple quotes (`"""`) allows you to use special characters like quotes (`"`) without having to escape them. They also make it easier to write multi-line requests.
```json

{
  "query": """
    FROM library
    | KEEP author, name, page_count, release_date
    | SORT page_count DESC
    | LIMIT 5
  """
}
```


### Response formats

ES|QL can return the data in the following human readable and binary formats. You can set the format by specifying the `format` parameter in the URL or by setting the `Accept` or `Content-Type` HTTP header.
For example:
```json

{
  "query": """
    FROM library
    | KEEP author, name, page_count, release_date
    | SORT page_count DESC
    | LIMIT 5
  """
}
```

<note>
  The URL parameter takes precedence over the HTTP headers. If neither is specified then the response is returned in the same format as the request.
</note>


#### Structured formats

Complete responses with metadata. Useful for automatic parsing.

| `format` | HTTP header        | Description                                                                                       |
|----------|--------------------|---------------------------------------------------------------------------------------------------|
| `json`   | `application/json` | [JSON](https://www.json.org/)JSON (JavaScript Object Notation) human-readable format              |
| `yaml`   | `application/yaml` | [YAML](https://en.wikipedia.org/wiki/YAML)YAML (YAML Ain’t Markup Language) human-readable format |


#### Tabular formats

Query results only, without metadata. Useful for quick and manual data previews.

| `format` | HTTP header                 | Description                                                                                          |
|----------|-----------------------------|------------------------------------------------------------------------------------------------------|
| `csv`    | `text/csv`                  | [Comma-separated values](https://en.wikipedia.org/wiki/Comma-separated_values)Comma-separated values |
| `tsv`    | `text/tab-separated-values` | [Tab-separated values](https://en.wikipedia.org/wiki/Tab-separated_values)Tab-separated values       |
| `txt`    | `text/plain`                | CLI-like representation                                                                              |

<tip>
  The `csv` format accepts a formatting URL query attribute, `delimiter`, which indicates which character should be used to separate the CSV values. It defaults to comma (`,`) and cannot take any of the following values: double quote (`"`), carriage-return (`\r`) and new-line (`\n`). The tab (`\t`) can also not be used. Use the `tsv` format instead.
</tip>


#### Binary formats

Compact binary encoding. To be used by applications.

| `format` | HTTP header                           | Description                                                                                                                                                                                                          |
|----------|---------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `cbor`   | `application/cbor`                    | [Concise Binary Object Representation](https://cbor.io/)Concise Binary Object Representation                                                                                                                         |
| `smile`  | `application/smile`                   | [Smile](https://en.wikipedia.org/wiki/Smile_(data_interchange_format))Smile binary data format similarto CBOR                                                                                                        |
| `arrow`  | `application/vnd.apache.arrow.stream` | **Experimental.**Experimental. [Apache Arrow](https://arrow.apache.org/)Apache Arrow dataframes, [IPC streaming format](https://arrow.apache.org/docs/format/Columnar.html#ipc-streaming-format)IPC streaming format |


### Filtering using Elasticsearch Query DSL

Specify a Query DSL query in the `filter` parameter to filter the set of documents that an ES|QL query runs on.
```json

{
  "query": """
    FROM library
    | KEEP author, name, page_count, release_date
    | SORT page_count DESC
    | LIMIT 5
  """,
  "filter": {
    "range": {
      "page_count": {
        "gte": 100,
        "lte": 200
      }
    }
  }
}
```

Which returns:
```text
    author     |                name                |  page_count   | release_date
---------------+------------------------------------+---------------+------------------------
Douglas Adams  |The Hitchhiker's Guide to the Galaxy|180            |1979-10-12T00:00:00.000Z
```


#### Filter vs WHERE clause behavior

The `filter` parameter can eliminate columns from the result set when it skips entire indices.
This is useful for resolving type conflicts between attributes of different indices.
For example, if several days of data in a data stream were indexed with an incorrect type, you can use a filter to exclude the incorrect range.
This allows ES|QL to use the correct type for the remaining data without changing the source pattern.

##### Example

Consider querying `index-1` with an `f1` attribute and `index-2` with an `f2` attribute.
Using a filter the following query returns only the `f1` column:
```json

{
  "query": "FROM index-*",
  "filter": {
    "term": {
      "f1": "*"
    }
  }
}
```

Using a WHERE clause returns both the `f1` and `f2` columns:
```json

{
  "query": "FROM index-* WHERE f1 is not null"
}
```


### Columnar results

By default, ES|QL returns results as rows. For example, `FROM` returns each individual document as one row. For the `json`, `yaml`, `cbor` and `smile` [formats](#esql-rest-format), ES|QL can return the results in a columnar fashion where one row represents all the values of a certain column in the results.
```json

{
  "query": """
    FROM library
    | KEEP author, name, page_count, release_date
    | SORT page_count DESC
    | LIMIT 5
  """,
  "columnar": true
}
```

Which returns:
```json
{
  "took": 28,
  "is_partial": false,
  "columns": [
    {"name": "author", "type": "text"},
    {"name": "name", "type": "text"},
    {"name": "page_count", "type": "integer"},
    {"name": "release_date", "type": "date"}
  ],
  "values": [
    ["Peter F. Hamilton", "Vernor Vinge", "Frank Herbert", "Alastair Reynolds", "James S.A. Corey"],
    ["Pandora's Star", "A Fire Upon the Deep", "Dune", "Revelation Space", "Leviathan Wakes"],
    [768, 613, 604, 585, 561],
    ["2004-03-02T00:00:00.000Z", "1992-06-01T00:00:00.000Z", "1965-06-01T00:00:00.000Z", "2000-03-15T00:00:00.000Z", "2011-06-02T00:00:00.000Z"]
  ]
}
```


### Returning localized results

Use the `locale` parameter in the request body to return results (especially dates) formatted per the conventions of the locale. If `locale` is not specified, defaults to `en-US` (English). Refer to [JDK Supported Locales](https://www.oracle.com/java/technologies/javase/jdk17-suported-locales.html).
Syntax: the `locale` parameter accepts language tags in the (case-insensitive) format `xy` and `xy-XY`.
For example, to return a month name in French:
```json

{
  "locale": "fr-FR",
  "query": """
          ROW birth_date_string = "2023-01-15T00:00:00.000Z"
          | EVAL birth_date = date_parse(birth_date_string)
          | EVAL month_of_birth = DATE_FORMAT("MMMM",birth_date)
          | LIMIT 5
   """
}
```


### Passing parameters to a query

Values, for example for a condition, can be passed to a query "inline", by integrating the value in the query string itself:
```json

{
  "query": """
    FROM library
    | EVAL year = DATE_EXTRACT("year", release_date)
    | WHERE page_count > 300 AND author == "Frank Herbert"
    | STATS count = COUNT(*) by year
    | WHERE count > 0
    | LIMIT 5
  """
}
```

To avoid any attempts of hacking or code injection, extract the values in a separate list of parameters. Use question mark placeholders (`?`) in the query string for each of the parameters:
```json

{
  "query": """
    FROM library
    | EVAL year = DATE_EXTRACT("year", release_date)
    | WHERE page_count > ? AND author == ?
    | STATS count = COUNT(*) by year
    | WHERE count > ?
    | LIMIT 5
  """,
  "params": [300, "Frank Herbert", 0]
}
```

The parameters can be named parameters or positional parameters.
Named parameters use question mark placeholders (`?`) followed by a string.
```json

{
  "query": """
    FROM library
    | EVAL year = DATE_EXTRACT("year", release_date)
    | WHERE page_count > ?page_count AND author == ?author
    | STATS count = COUNT(*) by year
    | WHERE count > ?count
    | LIMIT 5
  """,
  "params": [{"page_count" : 300}, {"author" : "Frank Herbert"}, {"count" : 0}]
}
```

Positional parameters use question mark placeholders (`?`) followed by an integer.
```json

{
  "query": """
    FROM library
    | EVAL year = DATE_EXTRACT("year", release_date)
    | WHERE page_count > ?1 AND author == ?2
    | STATS count = COUNT(*) by year
    | WHERE count > ?3
    | LIMIT 5
  """,
  "params": [300, "Frank Herbert", 0]
}
```


### Running an async ES|QL query

The [ES|QL async query API](https://www.elastic.co/docs/api/doc/elasticsearch/operation/operation-esql-async-query) lets you asynchronously execute a query request, monitor its progress, and retrieve results when they become available.
Executing an ES|QL query is commonly quite fast, however queries across large data sets or frozen data can take some time. To avoid long waits, run an async ES|QL query.
Queries initiated by the async query API may return results or not. The `wait_for_completion_timeout` property determines how long to wait for the results. If the results are not available by this time, a [query id](https://www.elastic.co/docs/api/doc/elasticsearch/operation/operation-esql-async-query#esql-async-query-api-response-body-query-id) is returned which can be later used to retrieve the results. For example:
```json

{
  "query": """
    FROM library
    | EVAL year = DATE_TRUNC(1 YEARS, release_date)
    | STATS MAX(page_count) BY year
    | SORT year
    | LIMIT 5
  """,
  "wait_for_completion_timeout": "2s"
}
```

If the results are not available within the given timeout period, 2 seconds in this case, no results are returned but rather a response that includes:
- A query ID
- An `is_running` value of *true*, indicating the query is ongoing

The query continues to run in the background without blocking other requests.
```json
{
  "id": "FmNJRUZ1YWZCU3dHY1BIOUhaenVSRkEaaXFlZ3h4c1RTWFNocDdnY2FSaERnUTozNDE=",
  "is_running": true
}
```

To check the progress of an async query, use the [ES|QL async query get API](https://www.elastic.co/docs/api/doc/elasticsearch/operation/operation-esql-async-query-get) with the query ID. Specify how long you’d like to wait for complete results in the `wait_for_completion_timeout` parameter.
```json
```

If the response’s `is_running` value is `false`, the query has finished and the results are returned, along with the `took` time for the query.
```json
{
  "is_running": false,
  "took": 48,
  "columns": ...
}
```

To stop a running async query and return the results computed so far, use the [async stop API](https://www.elastic.co/docs/api/doc/elasticsearch/operation/operation-esql-async-query-stop) with the query ID.
```json
```

The query will be stopped and the response will contain the results computed so far. The response format is the same as the `get` API.
```json
{
  "is_running": false,
  "took": 48,
  "is_partial": true,
  "columns": ...
}
```

This API can be used to retrieve results even if the query has already completed, as long as it's within the `keep_alive` window.
The `is_partial` field indicates result completeness. A value of `true` means the results are potentially incomplete.
Use the [ES|QL async query delete API](https://www.elastic.co/docs/api/doc/elasticsearch/operation/operation-esql-async-query-delete) to delete an async query before the `keep_alive` period ends. If the query is still running, Elasticsearch cancels it.
```json
```

<note>
  You will also receive the async ID and running status in the `X-Elasticsearch-Async-Id` and `X-Elasticsearch-Async-Is-Running` HTTP headers of the response, respectively.
  Useful if you use a tabular text format like `txt`, `csv` or `tsv`, as you won't receive those fields in the body there.
</note>
