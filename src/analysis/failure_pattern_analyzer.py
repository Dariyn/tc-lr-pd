"""
Failure pattern analysis module for extracting recurring issues from work order text.

Purpose: Identify common failure types, root causes, and recurring problems to
prioritize preventive maintenance and equipment upgrades.
"""

import pandas as pd
import logging
from collections import Counter
from typing import List, Dict, Set
import re

logger = logging.getLogger(__name__)

# Common English stopwords to filter out
STOPWORDS = {
    'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
    'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
    'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'should',
    'could', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those',
    'it', 'its', 'they', 'them', 'their', 'what', 'which', 'who', 'when',
    'where', 'why', 'how', 'all', 'each', 'every', 'both', 'few', 'more',
    'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own',
    'same', 'so', 'than', 'too', 'very', 'just', 'there', 'here'
}

# Common failure keywords to detect
FAILURE_KEYWORDS = {
    'leak': ['leak', 'leaking', 'leakage', 'drip', 'dripping'],
    'broken': ['broken', 'break', 'broke', 'damage', 'damaged', 'cracked', 'crack'],
    'malfunction': ['malfunction', 'malfunctioning', 'not working', 'failed', 'failure'],
    'electrical': ['electrical', 'electric', 'power', 'circuit', 'wiring', 'short'],
    'noise': ['noise', 'noisy', 'loud', 'sound', 'vibration', 'vibrating'],
    'clog': ['clog', 'clogged', 'blocked', 'blockage', 'stuck'],
    'worn': ['worn', 'wear', 'deteriorated', 'corroded', 'corrosion', 'rust', 'rusted'],
    'sensor': ['sensor', 'detector', 'alarm', 'switch'],
    'motor': ['motor', 'compressor', 'pump', 'fan', 'blower'],
    'valve': ['valve', 'solenoid', 'actuator'],
}


