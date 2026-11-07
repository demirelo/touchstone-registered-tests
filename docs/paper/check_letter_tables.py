"""Fails when a response letter names a table number that the compiled paper does not give that table (lessons
2026-11-05 and 2026-11-07: numbers typed from memory were wrong, and a phrase list missed new references). Every table
number in the letter is written "Table N (tab:label)"; an unlabelled "Table N" fails. Usage: check_letter_tables.py LETTER.md MAIN.aux"""
import re
import sys


def problems(letter: str, aux: str) -> list[str]:
    num = dict(re.findall(r"\\newlabel\{(tab:[^}]*)\}\{\{(\d+)\}", aux)); out = []
    for m in re.finditer(r"\bTables? (\d+)(\s*\((tab:[^)\s]+)\))?", letter):
        n, label = m.group(1), m.group(3)
        if label is None:
            out.append(f"'{m.group(0)}': table number without its label; write 'Table {n} (tab:...)'")
        elif label not in num:
            out.append(f"{label}: not in the paper")
        elif num[label] != n:
            out.append(f"'{m.group(0)}': paper has Table {num[label]} for {label}")
    return out


if __name__ == "__main__":
    pr = problems(open(sys.argv[1]).read(), open(sys.argv[2]).read())
    print("\n".join(pr) or "ok"); sys.exit(1 if pr else 0)
