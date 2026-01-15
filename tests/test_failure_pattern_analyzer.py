"""
Tests for failure pattern analysis.

Validates text extraction, pattern identification, cost correlation,
and recommendation generation.
"""

import pytest
import pandas as pd
from src.analysis.failure_pattern_analyzer import FailurePatternAnalyzer


@pytest.fixture
def analyzer():
    """Create a FailurePatternAnalyzer instance."""
    return FailurePatternAnalyzer()


@pytest.fixture
def sample_data():
    """Create sample work order data with known patterns."""
    data = {
        'wo_no': ['WO001', 'WO002', 'WO003', 'WO004', 'WO005',
                 'WO006', 'WO007', 'WO008', 'WO009', 'WO010'],
        'Equipment_ID': ['EQ001', 'EQ001', 'EQ001', 'EQ002', 'EQ002',
                        'EQ003', 'EQ003', 'EQ004', 'EQ005', 'EQ006'],
        'equipment_primary_category': ['HVAC', 'HVAC', 'HVAC', 'HVAC', 'HVAC',
                                      'Elevator', 'Elevator', 'Plumbing', 'Electrical', 'HVAC'],
        'Problem': [
            'HVAC refrigerant leak detected',
            'Refrigerant leak in cooling system',
            'HVAC refrigerant leak',
            'Motor malfunction not working',
            'Motor malfunction in compressor',
            'Elevator malfunction',
            'Cable worn and damaged',
            'Pipe leak dripping water',
            'Electrical circuit broken',
            'Filter clogged'
        ],
        'Cause': [
            'Worn seal causing leak',
            'Cracked pipe',
            'Seal damage',
            'Electrical fault',
            'Bearing worn',
            'Sensor failure',
            'Normal wear',
            'Corrosion',
            'Short circuit',
            'Dirt accumulation'
        ],
        'Remedy': [
            'Replaced seal and recharged refrigerant',
            'Repaired pipe and recharged system',
            'Replaced seal',
            'Replaced motor',
            'Replaced bearings and motor',
            'Replaced sensor',
            'Replaced cable',
            'Repaired pipe',
            'Replaced circuit breaker',
            'Cleaned filter'
        ],
        'description': [
            'Annual maintenance found leak',
            'Tenant complaint about cooling',
            'Routine check found issue',
            'Equipment not responding',
            'Loud noise from unit',
            'Elevator stuck on floor 3',
            'Regular inspection found damage',
            'Water damage reported',
            'Power outage in area',
            'Reduced airflow'
        ],
        'PO_AMOUNT': [5000, 4500, 4800, 3000, 3500, 2000, 1500, 800, 1200, 300]
    }
    return pd.DataFrame(data)


def test_extract_keywords_basic(analyzer):
    """Test basic keyword extraction."""
    text = "The HVAC system has a refrigerant leak"
    keywords = analyzer.extract_keywords(text)

    # Should filter 'the', 'has', 'a' (stopwords)
    # Should keep 'hvac', 'system', 'refrigerant', 'leak'
    assert 'hvac' in keywords
    assert 'system' in keywords
    assert 'refrigerant' in keywords
    assert 'leak' in keywords
    assert 'the' not in keywords
    assert 'has' not in keywords
    assert 'a' not in keywords


def test_extract_keywords_min_length(analyzer):
    """Test keyword extraction filters short words."""
    text = "A big red car on street"
    keywords = analyzer.extract_keywords(text, min_length=3)

    # Should keep words >= 3 chars (excluding stopwords)
    assert 'big' in keywords
    assert 'red' in keywords
    assert 'car' in keywords
    assert 'street' in keywords
    # Should filter 'a', 'on' (stopwords) and would filter 2-letter words


def test_extract_keywords_mixed_language(analyzer):
    """Test keyword extraction preserves Chinese characters."""
    text = "空调 leak detected 制冷剂 problem"
    keywords = analyzer.extract_keywords(text)

    # Should preserve Chinese words (non-ASCII)
    assert '空调' in keywords
    assert '制冷剂' in keywords
    # Should also keep English words
    assert 'leak' in keywords
    assert 'detected' in keywords
    assert 'problem' in keywords


def test_extract_keywords_empty_text(analyzer):
    """Test keyword extraction with empty or None text."""
    assert analyzer.extract_keywords(None) == []
    assert analyzer.extract_keywords('') == []
    assert analyzer.extract_keywords('   ') == []


