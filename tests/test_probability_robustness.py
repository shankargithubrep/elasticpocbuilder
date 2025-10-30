"""
Tests for probability distribution robustness
Validates that safe_choice() helper prevents probability errors
"""

import numpy as np
import pytest


class TestSafeChoice:
    """Test suite for safe_choice() helper method"""

    @staticmethod
    def safe_choice(choices, size=None, weights=None):
        """
        Safer alternative to np.random.choice with automatic probability normalization.
        This is the same implementation used in generated modules.
        """
        if weights is not None:
            # Convert to numpy array and normalize
            weights = np.array(weights, dtype=float)
            probabilities = weights / weights.sum()
            return np.random.choice(choices, size=size, p=probabilities)
        else:
            return np.random.choice(choices, size=size)

    def test_weights_sum_to_100(self):
        """Test with weights that sum to 100 (common pattern)"""
        choices = ['PC', 'Console', 'Mobile']
        weights = [35, 45, 20]  # Sum = 100

        # Should work without error
        result = self.safe_choice(choices, size=1000, weights=weights)

        # Verify result
        assert len(result) == 1000
        assert all(r in choices for r in result)

    def test_weights_sum_to_1(self):
        """Test with weights that already sum to 1.0"""
        choices = ['A', 'B', 'C']
        weights = [0.5, 0.3, 0.2]  # Already probabilities

        # Should work without error
        result = self.safe_choice(choices, size=1000, weights=weights)

        # Verify result
        assert len(result) == 1000
        assert all(r in choices for r in result)

    def test_weights_arbitrary_values(self):
        """Test with arbitrary weight values"""
        choices = ['Free', 'Pro', 'Enterprise']
        weights = [5000, 3000, 1500]  # Arbitrary large numbers

        # Should work without error
        result = self.safe_choice(choices, size=1000, weights=weights)

        # Verify result
        assert len(result) == 1000
        assert all(r in choices for r in result)

    def test_weights_floating_point_precision(self):
        """Test with weights that might cause floating point issues"""
        choices = ['A', 'B', 'C']
        weights = [0.333, 0.333, 0.334]  # Sum = 1.000 (but might have precision issues)

        # Should work without error
        result = self.safe_choice(choices, size=1000, weights=weights)

        # Verify result
        assert len(result) == 1000
        assert all(r in choices for r in result)

    def test_distribution_matches_weights(self):
        """Verify distribution roughly matches input weights"""
        np.random.seed(42)  # For reproducibility

        choices = ['PC', 'Console', 'Mobile']
        weights = [50, 30, 20]  # Expected: 50%, 30%, 20%

        # Generate large sample
        result = self.safe_choice(choices, size=10000, weights=weights)

        # Count occurrences
        unique, counts = np.unique(result, return_counts=True)
        proportions = dict(zip(unique, counts / counts.sum()))

        # Verify proportions roughly match expected (within 2%)
        expected_proportions = {
            'PC': 0.50,
            'Console': 0.30,
            'Mobile': 0.20
        }

        for choice, expected in expected_proportions.items():
            actual = proportions[choice]
            assert abs(actual - expected) < 0.02, \
                f"{choice}: expected {expected:.2f}, got {actual:.2f}"

    def test_single_value_selection(self):
        """Test selecting a single value (size=None)"""
        choices = ['Free', 'Pro', 'Enterprise']
        weights = [50, 30, 20]

        # Should return a single value
        result = self.safe_choice(choices, weights=weights)

        # Verify result is a single choice
        assert result in choices

    def test_uniform_distribution_no_weights(self):
        """Test uniform distribution when no weights provided"""
        np.random.seed(42)

        choices = ['A', 'B', 'C', 'D']

        # Generate sample without weights
        result = self.safe_choice(choices, size=10000)

        # Count occurrences
        unique, counts = np.unique(result, return_counts=True)
        proportions = counts / counts.sum()

        # All should be roughly equal (within 2%)
        expected = 0.25
        for proportion in proportions:
            assert abs(proportion - expected) < 0.02

    def test_two_choice_boolean_pattern(self):
        """Test common boolean pattern (True/False with weights)"""
        choices = [True, False]
        weights = [85, 15]  # 85% True, 15% False

        result = self.safe_choice(choices, size=1000, weights=weights)

        # Verify distribution
        true_count = sum(result)
        true_proportion = true_count / len(result)

        assert abs(true_proportion - 0.85) < 0.05  # Within 5%

    def test_hourly_distribution_pattern(self):
        """Test realistic hourly distribution (24 choices)"""
        # Simulate hourly activity pattern
        hourly_weights = [
            1, 1, 1, 1, 1, 1, 2, 3,        # 0-7am: low
            5, 7, 8, 9, 10, 11, 10, 9,     # 8am-3pm: peak
            8, 7, 5, 4, 3, 2, 1, 1         # 4pm-11pm: decline
        ]

        result = self.safe_choice(range(24), size=10000, weights=hourly_weights)

        # Verify peak hours (8am-3pm) have more activity
        peak_hours = [8, 9, 10, 11, 12, 13, 14, 15]
        peak_count = sum(1 for h in result if h in peak_hours)
        peak_proportion = peak_count / len(result)

        # Peak hours should be > 50% of activity
        assert peak_proportion > 0.5

    def test_empty_weights_error(self):
        """Test that empty weights raises appropriate error"""
        choices = ['A', 'B', 'C']
        weights = []

        with pytest.raises((ValueError, ZeroDivisionError)):
            self.safe_choice(choices, size=100, weights=weights)

    def test_negative_weights_handled(self):
        """Test that negative weights are handled (should work after normalization)"""
        choices = ['A', 'B', 'C']
        weights = [50, 30, -10]  # Negative weight (unusual but valid after abs)

        # numpy choice doesn't allow negative probabilities
        # Our implementation should either:
        # 1. Raise an error, or
        # 2. Handle it gracefully

        # For now, expect it to raise an error from numpy
        with pytest.raises(ValueError):
            result = self.safe_choice(choices, size=100, weights=weights)

    def test_zero_weights_handled(self):
        """Test that zero weights work correctly"""
        choices = ['A', 'B', 'C']
        weights = [50, 0, 50]  # B has zero probability

        result = self.safe_choice(choices, size=1000, weights=weights)

        # B should never appear
        assert 'B' not in result
        assert 'A' in result
        assert 'C' in result

    def test_large_weight_differences(self):
        """Test with very large weight differences"""
        choices = ['Common', 'Rare', 'Epic', 'Legendary']
        weights = [10000, 100, 10, 1]  # Dramatic differences

        result = self.safe_choice(choices, size=10000, weights=weights)

        # Common should appear most frequently
        unique, counts = np.unique(result, return_counts=True)
        count_dict = dict(zip(unique, counts))

        assert count_dict['Common'] > count_dict.get('Rare', 0)
        assert count_dict.get('Rare', 0) > count_dict.get('Epic', 0)


