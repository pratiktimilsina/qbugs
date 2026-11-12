# Separating Program-Level and Platform-Level Fault Representation

**References**

- **Primary study** (referred to as "the paper"): Saad, A. M., Sabit, A. A., Brandenburgh, J.,
  Wang, J., Zhang, Q., & Hossain, S. B. (2026). *Are we testing the wrong quantum bugs?
  A study of fault representation gaps in quantum software testing.*
  [arXiv:2610.22089](https://arxiv.org/abs/2610.22089)
- **Platform-level fault model:** Nasir, F., Shah, A., & Alam, I. (2026).
  *Fault-class-matched test oracles for output-invisible quantum transpiler regressions.*
  [arXiv:2609.24230](https://arxiv.org/abs/2609.24230)

## Summary

The paper's 23/410 (5.6%) combines two questions. Here they are measured separately,
with the paper's own taxonomy and family-level measure:
- **(a) Program level.** Of 42 eligible bugs in user quantum programs, 9 (21.4%) were assigned at
  least one of the 20 mutation-supported families. The other 33 (78.6%) fall outside them.
- **(b) Platform level.** One qualifying platform-level fault model was identified (Nasir et al., 2026).
  Two of its three fault classes were mapped to taxonomy families, and those two families occur in
  15 of the paper's 410 platform bugs (3.7%). This is a family-level overlap. It does not show that
  the fault model can reproduce any of those 15 bugs.

## 1. Issue and Improvement

> Issue: The mutation tools and the real bugs target different software. As §4.3 itself explains,
> the mutation tools change the program under test, while all 410 bugs come from platform
> repositories. §1 motivates the study with how techniques such as Quito, QuSBT and MutTG
> are evaluated, and these techniques test quantum programs, so it is not clear what platform bugs
> show about those evaluations. The low overlap, with only 23 of 410 bugs (5.6%) in a
> mutation-supported family, is therefore hard to interpret because it combines two questions:
> whether mutants match recent bugs in user quantum programs, which the paper does not measure,
> and whether fault models exist for the platforms themselves.

> Improvement: compare program mutants with bugs in user quantum programs, and platform bugs with
> platform-level fault models.

## 2. Method

### 2.1 Common to both halves

- **Measure:** the same bug-level measure as the paper: (bugs with at least one assigned family in
  the target family set) / (all eligible bugs in the corpus). The corpus is the 42 eligible
  user-program bugs in half (a) and the paper's 410 platform bugs in half (b).
- **Taxonomy:** the paper's 56 families and definitions. Items that fit none of the 56 families
  are recorded as **"no fitting family"** and counted as not represented. No additional families
  are introduced.
- **Window:** bugs (QCSE questions and GitHub issues) created July 24, 2024 – July 23, 2026, the
  same window as the paper. The window does not apply to fault models ([Section 2.3](#23-half-b-platform-bugs-vs-platform-level-fault-models)).
- **Results:** each half is reported alongside the paper's 23/410 (5.6%) result.

### 2.2 Half (a): program mutants vs bugs in user quantum programs

**Definition: user quantum program.** Code that uses a quantum SDK to build or run circuits for
an algorithm, application, tutorial or demo. It is not itself part of an SDK, compiler, simulator
or execution service.

**Candidate sources.** Unlike the paper's corpus of platform issues, half (a) draws on two sources
of user-program bugs. Quantum Computing Stack Exchange (QCSE) was chosen over repositories of
vendor demos and tutorials because one such repository (Qiskit/documentation, 1,109 closed issues
in the window) would have dominated the pool.

- **Source A1: QCSE questions.** A candidate is a question on quantumcomputing.stackexchange.com
  that meets all of these:
  - It was created in the window (UTC).
  - It has an accepted answer.
  - It carries at least one of these tags: `qiskit`, `qiskit-runtime`, `cirq`, `pyquil`,
    `rigetti`, `pennylane`, `pytket`, `amazon-braket`, `qutip`, `qasm`, `programming`.

  `qasm2circ` is excluded because it is not one of the ten platforms. CUDA-Q and Mitiq have no
  QCSE tag.
- **Source A2: user-error issues in the paper's ten platform repositories.** A candidate is an
  issue that was created in the window, is closed, and meets at least one of these:
  - It was closed as "not planned".
  - It carries one of these labels:
    - Cirq: `kind/question`, `triage/works-as-expected`
    - PennyLane: `question :question:`
    - TKET: `invalid`, `question`
    - Amazon Braket: `invalid`, `question`
    - QuTiP: `invalid`
    - OpenQASM: `invalid`, `question`

  The labels `duplicate`, `wontfix` and `user experience` are not used. Qiskit, PyQuil, CUDA-Q
  and Mitiq have no user-error label, so for them only "not planned" applies. These candidates
  come from the same projects and period as the paper's corpus. The eligibility screening below
  determines whether they concern faults in user programs rather than faults in the platform.

**Eligibility.** Every eligible bug was confirmed by the author as a fault in user program code.
Because user-program bugs have no platform fix, the evidence is an accepted answer or a
maintainer's conclusion, rather than the merged fix or maintainer acceptance required by the paper.
- **A1 (QCSE):** the question shows the asker's own program code, and the program misbehaves. The
  accepted answer identifies a mistake in that code as the cause.
- **A2:** a maintainer states, or the closing reason shows, that the fault is in the reporter's
  code. The issue shows enough of the reporter's code and the explanation to identify the faulty
  mechanism.
- **Excluded from both:** feature requests, conceptual or usage questions without faulty code,
  installation or environment-only problems, duplicates, and cases where the answer or maintainer
  says the platform was at fault.

**Screening.** All 218 candidates (126 from A1, 92 from A2) were screened.

**Classification.** Each eligible bug was assigned one or more of the 56 families, or "no fitting
family", by the author.

**Baseline.** Quito, QuSBT and MutTG were evaluated using manually inserted faults in quantum
programs, rather than faults generated by the four mutation tools audited in the paper. Half (a)
uses the same 20 mutation-supported families as the paper, asking the same question as its 23/410
result using user-program bugs instead of platform bugs. The comparison is at the family level and
does not reproduce those manually inserted faults.

**Result (a).** k / N bugs with at least one family among the 20 mutation-supported families
(Saad et al., 2026, Table 4), reported separately for A1, for A2 and for the pooled sample, next to
23/410 (5.6%).

### 2.3 Half (b): platform bugs vs platform-level fault models

**Inclusion rule for a platform-level fault model.**
- It is published work (peer-reviewed or arXiv).
- It targets quantum platform software: compilers or transpilers, IR and serialization,
  simulators, SDK internals, or execution services.
- It gives an explicit, inspectable list of fault or mutation classes, as Saad et al. (2026,
  Table 4) do for mutation operators.
- Testing oracles that define no fault classes do not qualify. QDiff, MorphQ and QASMInfer are
  examples.

The fault classes must describe faults in the platform software itself. Tools that only mutate
the input circuits given to a compiler or simulator (fuzzers, metamorphic testers) are
program-level and do not qualify. Empirical bug taxonomies are not fault models, although a
fault-injection tool built from one would qualify. No date limit applies, and a fault model may
target any quantum platform software, not only the paper's ten platforms.

One qualifying platform-level fault model was identified (Nasir et al., 2026). It defines three
classes of faults in the transpiler itself (Nasir et al., 2026, §2.3): **contract/metadata**,
**global-phase** and **determinism**. Its mutant families (Nasir et al., 2026, §5.3) are injected
into the compiler's output and metadata, not into input circuits.

**Mapping.** Each fault class is mapped to one of the 56 families "by the primary fault it
introduces", the same rule as the paper (Saad et al., 2026, §3.2, Step 1). A class with no
fitting family is recorded as "no fitting family". The family for each class was decided by the
author before result (b) was computed. Class definitions are quoted from Nasir et al. (2026, §2.3),
and family definitions from the `Taxonomy` sheet.

| Class | Assigned family | Mutation-supported? | Mapping assessment |
|---|---|---|---|
| Contract/metadata | *Measurement ordering error* | no | Strong alternative: *Wrong qubit target* |
| Global-phase | *Missing field set* | no | Direct for dropping; borderline for double-counting |
| Determinism | no fitting family | — | No family describes run-to-run non-determinism |

**Contract/metadata.** Class definition: "corrupts the recorded layout or permutation metadata
(TranspileLayout, final index layout, routing permutation) without touching the executed circuit".
Assigned family: *Measurement ordering error*: "Measurements, wire assignments or classical
dependencies are ordered differently from what the algorithm or convention requires."

The primary fault is a wire assignment recorded in the wrong order: Nasir et al.'s mutants swap,
rotate or reverse the recorded permutation, which is the "wire assignments … ordered differently"
case of the definition. Consistent with half (a), order 108 in `pool_a.csv`, where index bookkeeping
against the ordering convention was ruled *Measurement ordering error*. **Strong alternative: *Wrong
qubit target*:** "An operation acts on, or is mapped to, a different qubit or wire than intended."
Its "or is mapped to" wording can be read as covering this class, since the corrupted metadata is a
record of how qubits are mapped. It was rejected on an **interpretation**: "mapped to" is read as an
operation or wire actually being mapped to the wrong qubit, not as an inaccurate record of a mapping
that was carried out correctly. Here the executed circuit is untouched, so every operation still
acts on its intended qubit, and only the recorded layout or permutation is reordered. The definition
does not settle this unambiguously.

**Global-phase.** Class definition: "drops or doublecounts a global phase that a standard
output-equivalence check normalizes away by construction". Assigned family: *Missing field set*: "An
object attribute (phase, name, tags, metadata) is not set or not propagated when the object is
created, converted or rebuilt."

The class has two cases, and both are a fault in carrying the circuit's phase attribute through the
transpiler's rebuild of the circuit. **Dropping** fits the definition directly: the definition names
phase, and a dropped phase is not propagated. **Double-counting** fits only loosely: the phase is
propagated, but with a wrong value, which is not literally "not set or not propagated". The mapping
is therefore **borderline** for the double-counting case. It was kept because the definition names
the attribute concerned (phase) and the step at fault (propagation when the object is rebuilt),
which describes the class's primary fault better than the other families considered. Not *Perturbed
parameter*: the global phase belongs to the circuit, not to a gate's parameter.

**Determinism.** Class definition: "makes a fixed-seed, fixed-configuration transpile return a
different compiled representation across runs while the computation actually performed stays
identical". Assigned family: **no fitting family**.

None of the 56 families describes run-to-run non-determinism. *Misplaced gate* requires "changing
the computation"; *Concurrency error* requires shared state across parallel execution.

**Why not *Compiler transformation error* for the contract/metadata and global-phase classes.**
Its definition requires "a semantically wrong or degraded output". The classes of Nasir et al.
(2026, §2.3) are output-invisible by definition, so the output is not wrong.

**Mapped family set:** {*Measurement ordering error*, *Missing field set*}. Neither is one of the
20 mutation-supported families.

**Result (b).** The share of the paper's 410 bugs with at least one assigned family in the mapped
family set, using the paper's own family labels from `quantum_software_bugs.xlsx` with no
reclassification, next to 23/410 (5.6%).

## 3. Results

### 3.1 Half (a): program mutants vs bugs in user quantum programs

| Source | Candidates screened | Eligible (N) | With ≥ 1 mutation-supported family (k) | k / N |
|---|---|---|---|---|
| A1 (QCSE) | 126 | 36 | 9 | 25.0% |
| A2 (user-error issues) | 92 | 6 | 0 | 0.0% |
| **Pooled** | **218** | **42** | **9** | **21.4%** |
| Paper (platform bugs) | | 410 | 23 | 5.6% |

**The nine bugs counted in k** (all A1): 23, 120, 157 (*Wrong qubit target*); 56, 200 (*Wrong
gate*); 68, 101, 177 (*Missing gate*); 97 (*Wrong qubit target*; *Missing gate*). Only three of
the 20 mutation-supported families occur.

**The families used most by eligible bugs** are all outside the 20: *Dependency incompatibility*
(6), *Backend dispatch error* (5), *Incorrect parameters* (5) and *Mathematical formulation error*
(5).

### 3.2 Half (b): platform bugs vs platform-level fault models

As a check, the paper's own family labels reproduce its figure: 23/410 bugs have at least one of
the 20 mutation-supported families.

| Comparison | Family set | Bugs with ≥ 1 family in the set | Share |
|---|---|---|---|
| **Result (b): platform-level fault model** (Nasir et al., 2026; mapping in [Section 2.3](#23-half-b-platform-bugs-vs-platform-level-fault-models)) | *Measurement ordering error*, *Missing field set* | **15 / 410** | **3.7%** |
| Paper: mutation operators (Table 4) | the 20 mutation-supported families | 23 / 410 | 5.6% |

Per family: *Measurement ordering error* 6 bugs, *Missing field set* 9 bugs. The 15 bugs counted
are Q2Y0059, Q2Y0063, Q2Y0064, Q2Y0100, Q2Y0117, Q2Y0159, Q2Y0163, Q2Y0175, Q2Y0185, Q2Y0399,
Q2Y0530, Q2Y0546, Q2Y0561, Q2Y0562 and Q2Y0563.

## 4. What the results show

- **Half (a):** the 20 mutation-supported families account for 9 of 42 eligible user-program bugs
  (21.4%). The remaining 33 bugs (78.6%) fall outside those families. This is not a like-for-like
  counterpart of 23/410: the corpora, the evidence standard and the number of reviewers differ.
- **Half (b):** the two mapped platform-level families occur in 15 of 410 platform bugs (3.7%).
  This is lower than the original 23/410 (5.6%), although the fault model found targets the
  narrower category of output-invisible transpiler regressions.
- **Both halves:** these are family-level comparisons. Membership does not establish that an
  operator or fault model can reproduce a particular bug (Saad et al., 2026, §2.4).

## 5. Limitations

- All eligibility and family-classification decisions were made by one reviewer. The paper used
  two reviewers (κ = 0.78); inter-reviewer agreement was not measured here.
- The source selection for half (a) and the literature search for half (b) were not systematic.
- The 42 eligible bugs give a coarse estimate. A2 has only six eligible bugs, too few for a
  separate estimate.
- A1 and A2 provide weaker evidence than the paper's Tier 1: there is no merged fix, and QCSE
  accepted answers are chosen by askers rather than independently verified. A1 also misses
  questions without the selected tags, while A2 misses user-error issues closed as "completed"
  without a label. QCSE askers may be learners, potentially over-representing beginner mistakes.
- The user programs in half (a) may not represent the benchmark programs used to evaluate Quito,
  QuSBT and MutTG. Therefore, the 21.4% result may not generalize to those benchmarks.
- Half (b) rests on one fault model, an arXiv preprint with no stated venue, identified through a
  non-systematic search. Its class-to-family mapping was decided by one reviewer, with alternative
  or borderline fits for both mapped classes ([Section 2.3](#23-half-b-platform-bugs-vs-platform-level-fault-models)). A companion mutation engine referenced
  in the preprint could not be located.
- The QCSE posts and GitHub issues were not archived. `pool_a.csv` preserves decisions, summaries
  and links, but the original evidence may be edited or deleted. QCSE content is licensed CC BY-SA;
  each question is linked in `pool_a.csv`.

## 6. Reproducibility

**Files.**
- `README.md`: this report.
- `half_a.py`: half (a): builds the candidate pool, shows candidates, records decisions, and
  scores the result.
- `half_b.py`: half (b): checks 23/410 from the paper's labels, then computes result (b).
- `pool_a.csv`: the 218 candidates of half (a), in screening order (shuffled with the fixed seed
  20261110), with every decision, family and note.

**Commands.**
- `python half_a.py pool`: built `pool_a.csv` once, on 2026-11-10, from the live QCSE and GitHub
  APIs (needs the GitHub CLI `gh`). Re-running it today would not give the same pool, so
  `pool_a.csv` is the record; the command refuses to overwrite it.
- `python half_a.py show` and `python half_a.py decide ORDER yes|no "Families" "note"`: the
  screening, one candidate at a time in screening order.
- `python half_a.py score`: result (a).
- `python half_b.py [path/to/quantum_software_bugs.xlsx]`: result (b), after the 23/410 check. The
  path defaults to `../quantum_software_bugs.xlsx` (the folder above this one).

**Data.** `quantum_software_bugs.xlsx` is not included; it is available to reviewers via the
paper's Data-Availability Statement.

## Author

Pratik Timilsina