class FailurePatternAnalyzer:
    """
    Analyzer for extracting and identifying failure patterns from work order text fields.

    Uses simple text processing (word frequency, phrase detection) to identify
    recurring issues without requiring machine learning models.
    """

    def __init__(self):
        """Initialize the failure pattern analyzer."""
        self.stopwords = STOPWORDS
        self.failure_keywords = FAILURE_KEYWORDS

    def extract_keywords(self, text: str, min_length: int = 3) -> List[str]:
        """
        Extract meaningful keywords from text.

        Filters out stopwords and short words to focus on meaningful terms.
        Handles mixed language text (English/Chinese) by preserving non-ASCII characters.

        Args:
            text: Text to extract keywords from
            min_length: Minimum word length to keep (default: 3)

        Returns:
            List of extracted keywords in lowercase
        """
        if not text or pd.isna(text):
            return []

        # Convert to lowercase and split on whitespace and common punctuation
        text = str(text).lower()
        # Split on whitespace, comma, semicolon, period, parentheses
        words = re.split(r'[\s,;.()\[\]]+', text)

        keywords = []
        for word in words:
            # Remove leading/trailing punctuation
            word = word.strip('.,;:!?"\'-')

            # Skip if empty after stripping
            if not word:
                continue

            # Keep if:
            # - Not a stopword AND length >= min_length (for English words)
            # - OR contains non-ASCII characters (for Chinese/mixed text)
            has_non_ascii = any(ord(char) > 127 for char in word)

            if has_non_ascii:
                keywords.append(word)
            elif word not in self.stopwords and len(word) >= min_length:
                keywords.append(word)

        return keywords

    def find_common_phrases(self, df: pd.DataFrame, field: str = 'Problem',
                           top_n: int = 20) -> pd.DataFrame:
        """
        Find most common 2-3 word phrases in a text field.

        Args:
            df: DataFrame with work order data
            field: Text field to analyze (default: 'Problem')
            top_n: Number of top phrases to return (default: 20)

        Returns:
            DataFrame with columns: phrase, frequency, example_text
        """
        if field not in df.columns:
            logger.warning(f"Field '{field}' not found in DataFrame")
            return pd.DataFrame(columns=['phrase', 'frequency', 'example_text'])

        # Extract all valid text values
        texts = df[field].dropna().astype(str)

        # Track 2-word and 3-word phrases
        bigrams = Counter()
        trigrams = Counter()
        phrase_examples = {}  # Store example text for each phrase

        for text in texts:
            keywords = self.extract_keywords(text)

            # Generate bigrams
            for i in range(len(keywords) - 1):
                phrase = f"{keywords[i]} {keywords[i+1]}"
                bigrams[phrase] += 1
                if phrase not in phrase_examples:
                    phrase_examples[phrase] = text[:100]  # Store first 100 chars as example

            # Generate trigrams
            for i in range(len(keywords) - 2):
                phrase = f"{keywords[i]} {keywords[i+1]} {keywords[i+2]}"
                trigrams[phrase] += 1
                if phrase not in phrase_examples:
                    phrase_examples[phrase] = text[:100]

        # Combine and get top phrases
        all_phrases = {**bigrams, **trigrams}
        top_phrases = Counter(all_phrases).most_common(top_n)

        # Build result DataFrame
        results = []
        for phrase, freq in top_phrases:
            results.append({
                'phrase': phrase,
                'frequency': freq,
                'example_text': phrase_examples.get(phrase, '')
            })

        result_df = pd.DataFrame(results)
        logger.info(f"Found {len(result_df)} common phrases in '{field}'")

        return result_df

    def categorize_by_failure_type(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Group failures into categories based on keywords in text fields.

        Analyzes Problem, Cause, Remedy, and description fields to categorize
        failures (leak, broken, malfunction, electrical, etc.).

        Args:
            df: DataFrame with work order data including text fields

        Returns:
            DataFrame with columns: failure_category, count, avg_cost, example_wo
        """
        # Text fields to analyze
        text_fields = ['Problem', 'Cause', 'Remedy', 'description']
        available_fields = [f for f in text_fields if f in df.columns]

        if not available_fields:
            logger.warning("No text fields available for failure categorization")
            return pd.DataFrame(columns=['failure_category', 'count', 'avg_cost', 'example_wo'])

        # Track which category each work order belongs to
        wo_categories = {}  # wo_index -> set of categories

        for idx, row in df.iterrows():
            categories = set()

            # Combine all available text fields
            combined_text = ' '.join([
                str(row[field]) for field in available_fields
                if pd.notna(row[field])
            ]).lower()

            # Check for each failure type
            for category, keywords in self.failure_keywords.items():
                for keyword in keywords:
                    if keyword in combined_text:
                        categories.add(category)
                        break

            # If no category found, mark as 'other'
            if not categories:
                categories.add('other')

            wo_categories[idx] = categories

        # Aggregate by category
        category_stats = {}

        for idx, categories in wo_categories.items():
            row = df.loc[idx]
            cost = row.get('PO_AMOUNT', 0) if 'PO_AMOUNT' in df.columns else 0
            wo_no = row.get('wo_no', f'WO-{idx}') if 'wo_no' in df.columns else f'WO-{idx}'

            for category in categories:
                if category not in category_stats:
                    category_stats[category] = {
                        'count': 0,
                        'total_cost': 0,
                        'costs': [],
                        'example_wo': wo_no
                    }

                category_stats[category]['count'] += 1
                if pd.notna(cost) and cost > 0:
                    category_stats[category]['total_cost'] += cost
                    category_stats[category]['costs'].append(cost)

        # Build result DataFrame
        results = []
        for category, stats in category_stats.items():
            avg_cost = (sum(stats['costs']) / len(stats['costs'])) if stats['costs'] else 0
            results.append({
                'failure_category': category,
                'count': stats['count'],
                'avg_cost': avg_cost,
                'example_wo': stats['example_wo']
            })

        result_df = pd.DataFrame(results).sort_values('count', ascending=False)
        logger.info(f"Categorized failures into {len(result_df)} categories")

        return result_df

    def identify_recurring_issues(self, df: pd.DataFrame,
                                  by_equipment: bool = True) -> pd.DataFrame:
        """
        Find equipment with repeated same failures.

        Args:
            df: DataFrame with work order data
            by_equipment: If True, group by equipment; if False, analyze overall

        Returns:
            DataFrame with columns: Equipment_ID (if by_equipment), pattern,
                                   occurrences, avg_cost, category
        """
        if by_equipment and 'Equipment_ID' not in df.columns:
            logger.warning("Equipment_ID not found, analyzing patterns overall")
            by_equipment = False

        # Text fields to analyze
        text_fields = ['Problem', 'Cause', 'Remedy', 'description']
        available_fields = [f for f in text_fields if f in df.columns]

        if not available_fields:
            logger.warning("No text fields available for pattern identification")
            return pd.DataFrame(columns=['Equipment_ID', 'pattern', 'occurrences',
                                        'avg_cost', 'category'])

        results = []

        if by_equipment:
            # Group by equipment
            for equipment_id, group in df.groupby('Equipment_ID'):
                # Find common phrases for this equipment
                for field in available_fields:
                    phrases_df = self.find_common_phrases(group, field=field, top_n=5)

                    # Only include patterns that occur multiple times
                    recurring = phrases_df[phrases_df['frequency'] > 1]

                    for _, phrase_row in recurring.iterrows():
                        # Calculate average cost for work orders with this pattern
                        pattern_mask = group[field].astype(str).str.lower().str.contains(
                            phrase_row['phrase'], na=False, regex=False
                        )
                        pattern_group = group[pattern_mask]

                        if 'PO_AMOUNT' in df.columns:
                            valid_costs = pattern_group[pattern_group['PO_AMOUNT'] > 0]['PO_AMOUNT']
                            avg_cost = valid_costs.mean() if len(valid_costs) > 0 else 0
                        else:
                            avg_cost = 0

                        # Determine category
                        category = self._get_pattern_category(phrase_row['phrase'])

                        results.append({
                            'Equipment_ID': equipment_id,
                            'pattern': phrase_row['phrase'],
                            'occurrences': phrase_row['frequency'],
                            'avg_cost': avg_cost,
                            'category': category
                        })
        else:
            # Analyze overall patterns
            for field in available_fields:
                phrases_df = self.find_common_phrases(df, field=field, top_n=20)

                # Only include patterns that occur multiple times
                recurring = phrases_df[phrases_df['frequency'] > 1]

                for _, phrase_row in recurring.iterrows():
                    # Calculate average cost for work orders with this pattern
                    pattern_mask = df[field].astype(str).str.lower().str.contains(
                        phrase_row['phrase'], na=False, regex=False
                    )
                    pattern_group = df[pattern_mask]

                    if 'PO_AMOUNT' in df.columns:
                        valid_costs = pattern_group[pattern_group['PO_AMOUNT'] > 0]['PO_AMOUNT']
                        avg_cost = valid_costs.mean() if len(valid_costs) > 0 else 0
                    else:
                        avg_cost = 0

                    category = self._get_pattern_category(phrase_row['phrase'])

                    results.append({
                        'pattern': phrase_row['phrase'],
                        'occurrences': phrase_row['frequency'],
                        'avg_cost': avg_cost,
                        'category': category
                    })

        result_df = pd.DataFrame(results)
        if len(result_df) > 0:
            result_df = result_df.sort_values('occurrences', ascending=False)

        logger.info(f"Identified {len(result_df)} recurring patterns")

        return result_df

    def _get_pattern_category(self, pattern: str) -> str:
        """
        Determine the failure category for a pattern.

        Args:
            pattern: Text pattern to categorize

        Returns:
            Category name or 'other' if no match
        """
        pattern_lower = pattern.lower()

        for category, keywords in self.failure_keywords.items():
            for keyword in keywords:
                if keyword in pattern_lower:
                    return category

        return 'other'
