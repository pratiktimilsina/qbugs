"""Half (a) of the Improvement: program mutants vs bugs in user quantum programs.

Usage:
    python half_a.py pool    # build the A1 + A2 candidate pool once, shuffle with the seed,
                             # and write pool_a.csv (refuses to overwrite an existing file)
    python half_a.py show    # print the next unscreened candidate (in seeded order) with its text
    python half_a.py decide ORDER yes "Family A; Family B" "note"
    python half_a.py decide ORDER no "" "reason"
                             # record the decision for candidate ORDER in pool_a.csv
    python half_a.py score   # Result (a): k/N for A1, A2 and pooled, next to the paper's 23/410

The rules followed here are in README Section 2.2.
"""
import csv
import gzip
import html
import json
import random
import re
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

SEED = 20261110
POOL_FILE = Path("pool_a.csv")

# Same window as the paper, inclusive at both ends (UTC).
START = datetime(2024, 7, 24, 0, 0, 0, tzinfo=timezone.utc)
END = datetime(2026, 7, 23, 23, 59, 59, tzinfo=timezone.utc)

# A1: QCSE tags listed in README Section 2.2.
QCSE_TAGS = ["qiskit", "qiskit-runtime", "cirq", "pyquil", "rigetti", "pennylane",
             "pytket", "amazon-braket", "qutip", "qasm", "programming"]

# A2: the paper's ten repositories and the user-error labels listed in README Section 2.2.
A2_LABELS = {
    "Qiskit/qiskit": None,
    "quantumlib/Cirq": '"kind/question","triage/works-as-expected"',
    "rigetti/pyquil": None,
    "PennyLaneAI/pennylane": '"question :question:"',
    "Quantinuum/tket": "invalid,question",
    "NVIDIA/cuda-quantum": None,
    "amazon-braket/amazon-braket-sdk-python": "invalid,question",
    "unitaryfoundation/mitiq": None,
    "qutip/qutip": "invalid",
    "openqasm/openqasm": "invalid,question",
}

# Columns for the screening and classification decisions.
DECISION_COLUMNS = ["eligible", "families", "decision_note"]
TARGET = 50  # planned target of eligible bugs; never reached (42 eligible)

# The paper's 56 families, names as in the Taxonomy sheet of quantum_software_bugs.xlsx.
# The first 20 are the mutation-supported families (In_Mutation_Related_Bugs = Yes; paper, Table 4).
MUTATION_FAMILIES = [
    "Broken inheritance", "Extra gate", "Extra measurement", "Flipped parameter sign",
    "Mishandled exception", "Misplaced gate", "Missing gate", "Missing measurement",
    "Missing statement", "Perturbed parameter", "Swapped parameters", "Wrong arithmetic",
    "Wrong comparison", "Wrong conditional", "Wrong constant", "Wrong decorator", "Wrong gate",
    "Wrong gate arity", "Wrong loop control", "Wrong qubit target",
]
OTHER_FAMILIES = [
    "Zeroed parameter", "API issue", "Conditional error", "Confusing mutator with accessor",
    "Constant replacement", "Incorrect operator", "Incorrect parameters", "Missing decomposition",
    "Missing field set", "Missing import", "Missing method call", "Missing transpilation",
    "Refactor", "Registration error", "Reversed output convention", "Backend dispatch error",
    "Circuit construction error", "Classical control error", "Compiler transformation error",
    "Concurrency error", "Copy aliasing error", "Dependency incompatibility",
    "Equality semantics error", "Format conversion error", "Mathematical formulation error",
    "Measurement ordering error", "Measurement result error", "Missing compilation step",
    "Missing input validation", "Numerical error", "Pass ordering error", "Serialization error",
    "Stale state error", "Symbolic algebra error", "Type-handling error", "Visualization error",
]
NO_FIT = "no fitting family"
ALL_LABELS = set(MUTATION_FAMILIES) | set(OTHER_FAMILIES) | {NO_FIT}
assert len(MUTATION_FAMILIES) == 20 and len(OTHER_FAMILIES) == 36


def fetch_qcse(tag):
    """Return QCSE questions with this tag, created in the window, with an accepted answer."""
    rows, page = [], 1
    while True:
        params = {
            "site": "quantumcomputing", "tagged": tag, "accepted": "True",
            "fromdate": int(START.timestamp()), "todate": int(END.timestamp()),
            "sort": "creation", "order": "asc", "pagesize": 100, "page": page,
        }
        url = "https://api.stackexchange.com/2.3/search/advanced?" + urllib.parse.urlencode(params)
        with urllib.request.urlopen(url) as resp:
            raw = resp.read()
            if resp.headers.get("Content-Encoding") == "gzip":
                raw = gzip.decompress(raw)
        data = json.loads(raw)
        if "error_id" in data:
            sys.exit(f"Stack Exchange API error for tag {tag}: {data}")
        for it in data["items"]:
            rows.append({
                "source": "A1", "where": "QCSE", "id": str(it["question_id"]),
                "url": it["link"], "title": html.unescape(it["title"]),
                "created": datetime.fromtimestamp(it["creation_date"], timezone.utc).strftime("%Y-%m-%d"),
            })
        time.sleep(max(1, data.get("backoff", 0)))
        if not data.get("has_more"):
            return rows
        page += 1


