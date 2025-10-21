"""
Enhanced Data Generator Service
Creates realistic synthetic data with relationships and A-ha moments
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
import json
import re
from faker import Faker
import logging

logger = logging.getLogger(__name__)


@dataclass
class DataGenerationPlan:
    """Plan for data generation"""
    datasets: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    relationships: List[Tuple[str, str, str]] = field(default_factory=list)
    total_records: int = 0
    aha_moments: List[Dict[str, Any]] = field(default_factory=list)


class EnhancedDataGenerator:
    """Enhanced data generator with realistic patterns and A-ha moments"""

    def __init__(self):
        """Initialize data generator"""
        self.fake = Faker()
        Faker.seed(None)  # Random seed by default

    def create_plan(self, context: Dict[str, Any]) -> DataGenerationPlan:
        """Create a data generation plan from context"""
        plan = DataGenerationPlan()

        # Parse scale
        scale = self._parse_scale(context.get("scale", "1000 records"))

        # Add industry-specific datasets
        industry = context.get("industry", "Generic")

        if industry == "Retail":
            plan.datasets = {
                "customers": {"type": "reference", "count": min(10000, scale // 10)},
                "products": {"type": "reference", "count": min(5000, scale // 20)},
                "transactions": {"type": "events", "count": scale},
                "inventory": {"type": "metrics", "count": scale // 2}
            }
            plan.relationships = [
                ("transactions", "customer_id", "customers"),
                ("transactions", "product_id", "products"),
                ("inventory", "product_id", "products")
            ]

        elif industry == "Healthcare":
            plan.datasets = {
                "patients": {"type": "reference", "count": min(10000, scale // 5)},
                "departments": {"type": "reference", "count": 50},
                "visits": {"type": "events", "count": scale},
                "vitals": {"type": "time_series", "count": scale * 2}
            }
            plan.relationships = [
                ("visits", "patient_id", "patients"),
                ("visits", "department_id", "departments"),
                ("vitals", "patient_id", "patients")
            ]

        elif industry == "Financial":
            plan.datasets = {
                "accounts": {"type": "reference", "count": min(5000, scale // 10)},
                "customers": {"type": "reference", "count": min(5000, scale // 10)},
                "transactions": {"type": "events", "count": scale},
                "risk_scores": {"type": "metrics", "count": scale // 5}
            }
            plan.relationships = [
                ("accounts", "customer_id", "customers"),
                ("transactions", "account_id", "accounts"),
                ("risk_scores", "account_id", "accounts")
            ]

        else:  # Generic
            plan.datasets = {
                "entities": {"type": "reference", "count": min(1000, scale // 10)},
                "events": {"type": "events", "count": scale},
                "metrics": {"type": "metrics", "count": scale // 2}
            }

        # Calculate total records
        plan.total_records = sum(ds["count"] for ds in plan.datasets.values())

        # Identify A-ha moments
        if context.get("pain_points"):
            plan.aha_moments = self.identify_aha_moments(context)

        return plan

    def _parse_scale(self, scale_str: str) -> int:
        """Parse scale string into record count"""
        if not scale_str:
            return 1000

        # Extract number
        match = re.search(r'(\d+\.?\d*)\s*([KMB]?)', scale_str, re.IGNORECASE)
        if not match:
            return 1000

        number = float(match.group(1))
        multiplier = match.group(2).upper() if match.group(2) else ''

        multipliers = {'K': 1000, 'M': 1000000, 'B': 1000000000}
        return int(number * multipliers.get(multiplier, 1))

    def generate_datasets(self, plan: DataGenerationPlan) -> Dict[str, pd.DataFrame]:
        """Generate all datasets according to plan"""
        datasets = {}

        for dataset_name, config in plan.datasets.items():
            if config["type"] == "reference":
                if "customer" in dataset_name:
                    datasets[dataset_name] = self.generate_customers(config["count"])
                elif "product" in dataset_name:
                    datasets[dataset_name] = self.generate_products(config["count"])
                elif "patient" in dataset_name:
                    datasets[dataset_name] = self.generate_patients(config["count"])
                else:
                    datasets[dataset_name] = self.generate_reference_data(
                        dataset_name, config["count"]
                    )

            elif config["type"] == "events":
                datasets[dataset_name] = self.generate_events(config["count"])

            elif config["type"] == "metrics":
                datasets[dataset_name] = self.generate_metrics(config["count"])

            elif config["type"] == "time_series":
                datasets[dataset_name] = self.generate_time_series(
                    metric=dataset_name, periods=config["count"]
                )

        return datasets

    def generate_customers(self, count: int, seed: Optional[int] = None) -> pd.DataFrame:
        """Generate customer reference data"""
        if seed is not None:
            np.random.seed(seed)
            Faker.seed(seed)

        fake = Faker() if seed is None else self.fake

        data = []
        for i in range(count):
            data.append({
                "customer_id": f"CUST-{i+1:06d}",
                "name": fake.company(),
                "segment": np.random.choice(["Enterprise", "SMB", "Startup"], p=[0.2, 0.5, 0.3]),
                "industry": np.random.choice(["Tech", "Retail", "Finance", "Healthcare", "Manufacturing"]),
                "created_date": fake.date_between(start_date="-5y", end_date="today"),
                "lifetime_value": np.random.lognormal(10, 2),
                "risk_score": np.random.beta(2, 5),  # Most customers low risk
                "country": fake.country(),
                "active": np.random.choice([True, False], p=[0.85, 0.15])
            })

        df = pd.DataFrame(data)
        df["created_date"] = pd.to_datetime(df["created_date"])
        return df

    def generate_products(self, count: int) -> pd.DataFrame:
        """Generate product reference data"""
        categories = ["Electronics", "Clothing", "Food", "Home", "Sports", "Books", "Toys"]

        data = []
        for i in range(count):
            category = np.random.choice(categories)
            data.append({
                "product_id": f"PROD-{i+1:06d}",
                "name": f"{self.fake.word().title()} {category} Item",
                "category": category,
                "price": np.random.lognormal(3, 1),
                "cost": np.random.lognormal(2.5, 1),
                "in_stock": np.random.choice([True, False], p=[0.9, 0.1])
            })

        return pd.DataFrame(data)

    def generate_patients(self, count: int) -> pd.DataFrame:
        """Generate patient reference data"""
        data = []
        for i in range(count):
            data.append({
                "patient_id": f"PAT-{i+1:06d}",
                "name": self.fake.name(),
                "age": np.random.normal(45, 20),
                "gender": np.random.choice(["M", "F", "Other"]),
                "risk_category": np.random.choice(["Low", "Medium", "High"], p=[0.6, 0.3, 0.1])
            })

        return pd.DataFrame(data)

    def generate_reference_data(self, name: str, count: int) -> pd.DataFrame:
        """Generate generic reference data"""
        data = []
        for i in range(count):
            data.append({
                f"{name}_id": f"{name.upper()}-{i+1:06d}",
                "name": self.fake.word().title(),
                "category": np.random.choice(["A", "B", "C"]),
                "value": np.random.random()
            })

        return pd.DataFrame(data)

    def generate_events(
        self,
        count: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> pd.DataFrame:
        """Generate event data"""
        if start_date is None:
            start_date = datetime.now() - timedelta(days=30)
        if end_date is None:
            end_date = datetime.now()

        timestamps = pd.date_range(start=start_date, end=end_date, periods=count)

        data = {
            "event_id": [f"EVT-{i+1:08d}" for i in range(count)],
            "timestamp": timestamps,
            "event_type": np.random.choice(
                ["click", "view", "purchase", "signup", "error"],
                size=count,
                p=[0.3, 0.4, 0.15, 0.1, 0.05]
            ),
            "value": np.random.exponential(100, count),
            "duration_ms": np.random.exponential(500, count)
        }

        return pd.DataFrame(data)

    def generate_orders(
        self,
        count: int,
        customer_ids: List[str]
    ) -> pd.DataFrame:
        """Generate orders with foreign key relationships"""
        data = []
        for i in range(count):
            data.append({
                "order_id": f"ORD-{i+1:08d}",
                "customer_id": np.random.choice(customer_ids),
                "order_date": self.fake.date_between(start_date="-1y", end_date="today"),
                "amount": np.random.lognormal(4, 1),
                "status": np.random.choice(["completed", "pending", "cancelled"], p=[0.8, 0.15, 0.05])
            })

        df = pd.DataFrame(data)
        df["order_date"] = pd.to_datetime(df["order_date"])
        return df

    def generate_metrics(
        self,
        count: int,
        metric_names: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """Generate metrics data"""
        if metric_names is None:
            metric_names = ["revenue", "cost", "profit_margin"]

        data = {
            "timestamp": pd.date_range(start="2024-01-01", periods=count, freq="H")
        }

        for metric in metric_names:
            if metric == "profit_margin":
                data[metric] = np.random.beta(5, 2, count) * 0.4 - 0.1  # -10% to 30%
            elif metric in ["revenue", "sales"]:
                data[metric] = np.random.lognormal(8, 1, count)
            elif metric == "cost":
                data[metric] = np.random.lognormal(7.5, 1, count)
            else:
                data[metric] = np.random.exponential(100, count)

        return pd.DataFrame(data)

    def generate_time_series(
        self,
        metric: str,
        periods: int,
        pattern: str = "random"
    ) -> pd.DataFrame:
        """Generate time series data with patterns"""
        dates = pd.date_range(start="2023-01-01", periods=periods, freq="D")

        if pattern == "seasonal":
            # Create seasonal pattern
            trend = np.linspace(100, 150, periods)
            seasonal = 20 * np.sin(2 * np.pi * np.arange(periods) / 365)
            noise = np.random.normal(0, 5, periods)
            values = trend + seasonal + noise
        elif pattern == "trending":
            trend = np.linspace(100, 200, periods)
            noise = np.random.normal(0, 10, periods)
            values = trend + noise
        else:  # random
            values = np.random.lognormal(5, 0.5, periods)

        return pd.DataFrame({
            "date": dates,
            "value": values,
            "metric": metric
        })

    def inject_anomalies(
        self,
        df: pd.DataFrame,
        anomaly_rate: float = 0.05,
        anomaly_type: str = "spike"
    ) -> pd.DataFrame:
        """Inject anomalies into data for demo purposes"""
        df = df.copy()
        n_anomalies = int(len(df) * anomaly_rate)

        # Mark anomalies
        df["is_anomaly"] = False
        anomaly_indices = np.random.choice(df.index, n_anomalies, replace=False)
        df.loc[anomaly_indices, "is_anomaly"] = True

        # Modify values for anomalies
        if anomaly_type == "spike":
            # Find first numeric column
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) > 0:
                col = numeric_cols[0]
                df.loc[anomaly_indices, col] *= np.random.uniform(5, 10, n_anomalies)

        return df

    def create_relationships(
        self,
        datasets: Dict[str, pd.DataFrame],
        relationships: List[Tuple[str, str, str]]
    ) -> Dict[str, pd.DataFrame]:
        """Ensure foreign key relationships are valid"""
        for source_table, fk_column, target_table in relationships:
            if source_table in datasets and target_table in datasets:
                # Get valid IDs from target table
                id_column = f"{target_table[:-1]}_id"  # Simple pluralization handling
                if id_column not in datasets[target_table].columns:
                    # Try first column as ID
                    id_column = datasets[target_table].columns[0]

                valid_ids = datasets[target_table][id_column].tolist()

                # Ensure source table has valid foreign keys
                if fk_column not in datasets[source_table].columns:
                    # Add foreign key column
                    datasets[source_table][fk_column] = np.random.choice(
                        valid_ids, len(datasets[source_table])
                    )

        return datasets

    def export_to_csv(self, df: pd.DataFrame) -> str:
        """Export DataFrame to CSV string"""
        return df.to_csv(index=False)

    def export_to_json(self, df: pd.DataFrame) -> str:
        """Export DataFrame to JSON string"""
        # Convert dates to string for JSON serialization
        df_copy = df.copy()
        for col in df_copy.select_dtypes(include=['datetime']).columns:
            df_copy[col] = df_copy[col].astype(str)
        return df_copy.to_json(orient="records")

    def to_elasticsearch_bulk(
        self,
        df: pd.DataFrame,
        index_name: str
    ) -> List[Dict[str, Any]]:
        """Convert DataFrame to Elasticsearch bulk format"""
        bulk_data = []

        for _, row in df.iterrows():
            # Add index action
            bulk_data.append({"index": {"_index": index_name}})
            # Add document
            doc = row.to_dict()
            # Convert any datetime objects to strings
            for key, value in doc.items():
                if pd.api.types.is_datetime64_any_dtype(type(value)):
                    doc[key] = str(value)
            bulk_data.append(doc)

        return bulk_data

    def identify_aha_moments(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify potential A-ha moments from context"""
        aha_moments = []
        pain_points = context.get("pain_points", [])

        for pain_point in pain_points:
            pain_lower = pain_point.lower()

            if "fraud" in pain_lower:
                aha_moments.append({
                    "type": "real_time_fraud_detection",
                    "description": "Detect fraud in real-time with 95% accuracy",
                    "query": "FROM transactions | WHERE risk_score > 0.8 | STATS count() BY hour",
                    "visualization": "spike_chart",
                    "expected_reaction": "Wow, we caught that fraud spike immediately!"
                })

            elif "slow" in pain_lower or "hours" in pain_lower:
                aha_moments.append({
                    "type": "instant_insights",
                    "description": "Get insights in milliseconds instead of hours",
                    "query": "FROM events | STATS avg(duration_ms) BY type | LIMIT 10",
                    "visualization": "comparison_chart",
                    "expected_reaction": "That's 1000x faster than our current system!"
                })

            elif "false positive" in pain_lower:
                aha_moments.append({
                    "type": "accuracy_improvement",
                    "description": "Reduce false positives by 80%",
                    "query": "FROM alerts | EVAL accurate = true_positive / (true_positive + false_positive)",
                    "visualization": "before_after",
                    "expected_reaction": "This would save us so much analyst time!"
                })

            elif "cost" in pain_lower or "expensive" in pain_lower:
                aha_moments.append({
                    "type": "cost_reduction",
                    "description": "Reduce operational costs by 60%",
                    "query": "FROM metrics | EVAL savings = old_cost - new_cost | STATS sum(savings)",
                    "visualization": "savings_counter",
                    "expected_reaction": "That's millions in savings!"
                })

        # Default A-ha moment if none identified
        if not aha_moments:
            aha_moments.append({
                "type": "general_insight",
                "description": "Instant insights from complex data",
                "query": "FROM data | STATS count() BY category | SORT count DESC",
                "visualization": "dashboard",
                "expected_reaction": "This is exactly what we need!"
            })

        return aha_moments

    def create_aha_moment_data(self, config: Dict[str, Any]) -> pd.DataFrame:
        """Create data that demonstrates the A-ha moment"""
        if config["type"] == "fraud_detection":
            # Create normal and anomalous periods
            normal_data = pd.DataFrame({
                "transaction_id": [f"TXN-{i:08d}" for i in range(1000)],
                "amount": np.random.lognormal(4, 1, 1000),
                "risk_score": np.random.beta(2, 8, 1000),  # Mostly low
                "is_fraud": np.random.choice([True, False], 1000, p=[config["normal_rate"], 1-config["normal_rate"]]),
                "period": "normal"
            })

            anomaly_data = pd.DataFrame({
                "transaction_id": [f"TXN-{i:08d}" for i in range(1000, 1100)],
                "amount": np.random.lognormal(5, 1.5, 100),  # Higher amounts
                "risk_score": np.random.beta(8, 2, 100),  # Mostly high
                "is_fraud": np.random.choice([True, False], 100, p=[config["anomaly_rate"], 1-config["anomaly_rate"]]),
                "period": "anomaly"
            })

            return pd.concat([normal_data, anomaly_data], ignore_index=True)

        elif config["type"] == "performance":
            # Show dramatic performance improvement
            old_system = pd.DataFrame({
                "query_id": [f"Q-{i:04d}" for i in range(100)],
                "system": "old",
                "response_time_ms": np.random.exponential(5000, 100),  # Average 5 seconds
                "success_rate": np.random.beta(7, 3, 100)  # 70% success
            })

            new_system = pd.DataFrame({
                "query_id": [f"Q-{i:04d}" for i in range(100, 200)],
                "system": "new",
                "response_time_ms": np.random.exponential(50, 100),  # Average 50ms
                "success_rate": np.random.beta(9.5, 0.5, 100)  # 95% success
            })

            return pd.concat([old_system, new_system], ignore_index=True)

        else:
            # Generic improvement data
            return pd.DataFrame({
                "metric_id": [f"M-{i:04d}" for i in range(200)],
                "before": np.random.exponential(100, 200),
                "after": np.random.exponential(20, 200),
                "improvement_pct": np.random.uniform(60, 90, 200)
            })

    def generate_aha_query(self, config: Dict[str, Any]) -> str:
        """Generate ES|QL query for the A-ha moment"""
        if config["type"] == "cost_savings":
            return f"""FROM metrics
| EVAL old_{config['metric']} = {config['metric']} * {1/(1-config['improvement'])}
| EVAL time_saved = old_{config['metric']} - {config['metric']}
| EVAL cost_reduction = time_saved * hourly_rate
| STATS
    total_saved = SUM(cost_reduction),
    avg_improvement = AVG(time_saved),
    improvement_pct = {config['improvement'] * 100}
"""
        elif config["type"] == "fraud_detection":
            return """FROM transactions
| WHERE risk_score > 0.7
| EVAL fraud_probability = CASE(
    risk_score > 0.9, "Very High",
    risk_score > 0.8, "High",
    risk_score > 0.7, "Medium",
    "Low"
  )
| STATS
    fraud_count = COUNT(*),
    total_amount = SUM(amount),
    avg_risk = AVG(risk_score)
  BY fraud_probability
| SORT avg_risk DESC
"""
        else:
            return """FROM events
| STATS count = COUNT(*) BY event_type
| EVAL percentage = ROUND(100.0 * count / SUM(count) OVER (), 2)
| SORT count DESC
| LIMIT 10
"""