class TestComparisonWithNumpyChoice:
    """Compare safe_choice with np.random.choice to ensure equivalence"""

    @staticmethod
    def safe_choice(choices, size=None, weights=None):
        """Same implementation as above"""
        if weights is not None:
            weights = np.array(weights, dtype=float)
            probabilities = weights / weights.sum()
            return np.random.choice(choices, size=size, p=probabilities)
        else:
            return np.random.choice(choices, size=size)

    def test_equivalent_to_normalized_numpy_choice(self):
        """Verify safe_choice produces same distribution as properly normalized numpy choice"""
        np.random.seed(42)

        choices = ['A', 'B', 'C']
        weights = [50, 30, 20]

        # Using safe_choice
        result1 = self.safe_choice(choices, size=1000, weights=weights)

        np.random.seed(42)

        # Using np.random.choice with manual normalization
        probabilities = np.array(weights) / np.sum(weights)
        result2 = np.random.choice(choices, size=1000, p=probabilities)

        # Results should be identical with same seed
        assert np.array_equal(result1, result2)


class TestRealWorldPatterns:
    """Test patterns commonly used in generated modules"""

    @staticmethod
    def safe_choice(choices, size=None, weights=None):
        """Same implementation as above"""
        if weights is not None:
            weights = np.array(weights, dtype=float)
            probabilities = weights / weights.sum()
            return np.random.choice(choices, size=size, p=probabilities)
        else:
            return np.random.choice(choices, size=size)

    def test_gaming_platform_distribution(self):
        """Test realistic gaming platform distribution"""
        platforms = ['PC', 'PlayStation', 'Xbox', 'Switch', 'iOS', 'Android']
        weights = [35, 20, 15, 8, 12, 10]

        result = self.safe_choice(platforms, size=1000, weights=weights)

        # Verify PC is most common
        unique, counts = np.unique(result, return_counts=True)
        count_dict = dict(zip(unique, counts))

        assert count_dict['PC'] > count_dict['PlayStation']
        assert count_dict['PlayStation'] > count_dict['Switch']

    def test_subscription_tier_distribution(self):
        """Test realistic subscription tier distribution"""
        tiers = ['Free', 'Basic', 'Premium', 'Enterprise']
        weights = [50, 30, 15, 5]  # Pyramid structure

        result = self.safe_choice(tiers, size=1000, weights=weights)

        # Verify pyramid structure
        unique, counts = np.unique(result, return_counts=True)
        count_dict = dict(zip(unique, counts))

        assert count_dict['Free'] > count_dict['Basic']
        assert count_dict['Basic'] > count_dict['Premium']
        assert count_dict['Premium'] > count_dict['Enterprise']

    def test_regional_distribution(self):
        """Test realistic regional distribution"""
        regions = ['North America', 'Europe', 'Asia Pacific', 'Latin America', 'Middle East', 'Africa']
        weights = [30, 25, 20, 12, 8, 5]

        result = self.safe_choice(regions, size=1000, weights=weights)

        # Verify North America is most common
        unique, counts = np.unique(result, return_counts=True)
        count_dict = dict(zip(unique, counts))

        assert count_dict['North America'] > count_dict['Europe']
        assert count_dict['Europe'] > count_dict['Asia Pacific']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