def fetch_github(query):
    """Return GitHub issues matching a search query (via the logged-in gh CLI)."""
    cmd = ["gh", "api", "-X", "GET", "search/issues", "--paginate",
           "-f", "per_page=100", "-f", f"q={query}",
           "--jq", ".items[] | {number, title, html_url, created_at}"]
    out = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    if out.returncode != 0:
        sys.exit(f"gh failed for query {query!r}:\n{out.stderr}")
    time.sleep(3)  # stay under GitHub's search rate limit
    return [json.loads(line) for line in out.stdout.splitlines() if line.strip()]


def build_pool():
    if POOL_FILE.exists():
        sys.exit(f"{POOL_FILE} already exists; the pool is built only once. Not overwriting.")

    pool = {}

    # A1: union over tags, one row per question.
    for tag in QCSE_TAGS:
        found = fetch_qcse(tag)
        print(f"A1 tag {tag}: {len(found)}")
        for r in found:
            pool.setdefault(("A1", r["id"]), r)

    # A2: union of "closed as not planned" and the per-repository labels, one row per issue.
    window = f"is:issue is:closed created:{START:%Y-%m-%d}..{END:%Y-%m-%d}"
    for repo, labels in A2_LABELS.items():
        queries = [f'repo:{repo} {window} reason:"not planned"']
        if labels:
            queries.append(f"repo:{repo} {window} label:{labels}")
        n_before = sum(1 for k in pool if k[0] == "A2")
        for q in queries:
            for it in fetch_github(q):
                key = ("A2", f"{repo}#{it['number']}")
                pool.setdefault(key, {
                    "source": "A2", "where": repo, "id": str(it["number"]),
                    "url": it["html_url"], "title": it["title"], "created": it["created_at"][:10],
                })
        print(f"A2 {repo}: {sum(1 for k in pool if k[0] == 'A2') - n_before}")

    # Sort into a fixed order first, so the shuffle does not depend on API return order.
    rows = sorted(pool.values(), key=lambda r: (r["source"], r["where"], int(r["id"])))
    random.Random(SEED).shuffle(rows)

    retrieved = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    fields = ["order", "source", "where", "id", "url", "title", "created", "retrieved"] + DECISION_COLUMNS
    with POOL_FILE.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for i, r in enumerate(rows, start=1):
            w.writerow({"order": i, **r, "retrieved": retrieved, **{c: "" for c in DECISION_COLUMNS}})

    n1 = sum(r["source"] == "A1" for r in rows)
    print(f"Pool: A1={n1}  A2={len(rows) - n1}  total={len(rows)}  seed={SEED}  retrieved={retrieved}")
    print(f"Wrote {POOL_FILE}")


def read_pool():
    with POOL_FILE.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return reader.fieldnames, list(reader)


def write_pool(fields, rows):
    with POOL_FILE.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def se_get(path, **params):
    """Call the Stack Exchange API and return the decoded JSON."""
    params = {"site": "quantumcomputing", "filter": "withbody", **params}
    url = f"https://api.stackexchange.com/2.3/{path}?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url) as resp:
        raw = resp.read()
        if resp.headers.get("Content-Encoding") == "gzip":
            raw = gzip.decompress(raw)
    return json.loads(raw)


def html_to_text(s):
    """Rough HTML-to-text, keeping code blocks and line breaks readable."""
    s = re.sub(r"<pre[^>]*>", "\n```\n", s)
    s = re.sub(r"</pre>", "\n```\n", s)
    s = re.sub(r"<br\s*/?>|</p>|</li>|</h\d>", "\n", s)
    s = re.sub(r"<[^>]+>", "", s)
    return re.sub(r"\n{3,}", "\n\n", html.unescape(s)).strip()