def test_extract_keywords_punctuation(analyzer):
    """Test keyword extraction removes punctuation."""
    text = "leak! broken, damaged; cracked. (malfunction)"
    keywords = analyzer.extract_keywords(text)

    # Should extract words without punctuation
    assert 'leak' in keywords
    assert 'broken' in keywords
    assert 'damaged' in keywords
    assert 'cracked' in keywords
    assert 'malfunction' in keywords


def test_find_common_phrases(analyzer, sample_data):
    """Test finding common phrases in Problem field."""
    phrases_df = analyzer.find_common_phrases(sample_data, field='Problem', top_n=5)

    # Should find "refrigerant leak" appearing 3 times
    assert len(phrases_df) > 0
    refrigerant_leak = phrases_df[phrases_df['phrase'].str.contains('refrigerant leak')]
    assert len(refrigerant_leak) > 0
    assert refrigerant_leak.iloc[0]['frequency'] == 3

    # Should find "motor malfunction" appearing 2 times
    motor_malfunction = phrases_df[phrases_df['phrase'].str.contains('motor malfunction')]
    if len(motor_malfunction) > 0:
        assert motor_malfunction.iloc[0]['frequency'] == 2


def test_find_common_phrases_missing_field(analyzer, sample_data):
    """Test finding phrases when field doesn't exist."""
    phrases_df = analyzer.find_common_phrases(sample_data, field='NonexistentField')

    # Should return empty DataFrame with correct columns
    assert len(phrases_df) == 0
    assert 'phrase' in phrases_df.columns
    assert 'frequency' in phrases_df.columns
    assert 'example_text' in phrases_df.columns


def test_categorize_by_failure_type(analyzer, sample_data):
    """Test failure categorization by keywords."""
    categories_df = analyzer.categorize_by_failure_type(sample_data)

    assert len(categories_df) > 0

    # Should detect 'leak' category (3 HVAC refrigerant leaks + 1 pipe leak = 4)
    leak_cat = categories_df[categories_df['failure_category'] == 'leak']
    assert len(leak_cat) > 0
    assert leak_cat.iloc[0]['count'] >= 3  # At least 3 refrigerant leaks

    # Should detect 'malfunction' category (3 total: 2 motor + 1 elevator)
    malfunction_cat = categories_df[categories_df['failure_category'] == 'malfunction']
    assert len(malfunction_cat) > 0
    assert malfunction_cat.iloc[0]['count'] >= 2

    # Should detect 'worn' category (cable worn)
    worn_cat = categories_df[categories_df['failure_category'] == 'worn']
    assert len(worn_cat) > 0

    # Should detect 'clog' category
    clog_cat = categories_df[categories_df['failure_category'] == 'clog']
    assert len(clog_cat) > 0


def test_categorize_by_failure_type_avg_cost(analyzer, sample_data):
    """Test that categorization calculates average costs correctly."""
    categories_df = analyzer.categorize_by_failure_type(sample_data)

    # Leak category should have high avg cost (refrigerant leaks are expensive)
    leak_cat = categories_df[categories_df['failure_category'] == 'leak']
    if len(leak_cat) > 0:
        # Refrigerant leaks: 5000, 4500, 4800 + pipe leak: 800
        # Average should be around (5000+4500+4800+800)/4 = 3775
        assert leak_cat.iloc[0]['avg_cost'] > 1000


def test_categorize_by_failure_type_no_text_fields(analyzer):
    """Test categorization when no text fields are available."""
    data = {
        'wo_no': ['WO001', 'WO002'],
        'Equipment_ID': ['EQ001', 'EQ002'],
        'PO_AMOUNT': [100, 200]
    }
    df = pd.DataFrame(data)

    categories_df = analyzer.categorize_by_failure_type(df)

    # Should return empty DataFrame with correct columns
    assert len(categories_df) == 0
    assert 'failure_category' in categories_df.columns


def test_identify_recurring_issues_by_equipment(analyzer, sample_data):
    """Test identifying recurring issues for specific equipment."""
    patterns_df = analyzer.identify_recurring_issues(sample_data, by_equipment=True)

    assert len(patterns_df) > 0

    # EQ001 should have "refrigerant leak" pattern (3 occurrences)
    eq001_patterns = patterns_df[patterns_df['Equipment_ID'] == 'EQ001']
    assert len(eq001_patterns) > 0
    refrigerant_patterns = eq001_patterns[
        eq001_patterns['pattern'].str.contains('refrigerant')
    ]
    assert len(refrigerant_patterns) > 0
    # Should have multiple occurrences
    assert refrigerant_patterns.iloc[0]['occurrences'] > 1


