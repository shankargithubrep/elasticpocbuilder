---
title: ES|QL metadata fields
description: ES|QL can access metadata fields. To access these fields, use the METADATA directive with the FROM source command. For example: The following metadata...
url: https://www.elastic.co/docs/reference/query-languages/esql/esql-metadata-fields
---

# ES|QL metadata fields

ES|QL can access [metadata fields](https://www.elastic.co/docs/reference/elasticsearch/mapping-reference/document-metadata-fields).
To access these fields, use the `METADATA` directive with the [`FROM`](https://www.elastic.co/docs/reference/query-languages/esql/commands/from) source command. For example:
```esql
FROM index METADATA _index, _id
```


## Available metadata fields

The following metadata fields are available in ES|QL:

| Metadata field                                                                                                      | Type                                                                                            | Description                                                                                                                                                                                                                  |
|---------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| [`_id`](https://www.elastic.co/docs/reference/elasticsearch/mapping-reference/mapping-id-field)`_id`                | [keyword](https://www.elastic.co/docs/reference/elasticsearch/mapping-reference/keyword)keyword | Unique document ID.                                                                                                                                                                                                          |
| [`_ignored`](https://www.elastic.co/docs/reference/elasticsearch/mapping-reference/mapping-ignored-field)`_ignored` | [keyword](https://www.elastic.co/docs/reference/elasticsearch/mapping-reference/keyword)keyword | Names every field in a document that was ignored when the document was indexed.                                                                                                                                              |
| [`_index`](https://www.elastic.co/docs/reference/elasticsearch/mapping-reference/mapping-index-field)`_index`       | [keyword](https://www.elastic.co/docs/reference/elasticsearch/mapping-reference/keyword)keyword | Index name.                                                                                                                                                                                                                  |
| `_index_mode`                                                                                                       | [keyword](https://www.elastic.co/docs/reference/elasticsearch/mapping-reference/keyword)keyword | [Index mode](/docs/reference/elasticsearch/index-settings/index-modules#index-mode-setting)Index mode. For example: `standard`, `lookup`, or `logsdb`.                                                                       |
| `_score`                                                                                                            | [`float`](https://www.elastic.co/docs/reference/elasticsearch/mapping-reference/number)`float`  | Query relevance score (when enabled). Scores are updated when using [full text search functions](https://www.elastic.co/docs/reference/query-languages/esql/functions-operators/search-functions)full text search functions. |
| [`_source`](https://www.elastic.co/docs/reference/elasticsearch/mapping-reference/mapping-source-field)`_source`    | Special `_source` type                                                                          | Original JSON document body passed at index time (or a reconstructed version if [synthetic `_source`](/docs/reference/elasticsearch/mapping-reference/mapping-source-field#synthetic-source)synthetic `_source` is enabled). |
| `_version`                                                                                                          | [`long`](https://www.elastic.co/docs/reference/elasticsearch/mapping-reference/number)`long`    | Document version number                                                                                                                                                                                                      |


## Usage and limitations

- Metadata fields are only available when the data source is an index
- The `_source` type is not supported by functions
- Only the `FROM` command supports the `METADATA` directive
- Once enabled, metadata fields work like regular index fields


## Examples


### Basic metadata usage

Once enabled, metadata fields are available to subsequent processing commands, just like other index fields:
```esql
FROM ul_logs, apps METADATA _index, _version
| WHERE id IN (13, 14) AND _version == 1
| EVAL key = CONCAT(_index, "_", TO_STR(id))
| SORT id, _index
| KEEP id, _index, _version, key
```


| id:long | _index:keyword | _version:long | key:keyword |
|---------|----------------|---------------|-------------|
| 13      | apps           | 1             | apps_13     |
| 13      | ul_logs        | 1             | ul_logs_13  |
| 14      | apps           | 1             | apps_14     |
| 14      | ul_logs        | 1             | ul_logs_14  |


### Metadata fields and aggregations

Similar to index fields, once an aggregation is performed, a metadata field will no longer be accessible to subsequent commands, unless used as a grouping field:
```esql
FROM employees METADATA _index, _id
| STATS max = MAX(emp_no) BY _index
```


| max:integer | _index:keyword |
|-------------|----------------|
| 10100       | employees      |


### Sort results by search score

```esql
FROM products METADATA _score
| WHERE MATCH(description, "wireless headphones")
| SORT _score DESC
| KEEP name, description, _score
```

<tip>
  Refer to [ES|QL for search](https://www.elastic.co/docs/solutions/search/esql-for-search#esql-for-search-scoring) for more information on relevance scoring and how to use `_score` in your queries.
</tip>