def show_next():
    _, rows = read_pool()
    n_yes = sum(r["eligible"] == "yes" for r in rows)
    if n_yes >= TARGET:
        print(f"Target reached: {n_yes} eligible bugs. Screening is finished.")
        return
    r = next((r for r in rows if r["eligible"] == ""), None)
    if r is None:
        print(f"Pool exhausted with {n_yes} eligible bugs (target {TARGET}).")
        return
    print(f"=== Candidate order {r['order']}  |  {r['source']}  |  {r['where']}  |  created {r['created']}")
    print(f"=== Screened so far: {sum(x['eligible'] != '' for x in rows)}  |  eligible so far: {n_yes}/{TARGET}")
    print(f"=== {r['url']}\n")
    if r["source"] == "A1":
        q = se_get(f"questions/{r['id']}")["items"][0]
        print("TITLE:", html.unescape(q["title"]))
        print("TAGS:", ", ".join(q["tags"]))
        print("\n--- QUESTION ---\n" + html_to_text(q["body"]))
        aid = q.get("accepted_answer_id")
        if aid:
            a = se_get(f"answers/{aid}")["items"][0]
            print(f"\n--- ACCEPTED ANSWER (id {aid}) ---\n" + html_to_text(a["body"]))
        else:
            print("\n--- No accepted answer now (it may have been un-accepted after retrieval) ---")
    else:
        meta = subprocess.run(
            ["gh", "issue", "view", r["id"], "-R", r["where"], "--json", "stateReason,labels",
             "--jq", '"CLOSED AS: \\(.stateReason)   LABELS: \\([.labels[].name] | join(", "))"'],
            capture_output=True, text=True, encoding="utf-8")
        print(meta.stdout.strip() or meta.stderr.strip())
        # Without --comments, gh prints the title, metadata and the issue text;
        # with --comments it prints only the comments. Both are needed.
        for extra, heading in (([], "--- ISSUE ---"), (["--comments"], "--- COMMENTS ---")):
            out = subprocess.run(["gh", "issue", "view", r["id"], "-R", r["where"], *extra],
                                 capture_output=True, text=True, encoding="utf-8")
            print(f"\n{heading}\n" + (out.stdout.strip() or out.stderr.strip()))


def decide(order, eligible, families, note):
    if eligible not in ("yes", "no"):
        sys.exit("eligible must be 'yes' or 'no'")
    fams = [x.strip() for x in families.split(";") if x.strip()]
    if eligible == "yes":
        if not fams:
            sys.exit("An eligible bug needs at least one family (or 'no fitting family').")
        unknown = [x for x in fams if x not in ALL_LABELS]
        if unknown:
            sys.exit(f"Not one of the 56 family names: {unknown}")
        if NO_FIT in fams and len(fams) > 1:
            sys.exit("'no fitting family' cannot be combined with other families.")
    elif fams:
        sys.exit("A non-eligible candidate gets no families; put the reason in the note.")
    fields, rows = read_pool()
    r = next((x for x in rows if x["order"] == str(order)), None)
    if r is None:
        sys.exit(f"No candidate with order {order}.")
    if r["eligible"]:
        sys.exit(f"Order {order} already decided ({r['eligible']}); not overwriting.")
    first_open = next((x for x in rows if x["eligible"] == ""), None)
    if first_open is not r:
        sys.exit(f"Screen in seeded order: the next candidate is order {first_open['order']}.")
    r["eligible"], r["families"], r["decision_note"] = eligible, "; ".join(fams), note
    write_pool(fields, rows)
    print(f"Recorded order {order}: eligible={eligible} families={r['families'] or '-'}")


def score():
    """Result (a): k/N eligible bugs with at least one of the 20 mutation-supported families,
    for A1, A2 and pooled, next to the paper's 23/410 (README Section 2.2, Result (a))."""
    _, rows = read_pool()
    open_ = [r["order"] for r in rows if r["eligible"] == ""]
    if open_:
        sys.exit(f"{len(open_)} candidates not decided yet (first: order {open_[0]}).")
    elig = [r for r in rows if r["eligible"] == "yes"]
    mut = set(MUTATION_FAMILIES)

    def fams(r):
        return [x.strip() for x in r["families"].split(";") if x.strip()]

    def hit(r):
        return any(f in mut for f in fams(r))

    print(f"Screened: {len(rows)}  eligible: {len(elig)}\n")
    print("Result (a): bugs with >= 1 mutation-supported family")
    for name, group in (("A1", [r for r in elig if r["source"] == "A1"]),
                        ("A2", [r for r in elig if r["source"] == "A2"]),
                        ("pooled", elig)):
        k, n = sum(hit(r) for r in group), len(group)
        pct = f"{100 * k / n:.1f}%" if n else "n/a"
        print(f"  {name:7s} k/N = {k}/{n} = {pct}")
    print("  paper   23/410 = 5.6%\n")

    print("Bugs counted in k (order, source, families):")
    for r in elig:
        if hit(r):
            print(f"  {r['order']:>4} {r['source']}  {r['families']}")

    print("\nFamilies used by eligible bugs (M = one of the 20 mutation-supported families):")
    counts = {}
    for r in elig:
        for f in fams(r):
            counts[f] = counts.get(f, 0) + 1
    for f in sorted(counts, key=lambda x: (-counts[x], x)):
        print(f"  {'M' if f in mut else '-'}  {counts[f]:>3}  {f}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")  # Windows consoles default to cp1252
    args = sys.argv[1:]
    if args == ["pool"]:
        build_pool()
    elif args == ["show"]:
        show_next()
    elif args == ["score"]:
        score()
    elif len(args) == 5 and args[0] == "decide":
        decide(args[1], args[2], args[3], args[4])
    else:
        sys.exit(__doc__)
