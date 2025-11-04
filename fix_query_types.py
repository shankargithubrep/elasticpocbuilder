#!/usr/bin/env python3
"""
Fix query type categorization in generated query modules.

Rewrites "type" field to use standardized values:
- 'scripted' for non-parameterized queries
- 'parameterized' for queries with ?parameters
- 'rag' for queries using MATCH (semantic search)
"""

import re
import sys
from pathlib import Path


def categorize_query(query_dict_str: str) -> str:
    """Determine the correct query type based on the esql content"""
    # Check for parameters (?param_name)
    has_param = bool(re.search(r'\?[\w]+', query_dict_str))

    # Check for MATCH (semantic search indicator)
    has_match = 'MATCH(' in query_dict_str

    if has_param:
        return 'parameterized'
    elif has_match:
        return 'rag'
    else:
        return 'scripted'


def fix_query_module(file_path: Path):
    """Fix query types in a query_generator.py file"""
    print(f"Processing: {file_path}")

    content = file_path.read_text()
    original_content = content

    # Find all queries.append({ ... }) blocks
    pattern = r'(queries\.append\(\{[\s\S]*?\}\))'
    matches = re.finditer(pattern, content)

    replacements = []
    for match in matches:
        query_block = match.group(1)

        # Extract current type value
        type_match = re.search(r'"type":\s*"([^"]+)"', query_block)
        if type_match:
            current_type = type_match.group(1)
            correct_type = categorize_query(query_block)

            if current_type != correct_type:
                print(f"  Changing type '{current_type}' -> '{correct_type}'")
                new_query_block = query_block.replace(
                    f'"type": "{current_type}"',
                    f'"type": "{correct_type}"'
                )
                replacements.append((query_block, new_query_block))

    # Apply all replacements
    for old, new in replacements:
        content = content.replace(old, new)

    if content != original_content:
        file_path.write_text(content)
        print(f"✅ Fixed {len(replacements)} query types in {file_path}")
        return len(replacements)
    else:
        print(f"✓ No changes needed for {file_path}")
        return 0


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Fix specific file
        file_path = Path(sys.argv[1])
        if file_path.exists():
            fix_query_module(file_path)
        else:
            print(f"Error: File not found: {file_path}")
            sys.exit(1)
    else:
        # Fix all query_generator.py files in demos/
        demos_dir = Path("demos")
        total_fixed = 0

        for query_file in demos_dir.glob("*/query_generator.py"):
            fixed = fix_query_module(query_file)
            total_fixed += fixed

        print(f"\n✅ Total query types fixed: {total_fixed}")
