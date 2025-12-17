"""
Context Tracker
Tracks demo context extraction progress and prompts for missing information
"""

from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class ContextTracker:
    """Tracks extraction progress and prompts for missing info"""

    # Minimum requirements for generation:
    # - Company Name (required)
    # - Department (required)
    # - Pain Points OR Use Cases (at least one)
    # - Key Metrics (optional but recommended)

    REQUIRED_FIELDS = {
        'company_name': {
            'weight': 30,
            'prompt': 'What company are you building this demo for?',
            'display_name': 'Company',
            'required_for_generate': True
        },
        'department': {
            'weight': 25,
            'prompt': 'Which department will use this?',
            'display_name': 'Department',
            'required_for_generate': True
        },
        'pain_points': {
            'weight': 25,
            'prompt': 'What are the main pain points they face?',
            'min_count': 1,
            'display_name': 'Pain Points',
            'required_for_generate': 'pain_points_or_use_cases'
        },
        'use_cases': {
            'weight': 10,
            'prompt': 'What are the key use cases for this demo?',
            'min_count': 1,
            'display_name': 'Use Cases',
            'required_for_generate': 'pain_points_or_use_cases'
        },
        'metrics': {
            'weight': 10,
            'prompt': 'What metrics matter most to them?',
            'min_count': 1,
            'display_name': 'Key Metrics',
            'required_for_generate': False  # Optional but recommended
        }
    }

    def calculate_progress(self, context: Dict) -> Tuple[float, List[Tuple[str, str]]]:
        """
        Calculate completion percentage and missing fields

        Args:
            context: Current demo context dictionary

        Returns:
            Tuple of (progress_percentage, list of (field_name, prompt))
        """
        total_weight = sum(f['weight'] for f in self.REQUIRED_FIELDS.values())
        earned_weight = 0
        missing_fields = []

        for field, config in self.REQUIRED_FIELDS.items():
            value = context.get(field)

            if isinstance(value, list):
                # For lists, check minimum count
                min_count = config.get('min_count', 1)
                if len(value) >= min_count:
                    earned_weight += config['weight']
                else:
                    missing_fields.append((field, config['prompt']))
            elif value:
                earned_weight += config['weight']
            else:
                missing_fields.append((field, config['prompt']))

        progress = earned_weight / total_weight
        return progress, missing_fields

    def generate_prompt_for_missing(self, missing_fields: List[Tuple[str, str]]) -> Optional[str]:
        """
        Generate natural prompt for missing information

        Args:
            missing_fields: List of (field_name, prompt) tuples

        Returns:
            Natural language prompt or None if all fields complete
        """
        if not missing_fields:
            return None

        # Ask for up to 2 missing fields at a time
        prompts = [prompt for _, prompt in missing_fields[:2]]

        if len(prompts) == 1:
            return f"To create a comprehensive demo, could you tell me:\n\n• {prompts[0]}"
        else:
            return f"To create a comprehensive demo, could you tell me:\n\n• " + "\n• ".join(prompts)

    def get_completion_status(self, context: Dict) -> Dict:
        """
        Get detailed completion status for each field

        Args:
            context: Current demo context dictionary

        Returns:
            Dictionary with field statuses and display info
        """
        status = {}

        for field, config in self.REQUIRED_FIELDS.items():
            value = context.get(field)

            if isinstance(value, list):
                min_count = config.get('min_count', 1)
                is_complete = len(value) >= min_count
                display_value = f"{len(value)}/{min_count}" if not is_complete else f"{len(value)} ✓"
            else:
                is_complete = bool(value)
                display_value = "✓" if is_complete else "—"

            status[field] = {
                'is_complete': is_complete,
                'display_name': config['display_name'],
                'display_value': display_value,
                'value': value
            }

        return status

    def is_ready_to_generate(self, context: Dict) -> bool:
        """
        Check if context has enough information to generate demo.

        Requirements:
        - Company Name (required)
        - Department (required)
        - Pain Points OR Use Cases (at least one with at least 1 item)

        Args:
            context: Current demo context dictionary

        Returns:
            True if minimum requirements are met
        """
        # Check required fields
        if not context.get('company_name'):
            return False
        if not context.get('department'):
            return False

        # Check pain_points OR use_cases (at least one must have items)
        pain_points = context.get('pain_points', [])
        use_cases = context.get('use_cases', [])

        if not pain_points and not use_cases:
            return False

        return True

    def get_summary(self, context: Dict) -> str:
        """
        Get human-readable summary of current context

        Args:
            context: Current demo context dictionary

        Returns:
            Summary string
        """
        progress, missing = self.calculate_progress(context)
        status = self.get_completion_status(context)

        summary_parts = []

        # Company and department
        if context.get('company_name'):
            company_dept = context['company_name']
            if context.get('department'):
                company_dept += f" - {context['department']}"
            summary_parts.append(f"**Demo for:** {company_dept}")

        # Industry
        if context.get('industry'):
            summary_parts.append(f"**Industry:** {context['industry']}")

        # Pain points
        if context.get('pain_points'):
            summary_parts.append(f"**Pain Points:** {len(context['pain_points'])} identified")

        # Use cases
        if context.get('use_cases'):
            summary_parts.append(f"**Use Cases:** {len(context['use_cases'])} defined")

        # Metrics
        if context.get('metrics'):
            summary_parts.append(f"**Key Metrics:** {len(context['metrics'])} specified")

        # Progress
        summary_parts.append(f"\n**Progress:** {int(progress * 100)}% complete")

        return "\n".join(summary_parts)
