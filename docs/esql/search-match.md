---
title: ES|QL Search functions
description: Use these functions for full-text search and semantic search. Full text functions can be used to match multivalued fields. A multivalued field that contains...
url: https://www.elastic.co/docs/reference/query-languages/esql/functions-operators/search-functions
---

# ES|QL Search functions

<tip>
  Get started with ES|QL for search use cases with
  our [hands-on tutorial](https://www.elastic.co/docs/reference/query-languages/esql/esql-search-tutorial).For a high-level overview of search functionalities in ES|QL, and to learn about relevance scoring, refer to [ES|QL for search](https://www.elastic.co/docs/solutions/search/esql-for-search#esql-for-search-scoring).For information regarding dense vector search functions,
  including [KNN](/docs/reference/query-languages/esql/functions-operators/dense-vector-functions#esql-knn), please refer to
  the [Dense vector functions](https://www.elastic.co/docs/reference/query-languages/esql/functions-operators/dense-vector-functions) documentation.
</tip>

Use these functions for [full-text search](https://www.elastic.co/docs/solutions/search/full-text)
and [semantic search](https://www.elastic.co/docs/solutions/search/semantic-search/semantic-search-semantic-text).
Full text functions can be used to
match [multivalued fields](https://www.elastic.co/docs/reference/query-languages/esql/esql-multivalued-fields).
A multivalued field that contains a value that matches a full text query is
considered to match the query.
Full text functions are significantly more performant for text search use cases
on large data sets than using pattern matching or regular expressions with
`LIKE` or `RLIKE`.
See [full text search limitations](/docs/reference/query-languages/esql/limitations#esql-limitations-full-text-search)
for information on the limitations of full text search.
ES|QL supports these full-text search functions:
- [`KQL`](#esql-kql)
- [`MATCH`](#esql-match)
- [`MATCH_PHRASE`](#esql-match_phrase)
- [`QSTR`](#esql-qstr)



## `MATCH`

```
stack: preview 9.0.0, ga 9.1.0
```

**Syntax**
![Embedded](https://www.elastic.co/docs/reference/query-languages/esql/images/functions/match.svg)

**Parameters**
<definitions>
  <definition term="field">
    Field that the query will target.
  </definition>
  <definition term="query">
    Value to find in the provided field.
  </definition>
  <definition term="options">
    (Optional) Match additional options as [function named parameters](/docs/reference/query-languages/esql/esql-syntax#esql-function-named-params).
  </definition>
</definitions>

**Description**
Use `MATCH` to perform a [match query](https://www.elastic.co/docs/reference/query-languages/query-dsl/query-dsl-match-query) on the specified field. Using `MATCH` is equivalent to using the `match` query in the Elasticsearch Query DSL.
Match can be used on fields from the text family like [text](https://www.elastic.co/docs/reference/elasticsearch/mapping-reference/text) and [semantic_text](https://www.elastic.co/docs/reference/elasticsearch/mapping-reference/semantic-text),
as well as other field types like keyword, boolean, dates, and numeric types.
When Match is used on a [semantic_text](https://www.elastic.co/docs/reference/elasticsearch/mapping-reference/semantic-text) field, it will perform a semantic query on the field.
Match can use [function named parameters](/docs/reference/query-languages/esql/esql-syntax#esql-function-named-params) to specify additional options
for the match query.
All [match query parameters](/docs/reference/query-languages/query-dsl/query-dsl-match-query#match-field-params) are supported.
For a simplified syntax, you can use the [match operator](/docs/reference/query-languages/esql/functions-operators/operators#esql-match-operator) `:` operator instead of `MATCH`.
`MATCH` returns true if the provided query matches the row.
**Supported types**

| field         | query         | options          | result  |
|---------------|---------------|------------------|---------|
| boolean       | boolean       | named parameters | boolean |
| boolean       | keyword       | named parameters | boolean |
| date          | date          | named parameters | boolean |
| date          | keyword       | named parameters | boolean |
| date_nanos    | date_nanos    | named parameters | boolean |
| date_nanos    | keyword       | named parameters | boolean |
| double        | double        | named parameters | boolean |
| double        | integer       | named parameters | boolean |
| double        | keyword       | named parameters | boolean |
| double        | long          | named parameters | boolean |
| integer       | double        | named parameters | boolean |
| integer       | integer       | named parameters | boolean |
| integer       | keyword       | named parameters | boolean |
| integer       | long          | named parameters | boolean |
| ip            | ip            | named parameters | boolean |
| ip            | keyword       | named parameters | boolean |
| keyword       | keyword       | named parameters | boolean |
| long          | double        | named parameters | boolean |
| long          | integer       | named parameters | boolean |
| long          | keyword       | named parameters | boolean |
| long          | long          | named parameters | boolean |
| text          | keyword       | named parameters | boolean |
| unsigned_long | double        | named parameters | boolean |
| unsigned_long | integer       | named parameters | boolean |
| unsigned_long | keyword       | named parameters | boolean |
| unsigned_long | long          | named parameters | boolean |
| unsigned_long | unsigned_long | named parameters | boolean |
| version       | keyword       | named parameters | boolean |
| version       | version       | named parameters | boolean |

**Supported function named parameters**
<definitions>
  <definition term="fuzziness">
    (keyword) Maximum edit distance allowed for matching.
  </definition>
  <definition term="auto_generate_synonyms_phrase_query">
    (boolean) If true, match phrase queries are automatically created for multi-term synonyms. Defaults to true.
  </definition>
  <definition term="analyzer">
    (keyword) Analyzer used to convert the text in the query value into token. Defaults to the index-time analyzer mapped for the field. If no analyzer is mapped, the index’s default analyzer is used.
  </definition>
  <definition term="minimum_should_match">
    (integer) Minimum number of clauses that must match for a document to be returned.
  </definition>
  <definition term="zero_terms_query">
    (keyword) Indicates whether all documents or none are returned if the analyzer removes all tokens, such as when using a stop filter. Defaults to none.
  </definition>
  <definition term="boost">
    (float) Floating point number used to decrease or increase the relevance scores of the query. Defaults to 1.0.
  </definition>
  <definition term="fuzzy_transpositions">
    (boolean) If true, edits for fuzzy matching include transpositions of two adjacent characters (ab → ba). Defaults to true.
  </definition>
  <definition term="fuzzy_rewrite">
    (keyword) Method used to rewrite the query. See the rewrite parameter for valid values and more information. If the fuzziness parameter is not 0, the match query uses a fuzzy_rewrite method of top_terms_blended_freqs_${max_expansions} by default.
  </definition>
  <definition term="prefix_length">
    (integer) Number of beginning characters left unchanged for fuzzy matching. Defaults to 0.
  </definition>
  <definition term="lenient">
    (boolean) If false, format-based errors, such as providing a text query value for a numeric field, are returned. Defaults to false.
  </definition>
  <definition term="operator">
    (keyword) Boolean logic used to interpret text in the query value. Defaults to OR.
  </definition>
  <definition term="max_expansions">
    (integer) Maximum number of terms to which the query will expand. Defaults to 50.
  </definition>
</definitions>

**Examples**
```esql
FROM books
| WHERE MATCH(author, "Faulkner")
```


| book_no:keyword | author:text                                        |
|-----------------|----------------------------------------------------|
| 2378            | [Carol Faulkner, Holly Byers Ochoa, Lucretia Mott] |
| 2713            | William Faulkner                                   |
| 2847            | Colleen Faulkner                                   |
| 2883            | William Faulkner                                   |
| 3293            | Danny Faulkner                                     |

```esql
FROM books
| WHERE MATCH(title, "Hobbit Back Again", {"operator": "AND"})
| KEEP title;
```


| title:text                         |
|------------------------------------|
| The Hobbit or There and Back Again |


## `MATCH_PHRASE`

```
stack: ga 9.1.0
```

**Syntax**
![Embedded](https://www.elastic.co/docs/reference/query-languages/esql/images/functions/match_phrase.svg)

**Parameters**
<definitions>
  <definition term="field">
    Field that the query will target.
  </definition>
  <definition term="query">
    Value to find in the provided field.
  </definition>
  <definition term="options">
    (Optional) MatchPhrase additional options as [function named parameters](/docs/reference/query-languages/esql/esql-syntax#esql-function-named-params). See [`match_phrase`](https://www.elastic.co/docs/reference/query-languages/query-dsl/query-dsl-match-query-phrase) for more information.
  </definition>
</definitions>

**Description**
Use `MATCH_PHRASE` to perform a [`match_phrase`](https://www.elastic.co/docs/reference/query-languages/query-dsl/query-dsl-match-query-phrase) on the specified field. Using `MATCH_PHRASE` is equivalent to using the `match_phrase` query in the Elasticsearch Query DSL.
MatchPhrase can be used on [text](https://www.elastic.co/docs/reference/elasticsearch/mapping-reference/text) fields, as well as other field types like keyword, boolean, or date types.
MatchPhrase is not supported for [semantic_text](https://www.elastic.co/docs/reference/elasticsearch/mapping-reference/semantic-text) or numeric types.
MatchPhrase can use [function named parameters](/docs/reference/query-languages/esql/esql-syntax#esql-function-named-params) to specify additional options for the
match_phrase query.
All [`match_phrase`](https://www.elastic.co/docs/reference/query-languages/query-dsl/query-dsl-match-query-phrase) query parameters are supported.
`MATCH_PHRASE` returns true if the provided query matches the row.
**Supported types**

| field   | query   | options          | result  |
|---------|---------|------------------|---------|
| keyword | keyword | named parameters | boolean |
| text    | keyword | named parameters | boolean |

**Supported function named parameters**
<definitions>
  <definition term="zero_terms_query">
    (keyword) Indicates whether all documents or none are returned if the analyzer removes all tokens, such as when using a stop filter. Defaults to none.
  </definition>
  <definition term="boost">
    (float) Floating point number used to decrease or increase the relevance scores of the query. Defaults to 1.0.
  </definition>
  <definition term="analyzer">
    (keyword) Analyzer used to convert the text in the query value into token. Defaults to the index-time analyzer mapped for the field. If no analyzer is mapped, the index’s default analyzer is used.
  </definition>
  <definition term="slop">
    (integer) Maximum number of positions allowed between matching tokens. Defaults to 0. Transposed terms have a slop of 2.
  </definition>
</definitions>

**Example**
```
stack: ga 9.1.0
```

```esql
FROM books
| WHERE MATCH_PHRASE(author, "William Faulkner")
```


| book_no:keyword | author:text      |
|-----------------|------------------|
| 2713            | William Faulkner |
| 2883            | William Faulkner |
| 4724            | William Faulkner |
| 4977            | William Faulkner |
| 5119            | William Faulkner |

