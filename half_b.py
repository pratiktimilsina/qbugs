"""Half (b) of the Improvement: platform bugs vs platform-level fault models.

Usage:
    python half_b.py [path/to/quantum_software_bugs.xlsx]     (default: ../quantum_software_bugs.xlsx)

Reads the paper's own family labels for its 410 bugs (sheet "Bug Families") and the 56 families
(sheet "Taxonomy"). No label is changed. Prints:
  1. Check: the share of the 410 bugs with >= 1 of the 20 mutation-supported families.
     It must be exactly 23/410 (paper, §4.3). If not, the script stops and does not
     print result (b), because it would be reading the labels differently from the paper.
  2. Result (b): the share of the 410 bugs with >= 1 family in the mapped family set
     (README Section 2.3), and the bugs counted.
"""
import sys
from pathlib import Path

import openpyxl

XLSX = Path(sys.argv[1] if len(sys.argv) > 1 else "../quantum_software_bugs.xlsx")

# Families assigned to the fault classes of arXiv:2609.24230 (README Section 2.3).
# Class 3 (determinism) was mapped to "no fitting family" and adds nothing to the set.
MAPPED = {"Measurement ordering error", "Missing field set"}

PAPER_K, PAPER_N = 23, 410  # paper, §4.3


def rows_of(ws):
    rows = list(ws.iter_rows(values_only=True))
    header = [str(c).strip() if c is not None else "" for c in rows[0]]
    return header, rows[1:]


def main():
    wb = openpyxl.load_workbook(XLSX, read_only=True)

    # The 56 families and the 20 mutation-supported ones, read from the Taxonomy sheet itself.
    header, rows = rows_of(wb["Taxonomy"])
    i_name, i_mut = header.index("Family_Name"), header.index("In_Mutation_Related_Bugs")
    names = {str(r[i_name]).strip() for r in rows if r and r[i_name]}
    mutation = {str(r[i_name]).strip() for r in rows if r and r[i_name] and str(r[i_mut]).strip() == "Yes"}
    print(f"Taxonomy: {len(names)} families, {len(mutation)} mutation-supported")
    missing = MAPPED - names
    if missing:
        sys.exit(f"Mapped families not in the Taxonomy sheet: {sorted(missing)}")

    # The paper's labels for each bug.
    header, rows = rows_of(wb["Bug Families"])
    i_id, i_fam = header.index("Bug_ID"), header.index("Bug_Families")
    bugs = {}
    unknown = set()
    for r in rows:
        if not r or not r[i_id]:
            continue
        raw = str(r[i_fam] or "")
        fams = {f.strip() for f in raw.replace(",", ";").replace("\n", ";").split(";") if f.strip()}
        unknown |= fams - names
        bugs[str(r[i_id]).strip()] = fams
    print(f"Bug Families: {len(bugs)} bugs read")
    if unknown:
        print(f"Labels not matching any of the 56 family names: {sorted(unknown)}")

    # Check against the paper's 23/410 before trusting any count.
    k_mut = sum(1 for f in bugs.values() if f & mutation)
    print(f"\nCheck: bugs with >= 1 mutation-supported family = {k_mut}/{len(bugs)}"
          f"  (paper: {PAPER_K}/{PAPER_N})")
    if (k_mut, len(bugs)) != (PAPER_K, PAPER_N) or unknown:
        sys.exit("CHECK FAILED: the labels are not being read as in the paper. "
                 "Result (b) is not printed.")
    print("Check passed.")

    # Result (b).
    hits = {b: f for b, f in bugs.items() if f & MAPPED}
    k = len(hits)
    print(f"\nResult (b): bugs with >= 1 family in the mapped set {sorted(MAPPED)}")
    print(f"  k/N = {k}/{len(bugs)} = {100 * k / len(bugs):.1f}%")
    print(f"  paper (mutation-supported): {PAPER_K}/{PAPER_N} = {100 * PAPER_K / PAPER_N:.1f}%")
    for fam in sorted(MAPPED):
        print(f"  bugs with {fam}: {sum(1 for f in bugs.values() if fam in f)}")
    print("\nBugs counted in result (b) (Bug_ID: families):")
    for b in sorted(hits):
        print(f"  {b}: {'; '.join(sorted(hits[b]))}")


if __name__ == "__main__":
    main()
