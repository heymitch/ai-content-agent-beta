"""
Abstract base validator for platform-specific content validation
All platform validators should inherit from this class
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any

class BaseValidator(ABC):
    """Abstract base class for content validators"""

    @abstractmethod
    def validate(self, content: str) -> List[Dict[str, Any]]:
        """
        Run platform-specific validation checks

        Args:
            content: Content to validate

        Returns:
            List of issue dicts with structure:
            {
                'type': str (issue type identifier),
                'severity': str (high/medium/low),
                'auto_fixable': bool,
                'fix_function': Optional[Callable],
                'message': str (human-readable description),
                ...additional context
            }
        """
        pass

    @abstractmethod
    def get_grading_rubric(self) -> str:
        """
        Return grading criteria for Claude validator

        Returns:
            Multi-line string with grading rubric
        """
        pass

    @abstractmethod
    def get_writing_rules(self) -> str:
        """
        Return platform-specific writing guidelines

        Returns:
            Multi-line string with writing rules
        """
        pass

    def get_validation_summary(self, issues: List[Dict[str, Any]]) -> str:
        """
        Generate human-readable summary of validation issues

        Args:
            issues: List of validation issues

        Returns:
            Formatted summary string
        """
        if not issues:
            return "✅ No validation issues found"

        high = [i for i in issues if i.get('severity') == 'high']
        medium = [i for i in issues if i.get('severity') == 'medium']
        low = [i for i in issues if i.get('severity') == 'low']

        summary = f"⚠️ Found {len(issues)} validation issue(s):\n"

        if high:
            summary += f"\n🔴 High priority ({len(high)}):\n"
            for issue in high:
                summary += f"  - {issue.get('message', issue.get('type', 'Unknown'))}\n"

        if medium:
            summary += f"\n🟡 Medium priority ({len(medium)}):\n"
            for issue in medium:
                summary += f"  - {issue.get('message', issue.get('type', 'Unknown'))}\n"

        if low:
            summary += f"\n🟢 Low priority ({len(low)}):\n"
            for issue in low:
                summary += f"  - {issue.get('message', issue.get('type', 'Unknown'))}\n"

        auto_fixable = [i for i in issues if i.get('auto_fixable')]
        if auto_fixable:
            summary += f"\n🔧 {len(auto_fixable)} issue(s) can be auto-fixed"

        return summary
