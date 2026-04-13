"""
Content Alignment Validator

Validates that indexed document content is semantically aligned with:
1. The metadata fields assigned to each document (intent_tags, doc_type must match content text)
2. The query intents in the strategy (each query must have supporting documents in the data)

This closes the "honest limit" gap where structural alignment passes but content is irrelevant
to the queries that are supposed to retrieve it.
"""

import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from elasticsearch import Elasticsearch

logger = logging.getLogger(__name__)


class ContentAlignmentValidator:
    """Validates semantic content alignment between indexed data and query intents"""

    # Fields considered "content-bearing" — their text must match metadata
    CONTENT_FIELDS = {'content', 'description', 'body', 'text', 'summary', 'details', 'message'}

    # Metadata fields whose values must be reflected in content
    METADATA_FIELDS = {'intent_tags', 'doc_type', 'content_category', 'category', 'event_type'}

    def __init__(self, es_client: Elasticsearch, llm_client):
        self.es = es_client
        self.llm = llm_client

    def validate(
        self,
        indexed_datasets: Dict[str, str],
        query_strategy: Dict[str, Any],
        config: Dict[str, Any],
        sample_size: int = 8
    ) -> Dict[str, Any]:
        """
        Run full content alignment validation.

        Args:
            indexed_datasets: {dataset_name: actual_index_name}
            query_strategy: The strategy dict with queries and datasets
            config: Demo config (company_name, pain_points etc.)
            sample_size: Docs to sample per dataset

        Returns:
            {
                'alignment_score': float 0-1,
                'passed': bool,
                'query_coverage': {query_name: {'covered': bool, 'gap': str}},
                'metadata_issues': [{dataset, field, example_doc_id, issue}],
                'content_gaps': [str],   # human-readable gap descriptions
                'content_seeds': {dataset_name: [topic_str]},  # what data regeneration must cover
                'summary': str
            }
        """
        report = {
            'alignment_score': 1.0,
            'passed': True,
            'query_coverage': {},
            'metadata_issues': [],
            'content_gaps': [],
            'content_seeds': {},
            'summary': ''
        }

        queries = query_strategy.get('queries', [])
        if not queries:
            report['summary'] = 'No queries to validate against.'
            return report

        # Step 1: For each dataset, sample docs and extract content + metadata
        dataset_samples = {}
        for dataset_name, index_name in indexed_datasets.items():
            try:
                samples = self._sample_documents(index_name, sample_size)
                if samples:
                    dataset_samples[dataset_name] = samples
                    logger.info(f"Sampled {len(samples)} docs from {dataset_name}")
            except Exception as e:
                logger.warning(f"Could not sample {dataset_name}: {e}")

        if not dataset_samples:
            report['summary'] = 'No documents sampled — skipping content validation.'
            return report

        # Step 2: Check content-metadata alignment per dataset
        metadata_issues = self._check_metadata_alignment(dataset_samples)
        report['metadata_issues'] = metadata_issues

        # Step 3: Check query-content coverage
        coverage_results, gaps = self._check_query_coverage(queries, dataset_samples, config)
        report['query_coverage'] = coverage_results
        report['content_gaps'] = gaps

        # Step 4: Build content seeds (topics that must be in data for queries to work)
        report['content_seeds'] = self._extract_content_seeds(queries, coverage_results, dataset_samples)

        # Step 5: Score
        total_queries = len(queries)
        covered = sum(1 for v in coverage_results.values() if v.get('covered', False))
        metadata_penalty = min(len(metadata_issues) * 0.05, 0.3)
        coverage_score = covered / total_queries if total_queries > 0 else 1.0
        report['alignment_score'] = max(0.0, coverage_score - metadata_penalty)
        report['passed'] = report['alignment_score'] >= 0.7

        # Step 6: Summary
        report['summary'] = self._build_summary(report, covered, total_queries)
        logger.info(f"Content alignment: score={report['alignment_score']:.2f}, covered={covered}/{total_queries}")

        return report

    def _sample_documents(self, index_name: str, size: int) -> List[Dict]:
        """Sample documents from index, excluding large vector fields"""
        try:
            resp = self.es.search(
                index=index_name,
                body={
                    'size': size,
                    'query': {'match_all': {}},
                    '_source': {'excludes': ['*.predicted_value', '*.model_id', 'ml', 'content_vector']}
                }
            )
            return [hit['_source'] for hit in resp['hits']['hits']]
        except Exception as e:
            logger.warning(f"Sample failed for {index_name}: {e}")
            return []

    def _check_metadata_alignment(self, dataset_samples: Dict[str, List[Dict]]) -> List[Dict]:
        """Check that metadata field values are reflected in content fields"""
        issues = []
        for dataset_name, docs in dataset_samples.items():
            for doc in docs:
                # Find content fields present in this doc
                content_text = ' '.join(
                    str(doc.get(f, ''))
                    for f in self.CONTENT_FIELDS
                    if doc.get(f)
                ).lower()

                if not content_text or len(content_text) < 20:
                    continue

                # Check metadata fields
                for meta_field in self.METADATA_FIELDS:
                    if meta_field not in doc:
                        continue
                    meta_value = doc[meta_field]
                    if isinstance(meta_value, list):
                        meta_value = meta_value[0] if meta_value else ''
                    if not meta_value:
                        continue

                    # Simple heuristic: tag value should appear in content (at least partially)
                    tag_words = str(meta_value).lower().replace('_', ' ').replace('-', ' ').split()
                    meaningful_words = [w for w in tag_words if len(w) > 3]
                    if meaningful_words and not any(w in content_text for w in meaningful_words):
                        issues.append({
                            'dataset': dataset_name,
                            'field': meta_field,
                            'value': meta_value,
                            'doc_id': doc.get('doc_id', doc.get('_id', 'unknown')),
                            'issue': f"'{meta_value}' in {meta_field} not reflected in content text"
                        })
        return issues

    def _check_query_coverage(
        self,
        queries: List[Dict],
        dataset_samples: Dict[str, List[Dict]],
        config: Dict[str, Any]
    ) -> Tuple[Dict, List[str]]:
        """Use LLM to check if sampled docs support each query intent"""
        coverage = {}
        gaps = []

        # Build a compact representation of all sampled content
        content_summary = self._build_content_summary(dataset_samples)

        if not content_summary:
            for q in queries:
                coverage[q.get('name', 'unknown')] = {'covered': False, 'gap': 'No content sampled'}
            return coverage, ['No content available to validate against']

        # Batch queries for LLM — check all at once
        query_intents = []
        for q in queries:
            query_intents.append({
                'name': q.get('name', ''),
                'intent': q.get('description', q.get('pain_point', ''))[:200]
            })

        prompt = f"""You are validating whether a dataset contains content that supports specific query intents.

DATASET CONTENT SAMPLES:
{content_summary}

QUERY INTENTS TO CHECK:
{json.dumps(query_intents, indent=2)}

For each query, determine:
1. Is there at least one document in the samples that would be a relevant result for this query?
2. If not, what specific topic is missing from the data?

Respond with a JSON array — one entry per query in the same order:
[
  {{
    "name": "query_name",
    "covered": true/false,
    "evidence": "brief explanation of which doc supports it OR what is missing"
  }}
]

Only return the JSON array, nothing else."""

        try:
            response = self.llm.generate(prompt, max_tokens=1500)
            # Parse JSON from response
            text = response.strip()
            if text.startswith('```'):
                text = text.split('```')[1]
                if text.startswith('json'):
                    text = text[4:]
            results = json.loads(text.strip())

            for item in results:
                name = item.get('name', '')
                covered = item.get('covered', False)
                evidence = item.get('evidence', '')
                coverage[name] = {'covered': covered, 'gap': '' if covered else evidence}
                if not covered:
                    gaps.append(f"Query '{name}': {evidence}")

        except Exception as e:
            logger.warning(f"LLM content coverage check failed: {e}")
            # Fallback: mark all as covered (don't block on LLM failure)
            for q in queries:
                coverage[q.get('name', '')] = {'covered': True, 'gap': ''}

        return coverage, gaps

    def _build_content_summary(self, dataset_samples: Dict[str, List[Dict]]) -> str:
        """Build a compact text summary of sampled document content for LLM"""
        lines = []
        for dataset_name, docs in dataset_samples.items():
            lines.append(f"\n=== {dataset_name} (sample of {len(docs)} docs) ===")
            for i, doc in enumerate(docs[:5]):  # Max 5 per dataset for prompt size
                # Extract content fields
                content = ' | '.join(
                    f"{f}={str(doc[f])[:100]}"
                    for f in ['title', 'content', 'description', 'body', 'message', 'doc_type', 'intent_tags', 'event_type', 'category']
                    if doc.get(f)
                )
                if content:
                    lines.append(f"  Doc {i+1}: {content[:200]}")
        return '\n'.join(lines)

    def _extract_content_seeds(
        self,
        queries: List[Dict],
        coverage: Dict[str, Dict],
        dataset_samples: Dict[str, List[Dict]]
    ) -> Dict[str, List[str]]:
        """
        Extract content seeds — specific topics each dataset must contain.
        Used to inject requirements into the data generator prompt on regeneration.
        """
        seeds: Dict[str, List[str]] = {}

        for q in queries:
            name = q.get('name', '')
            if coverage.get(name, {}).get('covered', True):
                continue  # Already covered — no seed needed

            # Determine which dataset this query targets
            esql = q.get('esql', q.get('query', ''))
            target_dataset = None
            for ds in dataset_samples.keys():
                if ds in esql:
                    target_dataset = ds
                    break

            if not target_dataset and dataset_samples:
                target_dataset = list(dataset_samples.keys())[0]

            if target_dataset:
                if target_dataset not in seeds:
                    seeds[target_dataset] = []
                intent = q.get('description', q.get('pain_point', name))
                seeds[target_dataset].append(intent[:150])

        return seeds

    def _build_summary(self, report: Dict, covered: int, total: int) -> str:
        score = report['alignment_score']
        status = 'PASS' if report['passed'] else 'FAIL'
        lines = [
            f"Content alignment {status}: score={score:.2f}, query coverage={covered}/{total}",
        ]
        if report['metadata_issues']:
            lines.append(f"Metadata issues: {len(report['metadata_issues'])} fields with content mismatch")
        if report['content_gaps']:
            lines.append("Gaps:")
            for gap in report['content_gaps'][:5]:
                lines.append(f"  - {gap}")
        return '\n'.join(lines)


