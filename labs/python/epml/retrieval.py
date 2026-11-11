"""m43 · Retrieval over course text and an offline harness for evaluating language-model answers.

Every function here implements one numbered equation of module m43 or a step of its code lab, and
is checked in tests/test_m43_retrieval.py. Nothing here calls an external AI service: the
"model" in the evaluation harness is a scripted stand-in (CLAUDE.md, Part VII rules).
"""

import math
import re
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]

# A short English stop-word list (our own); words that carry no topic.
STOP = set("""
a an and are as at be by can does do for from has have how in into is it its of on or that the
their them they this to was what when where which while who why will with without you your than
then there these those also each one two not no more most much many very same other another
""".split())


def tokenize(text):
    """Lower-case words of letters and digits, without stop words. A crude plural rule makes
    'electrograms' match 'electrogram': -ies -> -y, and a final -s is dropped from words longer
    than three letters (but not from -ss)."""
    out = []
    for w in re.findall(r"[a-z0-9]+", text.lower()):
        if w in STOP:
            continue
        if len(w) > 4 and w.endswith("ies"):
            w = w[:-3] + "y"
        elif len(w) > 3 and w.endswith("s") and not w.endswith("ss"):
            w = w[:-1]
        out.append(w)
    return out


# ---------------------------------------------------------------------------------------------
# TF-IDF and cosine retrieval (eq-m43-tfidf, eq-m43-cosine)


def idf_weights(docs_tokens):
    """eq-m43-tfidf, second factor: idf_t = ln((1 + N) / (1 + df_t)) + 1 (the 'smooth' form).
    Returns (sorted vocabulary, idf array)."""
    n = len(docs_tokens)
    df = {}
    for toks in docs_tokens:
        for t in set(toks):
            df[t] = df.get(t, 0) + 1
    vocab = sorted(df)
    idf = np.array([math.log((1 + n) / (1 + df[t])) + 1 for t in vocab])
    return vocab, idf


def tfidf_matrix(docs_tokens, vocab, idf):
    """eq-m43-tfidf: w_td = tf_td * idf_t (tf = raw count), rows scaled to unit length."""
    index = {t: j for j, t in enumerate(vocab)}
    W = np.zeros((len(docs_tokens), len(vocab)))
    for i, toks in enumerate(docs_tokens):
        for t in toks:
            j = index.get(t)
            if j is not None:
                W[i, j] += 1.0
    W *= idf
    norms = np.linalg.norm(W, axis=1, keepdims=True)
    return np.divide(W, norms, out=np.zeros_like(W), where=norms > 0)