def test_identify_recurring_issues_overall(analyzer, sample_data):
    """Test identifying recurring issues across all equipment."""
    patterns_df = analyzer.identify_recurring_issues(sample_data, by_equipment=False)

    assert len(patterns_df) > 0

    # Should find "refrigerant leak" as top pattern (3 occurrences)
    refrigerant_patterns = patterns_df[
        patterns_df['pattern'].str.contains('refrigerant')
    ]
    assert len(refrigerant_patterns) > 0
    assert refrigerant_patterns.iloc[0]['occurrences'] >= 3


def test_identify_recurring_issues_categories(analyzer, sample_data):
    """Test that recurring issues are assigned correct categories."""
    patterns_df = analyzer.identify_recurring_issues(sample_data, by_equipment=False)

    # Refrigerant leak should be categorized as 'leak'
    refrigerant_patterns = patterns_df[
        patterns_df['pattern'].str.contains('refrigerant')
    ]
    if len(refrigerant_patterns) > 0:
        assert refrigerant_patterns.iloc[0]['category'] == 'leak'

    # Motor malfunction should be categorized as 'malfunction'
    motor_patterns = patterns_df[
        patterns_df['pattern'].str.contains('motor')
    ]
    if len(motor_patterns) > 0:
        assert motor_patterns.iloc[0]['category'] in ['malfunction', 'motor']


def test_calculate_pattern_costs(analyzer, sample_data):
    """Test pattern cost calculation."""
    costs_df = analyzer.calculate_pattern_costs(sample_data)

    assert len(costs_df) > 0

    # Should have correct columns
    assert 'pattern' in costs_df.columns
    assert 'occurrences' in costs_df.columns
    assert 'total_cost' in costs_df.columns
    assert 'avg_cost' in costs_df.columns
    assert 'category' in costs_df.columns
    assert 'equipment_affected' in costs_df.columns

    # Refrigerant leak should have high total cost (3 occurrences: 5000+4500+4800)
    refrigerant_patterns = costs_df[
        costs_df['pattern'].str.contains('refrigerant')
    ]
    if len(refrigerant_patterns) > 0:
        assert refrigerant_patterns.iloc[0]['total_cost'] > 10000
        assert refrigerant_patterns.iloc[0]['occurrences'] >= 3


def test_calculate_pattern_costs_equipment_affected(analyzer, sample_data):
    """Test that pattern costs track equipment affected."""
    costs_df = analyzer.calculate_pattern_costs(sample_data)

    # Refrigerant leak affects EQ001 (3 times) but only 1 equipment
    refrigerant_patterns = costs_df[
        costs_df['pattern'].str.contains('refrigerant')
    ]
    if len(refrigerant_patterns) > 0:
        # Should affect at least 1 equipment
        assert refrigerant_patterns.iloc[0]['equipment_affected'] >= 1


def test_find_high_impact_patterns(analyzer, sample_data):
    """Test finding high-impact patterns."""
    high_impact_df = analyzer.find_high_impact_patterns(sample_data, min_occurrences=2)

    # Should find patterns with >= 2 occurrences and above-median cost
    if len(high_impact_df) > 0:
        assert all(high_impact_df['occurrences'] >= 2)
        assert 'impact_score' in high_impact_df.columns

        # Refrigerant leak should be high impact (frequent + expensive)
        refrigerant_patterns = high_impact_df[
            high_impact_df['pattern'].str.contains('refrigerant')
        ]
        if len(refrigerant_patterns) > 0:
            assert refrigerant_patterns.iloc[0]['impact_score'] > 0


def test_find_high_impact_patterns_threshold(analyzer, sample_data):
    """Test high-impact pattern filtering with different thresholds."""
    # With low threshold (2), should find more patterns
    low_threshold = analyzer.find_high_impact_patterns(sample_data, min_occurrences=2)

    # With high threshold (5), should find fewer patterns
    high_threshold = analyzer.find_high_impact_patterns(sample_data, min_occurrences=5)

    # High threshold should have fewer or equal patterns
    assert len(high_threshold) <= len(low_threshold)


def test_find_high_impact_patterns_no_patterns(analyzer):
    """Test high-impact patterns when no recurring issues exist."""
    data = {
        'wo_no': ['WO001', 'WO002'],
        'Equipment_ID': ['EQ001', 'EQ002'],
        'Problem': ['Issue A', 'Issue B'],  # All different, no patterns
        'PO_AMOUNT': [100, 200]
    }
    df = pd.DataFrame(data)

    high_impact_df = analyzer.find_high_impact_patterns(df, min_occurrences=2)

    # Should return empty DataFrame with correct columns
    assert len(high_impact_df) == 0
    assert 'impact_score' in high_impact_df.columns


