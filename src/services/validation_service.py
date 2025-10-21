"""
Validation Service for ES|QL Queries and Data
Ensures generated queries work with the sample data before demo
"""

import logging
import pandas as pd
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from elasticsearch import Elasticsearch
from dataclasses import dataclass
import json

logger = logging.getLogger(__name__)

@dataclass
class ValidationResult:
    """Result of a validation check"""
    query_id: str
    query_name: str
    status: str  # 'success', 'warning', 'error'
    message: str
    execution_time_ms: float
    result_count: int
    sample_results: Optional[List[Dict]] = None
    error_details: Optional[str] = None

@dataclass
class ValidationTask:
    """A validation task to track"""
    task_id: str
    task_type: str  # 'data_upload', 'index_creation', 'query_validation'
    description: str
    status: str  # 'pending', 'running', 'success', 'failed'
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    metadata: Optional[Dict] = None


class ValidationService:
    def __init__(self, es_client: Elasticsearch):
        self.es_client = es_client
        self.validation_tasks: List[ValidationTask] = []
        self.validation_results: List[ValidationResult] = []

    def create_task(self, task_type: str, description: str) -> ValidationTask:
        """Create a new validation task"""
        task = ValidationTask(
            task_id=f"{task_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            task_type=task_type,
            description=description,
            status='pending'
        )
        self.validation_tasks.append(task)
        return task

    def update_task(self, task_id: str, status: str, error_message: Optional[str] = None):
        """Update task status"""
        for task in self.validation_tasks:
            if task.task_id == task_id:
                task.status = status
                if status == 'running':
                    task.started_at = datetime.now()
                elif status in ['success', 'failed']:
                    task.completed_at = datetime.now()
                    if error_message:
                        task.error_message = error_message
                break

    def validate_data_upload(self, index_name: str, data_df: pd.DataFrame) -> ValidationTask:
        """Validate that data can be uploaded to Elasticsearch"""
        task = self.create_task('data_upload', f"Uploading data to index: {index_name}")
        self.update_task(task.task_id, 'running')

        try:
            # Check if index exists
            if not self.es_client.indices.exists(index=index_name):
                # Create index with appropriate mappings
                self._create_index_mapping(index_name, data_df)

            # Upload data in batches
            batch_size = 1000
            total_docs = 0

            for i in range(0, len(data_df), batch_size):
                batch = data_df.iloc[i:i+batch_size]
                actions = []

                for _, row in batch.iterrows():
                    actions.append({
                        "index": {
                            "_index": index_name,
                            "_id": row.get('id', None)
                        }
                    })
                    actions.append(row.to_dict())

                response = self.es_client.bulk(body=actions, refresh=True)
                if response['errors']:
                    raise Exception(f"Bulk upload errors: {response['errors']}")

                total_docs += len(batch)

            self.update_task(task.task_id, 'success')
            task.metadata = {'documents_uploaded': total_docs}
            logger.info(f"Successfully uploaded {total_docs} documents to {index_name}")

        except Exception as e:
            logger.error(f"Failed to upload data: {str(e)}")
            self.update_task(task.task_id, 'failed', str(e))

        return task

    def validate_esql_query(self, query: Dict) -> ValidationResult:
        """Validate a single ES|QL query"""
        query_id = query.get('id', 'unknown')
        query_name = query.get('name', 'Unnamed Query')
        esql = query.get('esql', '')

        logger.info(f"Validating query: {query_name}")

        try:
            # Execute the ES|QL query
            start_time = datetime.now()
            response = self.es_client.esql.query(
                body={"query": esql}
            )
            execution_time = (datetime.now() - start_time).total_seconds() * 1000

            # Process results
            columns = response.get('columns', [])
            values = response.get('values', [])

            # Convert to list of dicts for easier processing
            results = []
            for row in values[:5]:  # Get first 5 rows as sample
                results.append({
                    columns[i]['name']: row[i]
                    for i in range(len(columns))
                })

            result = ValidationResult(
                query_id=query_id,
                query_name=query_name,
                status='success',
                message=f"Query executed successfully in {execution_time:.2f}ms",
                execution_time_ms=execution_time,
                result_count=len(values),
                sample_results=results
            )

            # Check for warnings
            if len(values) == 0:
                result.status = 'warning'
                result.message = "Query returned no results - verify data matches query conditions"
            elif len(values) > 10000:
                result.status = 'warning'
                result.message = f"Query returned {len(values)} results - consider adding LIMIT"

        except Exception as e:
            logger.error(f"Query validation failed: {str(e)}")
            result = ValidationResult(
                query_id=query_id,
                query_name=query_name,
                status='error',
                message=f"Query failed: {str(e)[:200]}",
                execution_time_ms=0,
                result_count=0,
                error_details=str(e)
            )

        self.validation_results.append(result)
        return result

    def validate_all_queries(self, queries: List[Dict]) -> Tuple[List[ValidationResult], Dict]:
        """Validate all queries and return results with summary"""
        task = self.create_task('query_validation', f"Validating {len(queries)} ES|QL queries")
        self.update_task(task.task_id, 'running')

        results = []
        for i, query in enumerate(queries):
            # Update task metadata to show progress
            task.metadata = {'current': i+1, 'total': len(queries)}
            result = self.validate_esql_query(query)
            results.append(result)

        # Generate summary
        summary = {
            'total': len(results),
            'success': sum(1 for r in results if r.status == 'success'),
            'warnings': sum(1 for r in results if r.status == 'warning'),
            'errors': sum(1 for r in results if r.status == 'error'),
            'avg_execution_time_ms': sum(r.execution_time_ms for r in results) / len(results) if results else 0
        }

        if summary['errors'] > 0:
            self.update_task(task.task_id, 'failed',
                           f"{summary['errors']} queries failed validation")
        else:
            self.update_task(task.task_id, 'success')

        return results, summary

    def validate_data_relationships(self, datasets: Dict[str, pd.DataFrame]) -> List[ValidationTask]:
        """Validate relationships between datasets"""
        tasks = []

        # Check for common join keys
        task = self.create_task('relationship_check', 'Validating dataset relationships')
        self.update_task(task.task_id, 'running')

        try:
            relationship_issues = []

            # Example: Check if Asset ID exists in all required datasets
            if 'brand_assets' in datasets and 'campaign_performance' in datasets:
                assets_ids = set(datasets['brand_assets']['Asset ID'].unique())
                campaign_asset_ids = set(datasets['campaign_performance']['Asset ID'].unique())

                missing_in_assets = campaign_asset_ids - assets_ids
                if missing_in_assets:
                    relationship_issues.append(
                        f"Found {len(missing_in_assets)} Asset IDs in campaign_performance not in brand_assets"
                    )

            if relationship_issues:
                self.update_task(task.task_id, 'warning',
                               f"Found issues: {'; '.join(relationship_issues)}")
            else:
                self.update_task(task.task_id, 'success')

        except Exception as e:
            self.update_task(task.task_id, 'failed', str(e))

        tasks.append(task)
        return tasks

    def _create_index_mapping(self, index_name: str, data_df: pd.DataFrame):
        """Create Elasticsearch index with appropriate mappings based on DataFrame"""
        # Infer mappings from DataFrame dtypes
        properties = {}

        for col in data_df.columns:
            dtype = str(data_df[col].dtype)

            if 'datetime' in dtype or 'date' in col.lower():
                properties[col] = {"type": "date"}
            elif 'int' in dtype:
                properties[col] = {"type": "long"}
            elif 'float' in dtype:
                properties[col] = {"type": "double"}
            elif col.lower().endswith('_id') or col.lower() == 'id':
                properties[col] = {"type": "keyword"}
            else:
                # Default to keyword for categorical data
                if data_df[col].nunique() < len(data_df) * 0.5:
                    properties[col] = {"type": "keyword"}
                else:
                    properties[col] = {"type": "text"}

        # Special handling for lookup indices
        settings = {}
        if 'asset' in index_name.lower() and 'brand' in index_name.lower():
            settings["index.mode"] = "lookup"

        mapping = {
            "settings": settings,
            "mappings": {
                "properties": properties
            }
        }

        self.es_client.indices.create(index=index_name, body=mapping)
        logger.info(f"Created index {index_name} with mapping")

    def get_validation_summary(self) -> Dict:
        """Get overall validation summary"""
        return {
            'tasks': [
                {
                    'id': t.task_id,
                    'type': t.task_type,
                    'description': t.description,
                    'status': t.status,
                    'started_at': t.started_at.isoformat() if t.started_at else None,
                    'completed_at': t.completed_at.isoformat() if t.completed_at else None,
                    'error': t.error_message,
                    'metadata': t.metadata
                }
                for t in self.validation_tasks
            ],
            'query_results': [
                {
                    'query_name': r.query_name,
                    'status': r.status,
                    'message': r.message,
                    'execution_time_ms': r.execution_time_ms,
                    'result_count': r.result_count
                }
                for r in self.validation_results
            ],
            'overall_status': self._calculate_overall_status()
        }

    def _calculate_overall_status(self) -> str:
        """Calculate overall validation status"""
        if any(t.status == 'failed' for t in self.validation_tasks):
            return 'failed'
        if any(t.status == 'running' for t in self.validation_tasks):
            return 'running'
        if any(t.status == 'pending' for t in self.validation_tasks):
            return 'pending'
        if any(r.status == 'error' for r in self.validation_results):
            return 'failed'
        if any(r.status == 'warning' for r in self.validation_results):
            return 'warning'
        return 'success'

    def export_validation_report(self) -> str:
        """Export validation report as markdown"""
        report = "# Validation Report\n\n"
        report += f"Generated: {datetime.now().isoformat()}\n\n"

        # Task summary
        report += "## Task Summary\n\n"
        for task in self.validation_tasks:
            status_icon = "✅" if task.status == "success" else "❌" if task.status == "failed" else "⚠️"
            report += f"- {status_icon} **{task.description}**: {task.status}\n"
            if task.error_message:
                report += f"  - Error: {task.error_message}\n"

        # Query validation results
        report += "\n## Query Validation Results\n\n"
        for result in self.validation_results:
            status_icon = "✅" if result.status == "success" else "❌" if result.status == "error" else "⚠️"
            report += f"### {status_icon} {result.query_name}\n"
            report += f"- Status: {result.status}\n"
            report += f"- Message: {result.message}\n"
            report += f"- Execution Time: {result.execution_time_ms:.2f}ms\n"
            report += f"- Result Count: {result.result_count}\n\n"

        return report