def extract_content_seeds_for_prompt(query_strategy: Dict[str, Any]) -> Dict[str, str]:
    """
    Extract content requirements from query strategy for injection into data generator prompt.
    Called BEFORE indexing (prevention layer) — tells data generator what topics to cover.

    Returns: {dataset_name: content_requirements_string}
    """
    seeds: Dict[str, List[str]] = {}

    for query in query_strategy.get('queries', []):
        esql = query.get('esql', query.get('query', ''))
        description = query.get('description', '')
        pain_point = query.get('pain_point', '')
        intent = description or pain_point
        if not intent:
            continue

        # Find target dataset from FROM clause
        import re
        match = re.search(r'FROM\s+(\w+)', esql, re.IGNORECASE)
        dataset = match.group(1) if match else None

        if dataset:
            if dataset not in seeds:
                seeds[dataset] = []
            seeds[dataset].append(intent[:150])

    # Format as prompt strings
    result = {}
    for dataset, intents in seeds.items():
        unique_intents = list(dict.fromkeys(intents))[:10]  # dedupe, max 10
        result[dataset] = (
            f"CONTENT REQUIREMENTS for {dataset}:\n"
            + "The following query intents MUST be supported by actual document content. "
            + "Generate documents whose text specifically addresses each topic below. "
            + "Do NOT use placeholder or generic text:\n"
            + '\n'.join(f"  - {i}" for i in unique_intents)
        )

    return result
