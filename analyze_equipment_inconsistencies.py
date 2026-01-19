"""
Analyze equipment naming inconsistencies in adhoc_wo.csv
Identifies where the same equipment is recorded under different names or IDs.
"""

import pandas as pd
from collections import defaultdict
import re
import sys

# Force UTF-8 encoding for output
sys.stdout.reconfigure(encoding='utf-8')

# Load data
df = pd.read_csv('input/adhoc_wo.csv', low_memory=False)

print("=" * 80)
print("EQUIPMENT NAMING INCONSISTENCY ANALYSIS")
print("=" * 80)

# Get equipment columns
equipment_cols = ['Equipment_ID', 'EquipmentNumber', 'EquipmentName']
print(f"\nTotal records: {len(df)}")
print(f"\nUnique values:")
for col in equipment_cols:
    print(f"  {col}: {df[col].nunique()} unique values")

# 1. Check for same EquipmentNumber with different EquipmentName
print("\n" + "=" * 80)
print("1. SAME EQUIPMENT NUMBER WITH DIFFERENT NAMES")
print("=" * 80)

equip_num_to_names = defaultdict(set)
for _, row in df.iterrows():
    if pd.notna(row['EquipmentNumber']) and pd.notna(row['EquipmentName']):
        equip_num_to_names[row['EquipmentNumber']].add(row['EquipmentName'])

inconsistent_numbers = {k: v for k, v in equip_num_to_names.items() if len(v) > 1}
if inconsistent_numbers:
    for num, names in inconsistent_numbers.items():
        print(f"\nEquipmentNumber: {num}")
        for name in names:
            count = len(df[(df['EquipmentNumber'] == num) & (df['EquipmentName'] == name)])
            print(f"  - '{name}' ({count} records)")
else:
    print("\nNo inconsistencies found.")

# 2. Check for same Equipment_ID with different EquipmentName
print("\n" + "=" * 80)
print("2. SAME EQUIPMENT ID WITH DIFFERENT NAMES")
print("=" * 80)

equip_id_to_names = defaultdict(set)
for _, row in df.iterrows():
    if pd.notna(row['Equipment_ID']) and pd.notna(row['EquipmentName']):
        equip_id_to_names[row['Equipment_ID']].add(row['EquipmentName'])

inconsistent_ids = {k: v for k, v in equip_id_to_names.items() if len(v) > 1}
if inconsistent_ids:
    for eid, names in inconsistent_ids.items():
        print(f"\nEquipment_ID: {eid}")
        for name in names:
            count = len(df[(df['Equipment_ID'] == eid) & (df['EquipmentName'] == name)])
            print(f"  - '{name}' ({count} records)")
else:
    print("\nNo inconsistencies found.")

# 3. Check for similar names that might be the same equipment (Traditional vs Simplified Chinese)
print("\n" + "=" * 80)
print("3. POTENTIAL NAMING VARIATIONS (Traditional/Simplified Chinese)")
print("=" * 80)

# Common variations to check
variations = [
    ("無設備", "无设备"),  # Traditional vs Simplified for "No Equipment"
]

for trad, simp in variations:
    trad_count = len(df[df['EquipmentName'] == trad])
    simp_count = len(df[df['EquipmentName'] == simp])
    if trad_count > 0 or simp_count > 0:
        print(f"\n'{trad}' (Traditional): {trad_count} records")
        print(f"'{simp}' (Simplified): {simp_count} records")

# 4. List all unique equipment names and their counts
print("\n" + "=" * 80)
print("4. ALL UNIQUE EQUIPMENT NAMES (with counts)")
print("=" * 80)

name_counts = df['EquipmentName'].value_counts()
for name, count in name_counts.items():
    print(f"  '{name}': {count} records")

# 5. Check for same EquipmentName with different Equipment_IDs
print("\n" + "=" * 80)
print("5. SAME EQUIPMENT NAME WITH DIFFERENT IDs")
print("=" * 80)

name_to_ids = defaultdict(set)
for _, row in df.iterrows():
    if pd.notna(row['EquipmentName']) and pd.notna(row['Equipment_ID']):
        name_to_ids[row['EquipmentName']].add(row['Equipment_ID'])

# Filter out "no equipment" entries and show only real inconsistencies
no_equip_values = ['無設備', '无设备', 'NULL', None]
inconsistent_names = {k: v for k, v in name_to_ids.items()
                     if len(v) > 1 and k not in no_equip_values}

if inconsistent_names:
    for name, ids in inconsistent_names.items():
        print(f"\nEquipmentName: '{name}'")
        for eid in ids:
            count = len(df[(df['EquipmentName'] == name) & (df['Equipment_ID'] == eid)])
            equip_nums = df[(df['EquipmentName'] == name) & (df['Equipment_ID'] == eid)]['EquipmentNumber'].unique()
            print(f"  - Equipment_ID: {eid} ({count} records)")
            print(f"    EquipmentNumbers: {list(equip_nums)}")
else:
    print("\nNo inconsistencies found in real equipment (excluding 'No Equipment' entries).")

# 6. Check for equipment with similar names (fuzzy matching)
print("\n" + "=" * 80)
print("6. SIMILAR EQUIPMENT NAMES (Potential Duplicates)")
print("=" * 80)

unique_names = df['EquipmentName'].dropna().unique()
unique_names = [n for n in unique_names if n not in no_equip_values]

# Simple similarity check - same words in different order or slight variations
from difflib import SequenceMatcher

def similar(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

similar_pairs = []
for i, name1 in enumerate(unique_names):
    for name2 in unique_names[i+1:]:
        if similar(name1, name2) > 0.6 and name1 != name2:
            similar_pairs.append((name1, name2, similar(name1, name2)))

if similar_pairs:
    for n1, n2, sim in sorted(similar_pairs, key=lambda x: -x[2]):
        count1 = len(df[df['EquipmentName'] == n1])
        count2 = len(df[df['EquipmentName'] == n2])
        print(f"\nSimilarity: {sim:.2%}")
        print(f"  '{n1}' ({count1} records)")
        print(f"  '{n2}' ({count2} records)")
else:
    print("\nNo similar equipment names found.")

print("\n" + "=" * 80)
print("ANALYSIS COMPLETE")
print("=" * 80)
