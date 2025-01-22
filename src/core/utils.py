import difflib

def get_diff(old_lines, new_lines):
    """
    Compute the differences between two lists of lines.
    """
    diff_lines = []
    diff = difflib.Differ()
    comparison = list(diff.compare(old_lines, new_lines))
    for line in comparison:
        if line.startswith("  "):
            continue  # No change
        elif line.startswith("- "):
            diff_lines.append(f"  - {line[2:].strip()}\n")
        elif line.startswith("+ "):
            diff_lines.append(f"  + {line[2:].strip()}\n")
    return diff_lines