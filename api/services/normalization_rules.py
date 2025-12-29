"""Source-specific normalization rules configuration."""

from typing import Dict, List, Optional, Pattern
import re


class NormalizationRule:
    """Configuration for a normalization rule."""
    
    def __init__(
        self,
        pattern: str,
        replacement: str = "",
        flags: int = 0,
        description: str = ""
    ):
        """
        Initialize a normalization rule.
        
        Args:
            pattern: Regex pattern to match
            replacement: Replacement string (empty string to remove)
            flags: Regex flags (re.IGNORECASE, etc.)
            description: Human-readable description of the rule
        """
        self.pattern = re.compile(pattern, flags)
        self.replacement = replacement
        self.description = description


# Default boilerplate patterns
DEFAULT_BOILERPLATE_PATTERNS = [
    # Common header patterns
    NormalizationRule(
        r"^.*?Copyright\s+©?\s*\d{4}.*?$",
        "",
        re.MULTILINE | re.IGNORECASE,
        "Copyright notices"
    ),
    NormalizationRule(
        r"^.*?All rights reserved.*?$",
        "",
        re.MULTILINE | re.IGNORECASE,
        "All rights reserved notices"
    ),
    # Common footer patterns
    NormalizationRule(
        r"^.*?Last updated:.*?$",
        "",
        re.MULTILINE | re.IGNORECASE,
        "Last updated timestamps"
    ),
    NormalizationRule(
        r"^.*?Page \d+ of \d+.*?$",
        "",
        re.MULTILINE | re.IGNORECASE,
        "Page numbers"
    ),
    # Navigation patterns (if on separate lines)
    NormalizationRule(
        r"^(Home|About|Contact|Privacy|Terms).*?$",
        "",
        re.MULTILINE | re.IGNORECASE,
        "Navigation menu items"
    ),
    # Email patterns in footers
    NormalizationRule(
        r"^.*?Contact us:.*?$",
        "",
        re.MULTILINE | re.IGNORECASE,
        "Contact information headers"
    ),
    # Date patterns that are likely timestamps (not content dates)
    NormalizationRule(
        r"^.*?Updated on: \d{1,2}/\d{1,2}/\d{4}.*?$",
        "",
        re.MULTILINE | re.IGNORECASE,
        "Update timestamps"
    ),
    # Common legal disclaimers
    NormalizationRule(
        r"^.*?This document is provided for informational purposes only.*?$",
        "",
        re.MULTILINE | re.IGNORECASE,
        "Legal disclaimers"
    ),
]


def get_normalization_rules(source_metadata: Optional[Dict] = None) -> List[NormalizationRule]:
    """
    Get normalization rules for a source.
    
    Args:
        source_metadata: Source metadata that may contain custom normalization rules
    
    Returns:
        List of NormalizationRule objects to apply
    """
    rules = DEFAULT_BOILERPLATE_PATTERNS.copy()
    
    # Add source-specific rules if provided
    if source_metadata and 'normalization_rules' in source_metadata:
        custom_rules = source_metadata['normalization_rules']
        
        if isinstance(custom_rules, list):
            for rule_config in custom_rules:
                if isinstance(rule_config, dict):
                    pattern = rule_config.get('pattern', '')
                    replacement = rule_config.get('replacement', '')
                    flags = rule_config.get('flags', 0)
                    description = rule_config.get('description', 'Custom rule')
                    
                    if pattern:
                        rules.append(NormalizationRule(pattern, replacement, flags, description))
    
    return rules


def get_boilerplate_patterns(source_metadata: Optional[Dict] = None) -> List[Pattern]:
    """
    Get compiled regex patterns for boilerplate removal.
    
    Args:
        source_metadata: Source metadata that may contain custom patterns
    
    Returns:
        List of compiled regex patterns
    """
    rules = get_normalization_rules(source_metadata)
    return [rule.pattern for rule in rules]