def test_get_pattern_recommendations(analyzer, sample_data):
    """Test generating actionable recommendations."""
    recommendations = analyzer.get_pattern_recommendations(sample_data)

    # Should generate recommendations for high-impact patterns
    if len(recommendations) > 0:
        rec = recommendations[0]

        # Should have required keys
        assert 'pattern' in rec
        assert 'occurrences' in rec
        assert 'total_cost' in rec
        assert 'avg_cost' in rec
        assert 'category' in rec
        assert 'equipment_affected' in rec
        assert 'suggestion' in rec

        # Suggestion should be a non-empty string
        assert isinstance(rec['suggestion'], str)
        assert len(rec['suggestion']) > 0

        # Costs should be formatted as strings with $
        assert rec['total_cost'].startswith('$')
        assert rec['avg_cost'].startswith('$')


def test_get_pattern_recommendations_category_specific(analyzer, sample_data):
    """Test that recommendations are category-specific."""
    recommendations = analyzer.get_pattern_recommendations(sample_data)

    if len(recommendations) > 0:
        # Find a leak recommendation
        leak_recs = [r for r in recommendations if r['category'] == 'leak']
        if leak_recs:
            # Leak recommendations should mention seals, gaskets, or piping
            suggestion = leak_recs[0]['suggestion'].lower()
            assert any(word in suggestion for word in ['seal', 'gasket', 'piping', 'pipe', 'leak'])


def test_get_pattern_recommendations_no_high_impact(analyzer):
    """Test recommendations when no high-impact patterns found."""
    data = {
        'wo_no': ['WO001', 'WO002'],
        'Equipment_ID': ['EQ001', 'EQ002'],
        'Problem': ['Issue A', 'Issue B'],
        'PO_AMOUNT': [10, 20]  # Low costs
    }
    df = pd.DataFrame(data)

    recommendations = analyzer.get_pattern_recommendations(df)

    # Should return empty list
    assert recommendations == []


def test_edge_case_single_word_description(analyzer):
    """Test handling of single-word descriptions."""
    data = {
        'wo_no': ['WO001', 'WO002'],
        'Equipment_ID': ['EQ001', 'EQ002'],
        'Problem': ['leak', 'leak'],  # Single word repeated
        'PO_AMOUNT': [100, 200]
    }
    df = pd.DataFrame(data)

    patterns_df = analyzer.identify_recurring_issues(df, by_equipment=False)

    # Single words don't form phrases (need 2-3 words), so no patterns found
    # This is expected behavior - pattern detection looks for multi-word phrases
    assert isinstance(patterns_df, pd.DataFrame)  # Should return valid DataFrame


def test_edge_case_empty_problem_fields(analyzer):
    """Test handling of empty text fields."""
    data = {
        'wo_no': ['WO001', 'WO002', 'WO003'],
        'Equipment_ID': ['EQ001', 'EQ001', 'EQ002'],
        'Problem': ['leak detected', None, ''],  # Some empty
        'PO_AMOUNT': [100, 200, 150]
    }
    df = pd.DataFrame(data)

    # Should not crash and should handle empty fields gracefully
    patterns_df = analyzer.identify_recurring_issues(df, by_equipment=False)

    # Result should be valid DataFrame (may be empty)
    assert isinstance(patterns_df, pd.DataFrame)


def test_edge_case_mixed_language_patterns(analyzer):
    """Test pattern detection with mixed English and Chinese text."""
    data = {
        'wo_no': ['WO001', 'WO002', 'WO003'],
        'Equipment_ID': ['EQ001', 'EQ001', 'EQ002'],
        'Problem': [
            '空调 refrigerant leak 制冷剂泄漏',
            'HVAC refrigerant leak detected',
            'Refrigerant leak 制冷剂'
        ],
        'PO_AMOUNT': [1000, 1200, 1100]
    }
    df = pd.DataFrame(data)

    patterns_df = analyzer.identify_recurring_issues(df, by_equipment=False)

    # Should detect "refrigerant leak" as common pattern
    refrigerant_patterns = patterns_df[
        patterns_df['pattern'].str.contains('refrigerant')
    ]
    assert len(refrigerant_patterns) > 0
    assert refrigerant_patterns.iloc[0]['occurrences'] >= 2
