"""
Data Generator Service
Creates synthetic datasets for demos
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import logging
from typing import Dict, List
from faker import Faker

logger = logging.getLogger(__name__)
fake = Faker()


class DataGenerator:
    """Generate synthetic datasets for demos"""

    def __init__(self):
        self.fake = Faker()
        Faker.seed(42)  # For reproducibility
        random.seed(42)
        np.random.seed(42)

    def generate_datasets(self, scenario: Dict) -> Dict[str, pd.DataFrame]:
        """
        Generate all datasets for a scenario

        Args:
            scenario: Scenario configuration

        Returns:
            Dictionary of dataset name to DataFrame
        """
        logger.info(f"Generating datasets for scenario: {scenario.get('name', 'Unknown')}")

        datasets = {}

        for dataset_config in scenario.get("datasets", []):
            dataset_name = dataset_config["name"]
            dataset_type = dataset_config.get("type", "reference")
            num_records = dataset_config.get("records", 1000)

            logger.info(f"Generating {dataset_name}: {num_records} records of type {dataset_type}")

            if dataset_type == "reference":
                df = self._generate_reference_data(dataset_name, num_records)
            elif dataset_type == "events":
                df = self._generate_event_data(dataset_name, num_records)
            elif dataset_type == "metrics":
                df = self._generate_metrics_data(dataset_name, num_records)
            elif dataset_type == "time_series":
                df = self._generate_timeseries_data(dataset_name, num_records)
            else:
                df = self._generate_generic_data(dataset_name, num_records)

            datasets[dataset_name] = df

        # Add relationships between datasets
        datasets = self._add_relationships(datasets, scenario.get("relationships", []))

        logger.info(f"Generated {len(datasets)} datasets")
        return datasets

    def _generate_reference_data(self, name: str, num_records: int) -> pd.DataFrame:
        """Generate reference/lookup data"""
        data = {
            "id": [f"{name[:3].upper()}-{i:04d}" for i in range(1, num_records + 1)],
            "name": [self.fake.company() for _ in range(num_records)],
            "type": [random.choice(["Type A", "Type B", "Type C", "Type D"]) for _ in range(num_records)],
            "status": [random.choice(["Active", "Inactive", "Pending"]) for _ in range(num_records)],
            "region": [random.choice(["North America", "Europe", "APAC", "LATAM"]) for _ in range(num_records)],
            "created_date": [
                self.fake.date_between(start_date="-2y", end_date="today")
                for _ in range(num_records)
            ],
            "value": np.random.uniform(100, 10000, num_records).round(2)
        }
        return pd.DataFrame(data)

    def _generate_event_data(self, name: str, num_records: int) -> pd.DataFrame:
        """Generate event data"""
        # Generate timestamps over the last 30 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)

        timestamps = pd.date_range(start=start_date, end=end_date, periods=num_records)
        timestamps = timestamps + pd.to_timedelta(np.random.randint(-3600, 3600, size=num_records), unit='s')

        data = {
            "event_id": [f"EVT-{i:06d}" for i in range(1, num_records + 1)],
            "timestamp": timestamps,
            "event_type": [
                random.choice(["create", "update", "delete", "view", "process"])
                for _ in range(num_records)
            ],
            "user_id": [f"USR-{random.randint(1, 100):03d}" for _ in range(num_records)],
            "entity_id": [f"ENT-{random.randint(1, 1000):04d}" for _ in range(num_records)],
            "status": [random.choice(["success", "failure", "pending"]) for _ in range(num_records)],
            "duration_ms": np.random.exponential(500, num_records).round(0),
            "metadata": [{"source": random.choice(["web", "api", "mobile"])} for _ in range(num_records)]
        }
        return pd.DataFrame(data)

    def _generate_metrics_data(self, name: str, num_records: int) -> pd.DataFrame:
        """Generate metrics data"""
        # Generate hourly metrics for the last N hours
        hours = min(num_records, 720)  # Max 30 days of hourly data
        timestamps = pd.date_range(end=datetime.now(), periods=hours, freq='H')

        if len(timestamps) < num_records:
            # If we need more records, duplicate with different entities
            timestamps = np.tile(timestamps, (num_records // hours + 1))[:num_records]
            entity_ids = [f"ENT-{i % 100:03d}" for i in range(num_records)]
        else:
            entity_ids = ["ENT-001"] * num_records

        data = {
            "timestamp": timestamps[:num_records],
            "entity_id": entity_ids,
            "cpu_usage": np.random.uniform(10, 90, num_records).round(2),
            "memory_usage": np.random.uniform(20, 80, num_records).round(2),
            "request_count": np.random.poisson(100, num_records),
            "error_count": np.random.poisson(5, num_records),
            "response_time_ms": np.random.gamma(2, 50, num_records).round(2),
            "throughput": np.random.uniform(100, 1000, num_records).round(2)
        }
        return pd.DataFrame(data)

    def _generate_timeseries_data(self, name: str, num_records: int) -> pd.DataFrame:
        """Generate time series data"""
        # Create realistic time series with trends and seasonality
        timestamps = pd.date_range(end=datetime.now(), periods=num_records, freq='5min')

        # Base trend
        trend = np.linspace(100, 150, num_records)

        # Add daily seasonality
        daily_pattern = 20 * np.sin(2 * np.pi * np.arange(num_records) / (288))  # 288 = 5-min periods in a day

        # Add noise
        noise = np.random.normal(0, 5, num_records)

        # Combine
        values = trend + daily_pattern + noise

        data = {
            "timestamp": timestamps,
            "value": values.round(2),
            "metric_name": [name] * num_records,
            "host": [f"host-{i % 10:02d}" for i in range(num_records)],
            "environment": [random.choice(["prod", "staging", "dev"]) for _ in range(num_records)]
        }
        return pd.DataFrame(data)

    def _generate_generic_data(self, name: str, num_records: int) -> pd.DataFrame:
        """Generate generic data when type is not specified"""
        data = {
            "id": range(1, num_records + 1),
            "name": [f"{name}_{i}" for i in range(num_records)],
            "value": np.random.uniform(0, 100, num_records).round(2),
            "category": [random.choice(["A", "B", "C"]) for _ in range(num_records)],
            "created_at": pd.date_range(end=datetime.now(), periods=num_records, freq='H')
        }
        return pd.DataFrame(data)

    def _add_relationships(self, datasets: Dict[str, pd.DataFrame], relationships: List[str]) -> Dict[str, pd.DataFrame]:
        """Add foreign key relationships between datasets"""
        for relationship in relationships:
            if "->" in relationship:
                source, target = relationship.split("->")
                source = source.strip()
                target = target.strip()

                if source in datasets and target in datasets:
                    # Add foreign keys
                    source_df = datasets[source]
                    target_df = datasets[target]

                    # Use the source ID in target dataset
                    if "id" in source_df.columns and len(target_df) > 0:
                        # Add foreign key column to target
                        target_df[f"{source}_id"] = [
                            random.choice(source_df["id"].values)
                            for _ in range(len(target_df))
                        ]
                        datasets[target] = target_df

                        logger.info(f"Added relationship: {source} -> {target}")

        return datasets

    def export_datasets(self, datasets: Dict[str, pd.DataFrame], output_dir: str = "data") -> Dict[str, str]:
        """
        Export datasets to CSV files

        Args:
            datasets: Dictionary of DataFrames
            output_dir: Output directory

        Returns:
            Dictionary of dataset name to file path
        """
        import os
        os.makedirs(output_dir, exist_ok=True)

        file_paths = {}

        for name, df in datasets.items():
            file_path = os.path.join(output_dir, f"{name}.csv")
            df.to_csv(file_path, index=False)
            file_paths[name] = file_path
            logger.info(f"Exported {name} to {file_path}")

        return file_paths