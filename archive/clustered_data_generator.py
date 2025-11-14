"""
Enhanced data generator that creates realistic event clustering patterns
to ensure queries return meaningful results.
"""

import random
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple


class ClusteredEventGenerator:
    """Generate events with realistic clustering patterns for better query results"""

    def __init__(self, start_time: datetime, end_time: datetime):
        self.start_time = start_time
        self.end_time = end_time
        self.duration = end_time - start_time

    def generate_incident_periods(
        self,
        num_incidents: int = 10,
        min_duration_hours: float = 0.5,
        max_duration_hours: float = 24
    ) -> List[Dict[str, Any]]:
        """
        Generate time periods when incidents occur with high failure rates.

        Returns list of incident dictionaries with:
        - start_time: When incident began
        - end_time: When incident ended
        - severity: 'minor', 'major', or 'critical'
        - affected_resources: List of affected cells/MMEs
        """
        incidents = []

        for i in range(num_incidents):
            # Random start time within the period
            start_offset = random.random() * 0.9  # Don't start incidents in last 10%
            start_time = self.start_time + self.duration * start_offset

            # Random duration
            duration_hours = random.uniform(min_duration_hours, max_duration_hours)
            end_time = start_time + timedelta(hours=duration_hours)

            # Random severity with realistic distribution
            severity = np.random.choice(
                ['minor', 'major', 'critical'],
                p=[0.6, 0.3, 0.1]  # Most incidents are minor
            )

            incidents.append({
                'incident_id': f'INC-{i+1:04d}',
                'start_time': start_time,
                'end_time': end_time,
                'duration_hours': duration_hours,
                'severity': severity
            })

        # Sort by start time
        incidents.sort(key=lambda x: x['start_time'])
        return incidents

    def generate_clustered_events(
        self,
        total_events: int,
        incident_periods: List[Dict[str, Any]],
        baseline_rate: float = 0.1,
        incident_multipliers: Dict[str, float] = None
    ) -> List[datetime]:
        """
        Generate event timestamps with clustering during incident periods.

        Args:
            total_events: Total number of events to generate
            incident_periods: List of incident period dictionaries
            baseline_rate: Proportion of events during normal operations
            incident_multipliers: Multipliers for event rate by severity

        Returns:
            List of timestamps
        """
        if incident_multipliers is None:
            incident_multipliers = {
                'minor': 10,
                'major': 50,
                'critical': 200
            }

        timestamps = []

        # Calculate total incident duration
        total_incident_hours = sum(inc['duration_hours'] for inc in incident_periods)
        total_hours = (self.end_time - self.start_time).total_seconds() / 3600
        normal_hours = total_hours - total_incident_hours

        # Calculate weighted rates
        weighted_incident_rate = sum(
            inc['duration_hours'] * incident_multipliers[inc['severity']]
            for inc in incident_periods
        )

        # Distribute events proportionally
        baseline_events = int(total_events * baseline_rate)
        incident_events = total_events - baseline_events

        # Generate baseline events (spread evenly)
        for _ in range(baseline_events):
            # Random time not during incidents
            while True:
                ts = self.start_time + timedelta(seconds=random.random() * self.duration.total_seconds())
                # Check if it's during an incident
                in_incident = any(
                    inc['start_time'] <= ts <= inc['end_time']
                    for inc in incident_periods
                )
                if not in_incident:
                    timestamps.append(ts)
                    break

        # Generate incident events
        remaining_events = incident_events
        for incident in incident_periods:
            # Calculate events for this incident based on severity and duration
            incident_weight = (
                incident['duration_hours'] * incident_multipliers[incident['severity']]
            ) / weighted_incident_rate

            num_events = int(remaining_events * incident_weight)

            # Generate events during this incident period
            inc_duration = (incident['end_time'] - incident['start_time']).total_seconds()
            for _ in range(num_events):
                offset = random.random() * inc_duration
                ts = incident['start_time'] + timedelta(seconds=offset)
                timestamps.append(ts)

        # Sort all timestamps
        timestamps.sort()
        return timestamps[:total_events]  # Ensure we return exactly the requested number

    def assign_resources_to_events(
        self,
        timestamps: List[datetime],
        incident_periods: List[Dict[str, Any]],
        all_cells: List[str],
        all_mmes: List[str],
        correlation_factor: float = 0.7
    ) -> Tuple[List[str], List[str]]:
        """
        Assign cells and MMEs to events with correlation during incidents.

        Args:
            timestamps: Event timestamps
            incident_periods: Incident periods
            all_cells: List of all cell IDs
            all_mmes: List of all MME hosts
            correlation_factor: How correlated failures are during incidents (0-1)

        Returns:
            Tuple of (cell assignments, MME assignments)
        """
        cell_assignments = []
        mme_assignments = []

        # Pre-assign affected resources to each incident
        for incident in incident_periods:
            if incident['severity'] == 'critical':
                # Critical affects multiple cells and MMEs
                incident['affected_cells'] = random.sample(all_cells, k=min(30, len(all_cells)))
                incident['affected_mmes'] = random.sample(all_mmes, k=min(3, len(all_mmes)))
            elif incident['severity'] == 'major':
                # Major affects a cluster of cells
                incident['affected_cells'] = random.sample(all_cells, k=min(10, len(all_cells)))
                incident['affected_mmes'] = random.sample(all_mmes, k=2)
            else:
                # Minor affects few cells
                incident['affected_cells'] = random.sample(all_cells, k=min(3, len(all_cells)))
                incident['affected_mmes'] = [random.choice(all_mmes)]

        # Assign resources to each event
        for ts in timestamps:
            # Check if timestamp is during an incident
            active_incident = None
            for incident in incident_periods:
                if incident['start_time'] <= ts <= incident['end_time']:
                    active_incident = incident
                    break

            if active_incident and random.random() < correlation_factor:
                # During incident, use affected resources
                cell = random.choice(active_incident['affected_cells'])
                mme = random.choice(active_incident['affected_mmes'])
            else:
                # Normal distribution
                cell = random.choice(all_cells)
                mme = random.choice(all_mmes)

            cell_assignments.append(cell)
            mme_assignments.append(mme)

        return cell_assignments, mme_assignments


