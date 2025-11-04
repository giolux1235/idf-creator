"""
IDF utilities: helpers for working with assembled IDF strings.
"""

from typing import List, Tuple


def dedupe_idf_string(idf_text: str) -> str:
    """Remove duplicate object definitions (by Type+Name) keeping first occurrence.
    Robust block-aware parsing: detects object headers with optional indentation,
    captures until the terminating semicolon, and de-duplicates regardless of spacing/case.
    """
    lines = idf_text.split('\n')
    out_lines: List[str] = []
    seen_keys: set[Tuple[str, str]] = set()
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        stripped = line.lstrip()
        # Detect object header line (not a comment, ends with ',')
        if stripped and not stripped.startswith('!') and stripped.endswith(','):
            # Capture header type
            obj_type = stripped.rstrip(',').strip()
            # Find name line (skip comments/blank)
            j = i + 1
            while j < n and (not lines[j].strip() or lines[j].lstrip().startswith('!')):
                j += 1
            if j >= len(lines):
                out_lines.append(line)
                i += 1
                continue
            obj_name = lines[j].strip().rstrip(',').strip()
            key = (obj_type.lower(), obj_name.lower())

            # Accumulate full block until a line ending with ';'
            block_lines = [lines[i]]
            k = i + 1
            ended = False
            while k < n:
                block_lines.append(lines[k])
                if lines[k].strip().endswith(';'):
                    ended = True
                    k += 1
                    break
                k += 1
            if not ended:
                if key not in seen_keys:
                    seen_keys.add(key)
                    out_lines.extend(block_lines)
                i = k
                continue

            if key in seen_keys:
                i = k
                continue
            else:
                seen_keys.add(key)
                out_lines.extend(block_lines)
                i = k
                continue
        else:
            out_lines.append(line)
            i += 1
    return '\n'.join(out_lines)
