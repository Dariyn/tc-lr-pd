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

    def calculate_pattern_costs(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate total and average costs for each identified pattern.

        Finds all patterns in the data and aggregates cost information.

        Args:
            df: DataFrame with work order data including text fields and costs

        Returns:
            DataFrame with columns: pattern, occurrences, total_cost, avg_cost,
                                   category, equipment_affected, example_wo_numbers
        """
        # Get all recurring patterns
        patterns_df = self.identify_recurring_issues(df, by_equipment=False)

        if len(patterns_df) == 0:
            logger.warning("No patterns found for cost calculation")
            return pd.DataFrame(columns=['pattern', 'occurrences', 'total_cost',
                                        'avg_cost', 'category', 'equipment_affected',
                                        'example_wo_numbers'])

        # Text fields to analyze
        text_fields = ['Problem', 'Cause', 'Remedy', 'description']
        available_fields = [f for f in text_fields if f in df.columns]

        results = []

        for _, pattern_row in patterns_df.iterrows():
            pattern = pattern_row['pattern']

            # Find all work orders containing this pattern
            mask = pd.Series([False] * len(df), index=df.index)
            for field in available_fields:
                if field in df.columns:
                    field_mask = df[field].astype(str).str.lower().str.contains(
                        pattern, na=False, regex=False
                    )
                    mask = mask | field_mask

            pattern_wos = df[mask]

            # Calculate costs
            if 'PO_AMOUNT' in df.columns:
                valid_costs = pattern_wos[pattern_wos['PO_AMOUNT'] > 0]['PO_AMOUNT']
                total_cost = valid_costs.sum()
                avg_cost = valid_costs.mean() if len(valid_costs) > 0 else 0
            else:
                total_cost = 0
                avg_cost = 0

            # Count equipment affected
            if 'Equipment_ID' in df.columns:
                equipment_affected = pattern_wos['Equipment_ID'].nunique()
            else:
                equipment_affected = 0

            # Get example work order numbers
            if 'wo_no' in df.columns:
                example_wo_numbers = pattern_wos['wo_no'].head(3).tolist()
            else:
                example_wo_numbers = []

            results.append({
                'pattern': pattern,
                'occurrences': len(pattern_wos),
                'total_cost': total_cost,
                'avg_cost': avg_cost,
                'category': pattern_row['category'],
                'equipment_affected': equipment_affected,
                'example_wo_numbers': ', '.join(str(wo) for wo in example_wo_numbers)
            })

        result_df = pd.DataFrame(results).sort_values('total_cost', ascending=False)
        logger.info(f"Calculated costs for {len(result_df)} patterns")

        return result_df

    def find_high_impact_patterns(self, df: pd.DataFrame,
                                  min_occurrences: int = 5) -> pd.DataFrame:
        """
        Find patterns that occur frequently with high costs.

        High-impact patterns are those with:
        - Frequency >= min_occurrences (recurring issue)
        - Average cost above median (expensive to fix)
        - Affecting multiple equipment items (not isolated)

        Args:
            df: DataFrame with work order data
            min_occurrences: Minimum occurrences to be considered recurring (default: 5)

        Returns:
            DataFrame with high-impact patterns sorted by impact score
        """
        # Get pattern costs
        pattern_costs = self.calculate_pattern_costs(df)

        if len(pattern_costs) == 0:
            logger.warning("No patterns found for high-impact analysis")
            return pd.DataFrame(columns=['pattern', 'occurrences', 'total_cost',
                                        'avg_cost', 'category', 'equipment_affected',
                                        'impact_score', 'example_wo_numbers'])

        # Filter by minimum occurrences
        recurring = pattern_costs[pattern_costs['occurrences'] >= min_occurrences]

        if len(recurring) == 0:
            logger.warning(f"No patterns with >= {min_occurrences} occurrences")
            return pd.DataFrame(columns=['pattern', 'occurrences', 'total_cost',
                                        'avg_cost', 'category', 'equipment_affected',
                                        'impact_score', 'example_wo_numbers'])

        # Calculate median average cost
        median_avg_cost = recurring['avg_cost'].median()

        # Filter for above-median cost
        high_cost = recurring[recurring['avg_cost'] > median_avg_cost]

        if len(high_cost) == 0:
            logger.info("No patterns with above-median costs found")
            return pd.DataFrame(columns=['pattern', 'occurrences', 'total_cost',
                                        'avg_cost', 'category', 'equipment_affected',
                                        'impact_score', 'example_wo_numbers'])

        # Calculate impact score: (frequency * avg_cost * equipment_affected)
        # Normalize components to avoid score being too large
        high_cost = high_cost.copy()
        high_cost['impact_score'] = (
            high_cost['occurrences'] *
            high_cost['avg_cost'] / 1000 *  # Normalize cost to thousands
            (1 + high_cost['equipment_affected'])  # +1 to avoid zero
        )

        # Sort by impact score
        result_df = high_cost.sort_values('impact_score', ascending=False)

        logger.info(f"Found {len(result_df)} high-impact patterns")

        return result_df

    def get_pattern_recommendations(self, df: pd.DataFrame) -> List[Dict]:
        """
        Generate actionable recommendations for recurring high-cost patterns.

        Args:
            df: DataFrame with work order data

        Returns:
            List of recommendation dictionaries with keys:
            - pattern: The failure pattern
            - occurrences: Number of times it occurred
            - total_cost: Total cost across all occurrences
            - avg_cost: Average cost per occurrence
            - category: Failure category
            - equipment_affected: Number of equipment items affected
            - suggestion: Actionable recommendation text
        """
        # Get high-impact patterns
        high_impact = self.find_high_impact_patterns(df, min_occurrences=5)

        if len(high_impact) == 0:
            logger.info("No high-impact patterns found for recommendations")
            return []

        recommendations = []

        for _, row in high_impact.iterrows():
            pattern = row['pattern']
            category = row['category']
            occurrences = row['occurrences']
            total_cost = row['total_cost']
            avg_cost = row['avg_cost']
            equipment_affected = row['equipment_affected']

            # Generate category-specific suggestions
            if category == 'leak':
                suggestion = f"Inspect all affected equipment for {pattern}. Consider upgrading seals, gaskets, or piping to prevent future leaks."
            elif category == 'broken':
                suggestion = f"Review maintenance schedules for equipment experiencing {pattern}. Consider preventive replacement of vulnerable components."
            elif category == 'electrical':
                suggestion = f"Conduct electrical system audit for equipment showing {pattern}. Check for loose connections, aging wiring, or power quality issues."
            elif category == 'malfunction':
                suggestion = f"Investigate root cause of {pattern}. May indicate need for equipment upgrade or replacement if failures are frequent."
            elif category == 'worn':
                suggestion = f"Implement preventive maintenance program to replace components before {pattern} occurs. Schedule regular inspections."
            elif category == 'clog':
                suggestion = f"Increase cleaning frequency and inspect filters for equipment with {pattern}. Review fluid quality and filtration systems."
            elif category == 'noise':
                suggestion = f"Schedule vibration analysis and bearing inspection for equipment with {pattern}. Address before escalation to major failure."
            elif category == 'motor':
                suggestion = f"Review motor performance for equipment with {pattern}. Consider predictive maintenance using thermal imaging or vibration monitoring."
            elif category == 'sensor':
                suggestion = f"Calibrate or replace sensors experiencing {pattern}. Review sensor quality and environmental conditions."
            elif category == 'valve':
                suggestion = f"Inspect and service valves showing {pattern}. Consider upgrade to more reliable valve types if failures persist."
            else:
                suggestion = f"Investigate recurring {pattern} issue affecting {equipment_affected} equipment items. Develop targeted preventive maintenance strategy."

            # Add equipment-specific context if available
            if equipment_affected > 1:
                suggestion += f" Priority: affects {equipment_affected} equipment items."

            recommendations.append({
                'pattern': pattern,
                'occurrences': int(occurrences),
                'total_cost': f"${total_cost:,.0f}",
                'avg_cost': f"${avg_cost:,.0f}",
                'category': category,
                'equipment_affected': int(equipment_affected),
                'suggestion': suggestion
            })

        logger.info(f"Generated {len(recommendations)} recommendations")

        return recommendations