class EnhancedDataGenerationStrategy:
    """Strategy for generating data that produces meaningful query results"""

    @staticmethod
    def calculate_required_events(
        time_range_days: int,
        num_dimensions: int,
        min_bucket_size: int = 10,
        time_bucket_minutes: int = 5
    ) -> int:
        """
        Calculate minimum events needed for meaningful aggregations.

        Args:
            time_range_days: Total days of data
            num_dimensions: Number of unique values in GROUP BY dimension
            min_bucket_size: Minimum events per bucket for meaningful stats
            time_bucket_minutes: Time bucket size in minutes

        Returns:
            Minimum number of events to generate
        """
        total_minutes = time_range_days * 24 * 60
        num_buckets = total_minutes / time_bucket_minutes

        # Account for clustering - not all buckets will have data
        active_bucket_ratio = 0.2  # Assume 20% of buckets have events

        active_buckets = num_buckets * active_bucket_ratio

        # Events needed for minimum bucket size across dimensions
        min_events = active_buckets * num_dimensions * min_bucket_size

        # Add 50% buffer for variation
        return int(min_events * 1.5)

    @staticmethod
    def validate_query_thresholds(
        query: str,
        expected_max_per_bucket: int
    ) -> Tuple[bool, str]:
        """
        Check if query thresholds are realistic given data distribution.

        Returns:
            Tuple of (is_valid, suggested_fix)
        """
        import re

        # Extract WHERE clause thresholds
        where_pattern = r'WHERE.*?(?:failure_count|error_rate|unique_imsi_count)\s*[>>=]+\s*(\d+)'
        matches = re.findall(where_pattern, query, re.IGNORECASE)

        if not matches:
            return True, ""

        max_threshold = max(int(m) for m in matches)

        if max_threshold > expected_max_per_bucket:
            suggested_threshold = max(2, expected_max_per_bucket // 2)
            return False, f"Threshold {max_threshold} too high. Suggest using {suggested_threshold}"

        return True, ""


# Example usage for fixing data generation
def generate_realistic_failure_data(
    num_cells: int = 100,
    num_mmes: int = 5,
    time_range_days: int = 90,
    target_query_bucket_size: int = 50
) -> pd.DataFrame:
    """
    Generate failure data with realistic clustering for meaningful query results.
    """
    end_time = datetime.now()
    start_time = end_time - timedelta(days=time_range_days)

    # Calculate required events
    strategy = EnhancedDataGenerationStrategy()
    total_failures = strategy.calculate_required_events(
        time_range_days=time_range_days,
        num_dimensions=num_cells,
        min_bucket_size=target_query_bucket_size,
        time_bucket_minutes=5
    )

    print(f"Generating {total_failures} failures for meaningful aggregations")

    # Generate clustered events
    generator = ClusteredEventGenerator(start_time, end_time)

    # Create incident periods
    incidents = generator.generate_incident_periods(
        num_incidents=15,  # More incidents for better clustering
        min_duration_hours=1,
        max_duration_hours=12
    )

    # Generate timestamps with clustering
    timestamps = generator.generate_clustered_events(
        total_events=total_failures,
        incident_periods=incidents,
        baseline_rate=0.2  # 20% during normal operations
    )

    # Generate cell and MME lists
    cells = [f'CELL-{i:04d}' for i in range(1, num_cells + 1)]
    mmes = [f'MME-{i:02d}' for i in range(1, num_mmes + 1)]

    # Assign resources with correlation
    cell_assignments, mme_assignments = generator.assign_resources_to_events(
        timestamps=timestamps,
        incident_periods=incidents,
        all_cells=cells,
        all_mmes=mmes,
        correlation_factor=0.8  # High correlation during incidents
    )

    # Create DataFrame
    df = pd.DataFrame({
        'failure_id': [f'FAIL-{i:08d}' for i in range(len(timestamps))],
        '@timestamp': timestamps,
        'current_cell_id': cell_assignments,
        'mme_host': mme_assignments,
        # Add other fields as needed
        'procedure_type': [random.choice(['ATTACH', 'TAU', 'HANDOVER']) for _ in timestamps],
        'error_code': [random.choice(['EMM_15', 'EMM_17', 'S1AP_TIMEOUT']) for _ in timestamps]
    })

    return df


if __name__ == "__main__":
    # Test the generator
    df = generate_realistic_failure_data()

    # Verify distribution
    df['time_bucket'] = pd.to_datetime(df['@timestamp']).dt.floor('5min')
    grouped = df.groupby(['time_bucket', 'current_cell_id']).size()

    print(f"\nDistribution stats:")
    print(f"Max failures per bucket: {grouped.max()}")
    print(f"Buckets with >10 failures: {(grouped > 10).sum()}")
    print(f"Buckets with >50 failures: {(grouped > 50).sum()}")
    print(f"Buckets with >100 failures: {(grouped > 100).sum()}")