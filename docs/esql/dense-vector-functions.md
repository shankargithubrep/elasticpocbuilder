---
title: ES|QL dense vector functions
description: ES|QL supports dense vector functions for vector similarity calculations and k-nearest neighbor search. Dsense vector functions work with  dense_vector...
url: https://www.elastic.co/docs/reference/query-languages/esql/functions-operators/dense-vector-functions
---

# ES|QL dense vector functions

ES|QL supports dense vector functions for vector similarity calculations and
k-nearest neighbor search.
Dsense vector functions work with [
`dense_vector` fields](https://www.elastic.co/docs/reference/elasticsearch/mapping-reference/dense-vector)
and require appropriate field mappings.
ES|QL supports these vector functions:
- [`KNN`](#esql-knn) `stack: preview 9.2` `serverless: preview`
- [`TEXT_EMBEDDING`](#esql-text_embedding) `stack: preview 9.3` `serverless: preview`


## `KNN`

```
stack: preview 9.2.0
serverless: preview
```

**Syntax**
![Embedded](https://www.elastic.co/docs/reference/query-languages/esql/images/functions/knn.svg)

**Parameters**
<definitions>
  <definition term="field">
    Field that the query will target. knn function can be used with dense_vector or semantic_text fields. Other text fields are not allowed
  </definition>
  <definition term="query">
    Vector value to find top nearest neighbours for.
  </definition>
  <definition term="options">
    (Optional) kNN additional options as [function named parameters](/docs/reference/query-languages/esql/esql-syntax#esql-function-named-params). See [knn query](https://www.elastic.co/docs/reference/query-languages/query-dsl/query-dsl-knn-query) for more information.
  </definition>
</definitions>

**Description**
Finds the k nearest vectors to a query vector, as measured by a similarity metric. knn function finds nearest vectors through approximate search on indexed dense_vectors or semantic_text fields.
**Supported types**

| field        | query        | options          | result  |
|--------------|--------------|------------------|---------|
| dense_vector | dense_vector | named parameters | boolean |
| text         | dense_vector | named parameters | boolean |

**Supported function named parameters**
<definitions>
  <definition term="boost">
    (float) Floating point number used to decrease or increase the relevance scores of the query.Defaults to 1.0.
  </definition>
  <definition term="min_candidates">
    (integer) The minimum number of nearest neighbor candidates to consider per shard while doing knn search.  KNN may use a higher number of candidates in case the query can't use a approximate results. Cannot exceed 10,000. Increasing min_candidates tends to improve the accuracy of the final results. Defaults to 1.5 * LIMIT used for the query.
  </definition>
  <definition term="rescore_oversample">
    (double) Applies the specified oversampling for rescoring quantized vectors. See [oversampling and rescoring quantized vectors](https://www.elastic.co/docs/solutions/search/vector/knn#dense-vector-knn-search-rescoring) for details.
  </definition>
  <definition term="similarity">
    (double) The minimum similarity required for a document to be considered a match. The similarity value calculated relates to the raw similarity used, not the document score.
  </definition>
</definitions>

**Example**
```esql
from colors metadata _score
| where knn(rgb_vector, [0, 120, 0])
| sort _score desc, color asc
```


| color:text | rgb_vector:dense_vector |
|------------|-------------------------|
| green      | [0.0, 128.0, 0.0]       |
| black      | [0.0, 0.0, 0.0]         |
| olive      | [128.0, 128.0, 0.0]     |
| teal       | [0.0, 128.0, 128.0]     |
| lime       | [0.0, 255.0, 0.0]       |
| sienna     | [160.0, 82.0, 45.0]     |
| maroon     | [128.0, 0.0, 0.0]       |
| navy       | [0.0, 0.0, 128.0]       |
| gray       | [128.0, 128.0, 128.0]   |
| chartreuse | [127.0, 255.0, 0.0]     |


## `TEXT_EMBEDDING`

```
stack: preview 9.3
serverless: preview
```

**Syntax**
![Embedded](https://www.elastic.co/docs/reference/query-languages/esql/images/functions/text_embedding.svg)

**Parameters**
<definitions>
  <definition term="text">
    Text string to generate embeddings from. Must be a non-null literal string value.
  </definition>
  <definition term="inference_id">
    Identifier of an existing inference endpoint the that will generate the embeddings. The inference endpoint must have the `text_embedding` task type and should use the same model that was used to embed your indexed data.
  </definition>
</definitions>

**Description**
Generates dense vector embeddings from text input using a specified [inference endpoint](https://www.elastic.co/docs/explore-analyze/elastic-inference/inference-api). Use this function to generate query vectors for KNN searches against your vectorized data or others dense vector based operations.
**Supported types**

| text    | inference_id | result       |
|---------|--------------|--------------|
| keyword | keyword      | dense_vector |

**Examples**
Basic text embedding generation from a text string using an inference endpoint.
```esql
ROW input="Who is Victor Hugo?"
| EVAL embedding = TEXT_EMBEDDING("Who is Victor Hugo?", "test_dense_inference")
```

Generate text embeddings and store them in a variable for reuse in KNN vector search queries.
```esql
FROM semantic_text METADATA _score
| EVAL query_embedding = TEXT_EMBEDDING("be excellent to each other", "test_dense_inference")
| WHERE KNN(semantic_text_dense_field, query_embedding)
```

Directly embed text within a KNN query for streamlined vector search without intermediate variables.
```esql
FROM semantic_text METADATA _score
| WHERE KNN(semantic_text_dense_field, TEXT_EMBEDDING("be excellent to each other", "test_dense_inference"))
```
