# Fails if a shell line has its case terminator ";;" only inside a trailing comment (the comment then swallows the
# branch's exit and ";;"; the churn mid launcher looped until a timeout on 2026-11-13). Usage: case_end_check.py FILE...
import re, sys
bad = []
for f in sys.argv[1:]:
    for n, line in enumerate(open(f), 1):
        m = re.search(r"\s#\s", line)
        if m and ";;" in line[m.end():] and ";;" not in line[:m.start()]:
            bad.append(f"{f}:{n}: ';;' only inside a comment")
print("\n".join(bad) or "case ends ok"); sys.exit(1 if bad else 0)