def cosine(a, b):
    """eq-m43-cosine: a.b / (|a| |b|); 0 if either vector is zero."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    return 0.0 if na == 0 or nb == 0 else float(a @ b / (na * nb))


class Index:
    """A TF-IDF index over a list of (id, text) documents."""

    def __init__(self, docs):
        self.ids = [d[0] for d in docs]
        self.texts = [d[1] for d in docs]
        toks = [tokenize(t) for t in self.texts]
        self.vocab, self.idf = idf_weights(toks)
        self.W = tfidf_matrix(toks, self.vocab, self.idf)

    def query_vector(self, text):
        return tfidf_matrix([tokenize(text)], self.vocab, self.idf)[0]

    def search(self, text, k=5):
        """Top-k (id, cosine score) for a query, highest first; ties keep document order."""
        scores = self.W @ self.query_vector(text)
        order = np.argsort(-scores, kind="stable")[:k]
        return [(self.ids[i], float(scores[i])) for i in order]


def recall_at_k(ranked_ids, gold, k):
    """Share of queries whose top k contain at least one gold id. gold: list of sets."""
    return float(np.mean([bool(set(r[:k]) & set(g)) for r, g in zip(ranked_ids, gold)]))


def mean_reciprocal_rank(ranked_ids, gold):
    """Mean of 1 / (rank of the first gold id), counting 0 when none is retrieved."""
    rr = []
    for r, g in zip(ranked_ids, gold):
        hits = [i for i, d in enumerate(r) if d in g]
        rr.append(1.0 / (hits[0] + 1) if hits else 0.0)
    return float(np.mean(rr))


# ---------------------------------------------------------------------------------------------
# Course text as a corpus


def parse_glossary(path=None):
    """Glossary entries as dicts: term, definition (without the module links) and module ids."""
    path = Path(path) if path else ROOT / "glossary" / "index.qmd"
    lines = path.read_text().splitlines()
    out = []
    for i, line in enumerate(lines):
        if line.startswith(": ") and i > 0 and lines[i - 1].strip():
            text = line[2:]
            mods = re.findall(r"\[(m\d\d)\]\(", text)
            definition = re.sub(r"\s*\[m\d\d\]\([^)]*\)", "", text).strip()
            out.append({"term": lines[i - 1].strip(), "definition": definition, "modules": mods})
    return out


def parse_formula_sheet(path=None):
    """Formula-sheet items as dicts: title, module heading and equation label."""
    path = Path(path) if path else ROOT / "formula-sheet" / "index.qmd"
    heading, out = "", []
    for line in path.read_text().splitlines():
        if line.startswith("## "):
            heading = line[3:].strip()
        m = re.match(r"^\*\*(.+?)\*\* \(\[derivation\]\(\.\./modules/[^#]+#(eq-[a-z0-9-]+)\)\)", line)
        if m:
            out.append({"title": m.group(1), "module": heading, "label": m.group(2)})
    return out


def course_corpus():
    """Documents for retrieval: one per glossary entry (id 'glossary:<term>') and one per
    formula-sheet item (id 'formula:<label>')."""
    docs = [(f"glossary:{g['term']}", f"{g['term']}. {g['definition']}") for g in parse_glossary()]
    docs += [(f"formula:{f['label']}", f"{f['title']}. {f['module']}") for f in parse_formula_sheet()]
    return docs


# Plain-language questions written for this course, each with the glossary entries that answer it.
QUESTIONS = [
    ("Why does a bipolar signal change with the direction the wave travels?", ["Bipolar electrogram"]),
    ("At what moment is the tissue under the electrode excited?", ["Local activation time"]),
    ("How fast does the activation front move through the tissue?", ["Conduction velocity"]),
    ("Which score measures the overlap of a predicted and a true mask?",
     ["Dice coefficient", "Jaccard index"]),
    ("A deflection recorded from tissue that is not under the electrode", ["Far-field signal"]),
    ("A network pretrained once on unlabeled data and reused for many tasks", ["Foundation model"]),
    ("Learning without labels by making a task out of the data themselves",
     ["Self-supervised learning", "Contrastive learning"]),
    ("Pull two views of the same patient together and push other patients apart",
     ["Contrastive learning"]),
    ("Train only a logistic regression on top of frozen pretrained features", ["Linear probe"]),
    ("A language model states a fact or a reference that does not exist", ["Hallucination"]),
    ("Give the model passages found in a document collection before it answers",
     ["Retrieval-augmented generation (RAG)"]),
    ("Weight a word more when few documents contain it", ["TF-IDF"]),
    ("The pieces of text that a language model reads and writes", ["Token"]),
    ("Testing a model on patients from a different hospital", ["External validation"]),
    ("The patients at deployment differ from the patients used for training", ["Dataset shift"]),
    ("Optical pulse sensor in a smartwatch", ["Photoplethysmography (PPG)"]),
    ("Small device under the skin that records the heart rhythm for years",
     ["Implantable loop recorder (ILR)"]),
    ("Uncertainty from the spread of several models trained differently", ["Ensemble"]),
    ("Choose the next pacing site with a probabilistic model of the match",
     ["Bayesian optimization", "Expected improvement", "Gaussian process", "Pace mapping"]),
    ("A neural network whose loss includes the residual of a differential equation",
     ["Physics-informed neural network (PINN)"]),
    ("Worst-case distance between two surfaces", ["Hausdorff distance"]),
    ("A fast model that imitates an expensive simulation", ["Surrogate model"]),
    ("Training at several hospitals without moving the patient data", ["Federated learning"]),
    ("Irregular fast rhythm of the upper chambers", ["Atrial fibrillation (AF)"]),
]


# ---------------------------------------------------------------------------------------------
# Evaluating answers (eq-m43-wilson, eq-m43-questions)


def wilson_interval(k, n, z=1.959963984540054):
    """eq-m43-wilson: the Wilson score interval for k successes in n independent trials."""
    if n == 0:
        return 0.0, 1.0
    p = k / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z / (1 + z * z / n) * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return max(0.0, centre - half), min(1.0, centre + half)


def questions_needed(p, half_width, z=1.959963984540054):
    """eq-m43-questions: n = z^2 p (1 - p) / h^2 independent questions give an interval of half-width
    about h (normal approximation), rounded up."""
    return int(math.ceil(z * z * p * (1 - p) / half_width**2))


def bib_keys(path=None):
    path = Path(path) if path else ROOT / "references.bib"
    return set(re.findall(r"^@\w+\{([^,]+),", path.read_text(), re.M))


def citation_resolves(citation, keys=None):
    """A citation is valid if it is a key in references.bib or an existing course module id."""
    keys = bib_keys() if keys is None else keys
    if citation in keys:
        return True
    if re.fullmatch(r"m\d\d", citation or ""):
        return any((ROOT / "modules").glob(f"{citation}-*.qmd"))
    return False


class ScriptedModel:
    """A deterministic stand-in for a language model, used to test the evaluation harness offline.

    mode="closed_book": answers from the answer key but gives another glossary term with probability
    error_rate on each call, and cites one of `cited_keys`, of which some may be invented
    (both rates are set by the lab, so the harness can be checked against faults we planted).
    mode="retrieval": retrieves the top k glossary entries, picks one with probability proportional
    to exp(score / temperature) (temperature 0 means always the top one), and cites the first module
    listed for that entry."""

    def __init__(self, mode, index, glossary, error_rate=0.3, cited_keys=("vaswani2017",),
                 k=3, temperature=0.0, seed=0):
        self.mode, self.index, self.k, self.temperature = mode, index, k, temperature
        self.error_rate, self.cited_keys = error_rate, list(cited_keys)
        self.terms = [g["term"] for g in glossary]
        self.module_of = {g["term"]: (g["modules"][0] if g["modules"] else "") for g in glossary}
        self.rng = np.random.default_rng(seed)

    def answer(self, question, gold=None):
        if self.mode == "closed_book":
            term = gold[0]
            if self.rng.random() < self.error_rate:
                term = self.rng.choice([t for t in self.terms if t not in gold])
            return {"answer": str(term), "citation": str(self.rng.choice(self.cited_keys))}
        if self.mode == "retrieval":
            hits = [(i.split(":", 1)[1], s) for i, s in self.index.search(question, k=50)
                    if i.startswith("glossary:")][: self.k]
            if self.temperature <= 0:
                term = hits[0][0]
            else:
                s = np.array([h[1] for h in hits]) / self.temperature
                p = np.exp(s - s.max())
                term = hits[self.rng.choice(len(hits), p=p / p.sum())][0]
            return {"answer": term, "citation": self.module_of[term]}
        raise ValueError(self.mode)


def evaluate(model, questions=QUESTIONS, repeats=3, keys=None):
    """Ask every question `repeats` times. Returns accuracy of the first run with its Wilson interval,
    the share of questions answered identically in all runs, Cohen's kappa between runs 1 and 2 on
    the answers, and the share of citations that resolve."""
    from .ml import cohen_kappa

    keys = bib_keys() if keys is None else keys
    runs = []
    for _ in range(repeats):
        runs.append([model.answer(q, g) for q, g in questions])
    correct = [a["answer"] in g for a, (_, g) in zip(runs[0], questions)]
    k, n = int(sum(correct)), len(questions)
    answers = [[a["answer"] for a in run] for run in runs]
    same = np.mean([len({run[i] for run in answers}) == 1 for i in range(n)])
    cites = [a["citation"] for run in runs for a in run]
    return {
        "accuracy": k / n,
        "ci": wilson_interval(k, n),
        "all_runs_agree": float(same),
        "kappa_runs_1_2": float(cohen_kappa(answers[0], answers[1])) if repeats > 1 else float("nan"),
        "citations_valid": float(np.mean([citation_resolves(c, keys) for c in cites])),
    }
