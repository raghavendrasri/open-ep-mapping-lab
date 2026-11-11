"""m43 equation tests: TF-IDF weights, cosine retrieval, the Wilson interval and the number of
questions an evaluation needs; and the offline evaluation harness with its scripted stand-in model."""

import math

import numpy as np
import pytest
import sympy as sp

from epml import retrieval as rt


def test_tokenize_plural_rule_and_stop_words():
    assert rt.tokenize("The electrograms of the atria") == ["electrogram", "atria"]
    assert rt.tokenize("Arrhythmias, loss, and AF") == ["arrhythmia", "loss", "af"]


def test_idf_and_tfidf_by_hand():
    """eq-m43-tfidf on a three-document corpus computed by hand."""
    docs = [["scar", "voltage"], ["scar", "scar", "map"], ["map"]]
    vocab, idf = rt.idf_weights(docs)
    assert vocab == ["map", "scar", "voltage"]
    expect = [math.log(4 / 3) + 1, math.log(4 / 3) + 1, math.log(4 / 2) + 1]
    assert np.allclose(idf, expect)
    W = rt.tfidf_matrix(docs, vocab, idf)
    row = np.array([1 * idf[0], 2 * idf[1], 0.0])
    assert np.allclose(W[1], row / np.linalg.norm(row))
    assert np.allclose(np.linalg.norm(W, axis=1), 1)
    # a word in every document gets the smallest weight; one in a single document the largest
    assert idf.argmax() == 2


def test_cosine_properties():
    """eq-m43-cosine: scale invariant, symmetric, between -1 and 1, and 1 for parallel vectors."""
    rng = np.random.default_rng(0)
    a, b = rng.normal(size=5), rng.normal(size=5)
    assert rt.cosine(a, b) == pytest.approx(rt.cosine(3 * a, 0.5 * b))
    assert rt.cosine(a, b) == pytest.approx(rt.cosine(b, a))
    assert -1 <= rt.cosine(a, b) <= 1 and rt.cosine(a, 2 * a) == pytest.approx(1)
    assert rt.cosine(a, np.zeros(5)) == 0.0


def test_index_finds_an_exact_definition_first():
    idx = rt.Index([("a", "conduction velocity of the wavefront"), ("b", "scar and low voltage"),
                    ("c", "voltage of the unipolar electrogram")])
    assert idx.search("low voltage scar", k=1)[0][0] == "b"
    assert [d for d, _ in idx.search("unipolar voltage", k=2)] == ["c", "b"]


def test_ranking_metrics():
    ranked = [["x", "y", "z"], ["y", "z", "x"], ["z", "x", "y"]]
    gold = [{"x"}, {"x"}, {"q"}]
    assert rt.recall_at_k(ranked, gold, 1) == pytest.approx(1 / 3)
    assert rt.recall_at_k(ranked, gold, 3) == pytest.approx(2 / 3)
    assert rt.mean_reciprocal_rank(ranked, gold) == pytest.approx((1 + 1 / 3 + 0) / 3)


def test_course_corpus_and_questions_are_consistent():
    """Every gold answer of the lab's question set is a glossary term, and the corpus holds both
    glossary entries and formula-sheet items."""
    terms = {g["term"] for g in rt.parse_glossary()}
    assert all(t in terms for _, gold in rt.QUESTIONS for t in gold)
    ids = [d for d, _ in rt.course_corpus()]
    assert any(i.startswith("glossary:") for i in ids) and any(i.startswith("formula:") for i in ids)
    assert len(rt.QUESTIONS) >= 20


def test_wilson_interval_solves_the_score_equation():
    """eq-m43-wilson: the bounds are the two roots in p of (k/n - p)^2 = z^2 p (1 - p) / n (SymPy),
    and they match the numbers for 57 of 100."""
    p, ph, n, z = sp.symbols("p phat n z", positive=True)
    roots = sp.solve(sp.Eq((ph - p) ** 2, z**2 * p * (1 - p) / n), p)
    vals = {ph: sp.Rational(57, 100), n: 100, z: sp.Float(1.959963984540054)}
    lo, hi = sorted(float(r.subs(vals)) for r in roots)
    assert rt.wilson_interval(57, 100) == pytest.approx((lo, hi), abs=1e-12)
    a, b = rt.wilson_interval(0, 20)
    assert a == 0.0 and 0 < b < 0.2          # zero successes still give an upper bound
    a, b = rt.wilson_interval(19, 150)
    assert a < 19 / 150 < b


def test_questions_needed_gives_the_half_width():
    """eq-m43-questions: at that many questions the Wilson half-width is close to the target."""
    for p, h in [(0.5, 0.05), (0.7, 0.1), (0.9, 0.05)]:
        n = rt.questions_needed(p, h)
        lo, hi = rt.wilson_interval(round(p * n), n)
        assert (hi - lo) / 2 == pytest.approx(h, rel=0.08)
    assert rt.questions_needed(0.5, 0.05) == 385


def test_citation_check():
    keys = {"vaswani2017"}
    assert rt.citation_resolves("vaswani2017", keys)
    assert rt.citation_resolves("m43", keys)
    assert not rt.citation_resolves("m99", keys) and not rt.citation_resolves("smith2021ecg", keys)


def test_harness_detects_planted_faults():
    """The harness finds what was planted in the scripted stand-in: invented citations, answers that
    change between runs, and a deterministic retriever that is fully consistent."""
    glossary = rt.parse_glossary()
    idx = rt.Index(rt.course_corpus())
    keys = rt.bib_keys()
    closed = rt.ScriptedModel("closed_book", idx, glossary, error_rate=0.3,
                              cited_keys=["vaswani2017", "smith2021ecg"], seed=1)
    r = rt.evaluate(closed, keys=keys)
    assert 0 < r["citations_valid"] < 1 and r["all_runs_agree"] < 1
    rag = rt.ScriptedModel("retrieval", idx, glossary, temperature=0.0, seed=1)
    r2 = rt.evaluate(rag, keys=keys)
    assert r2["all_runs_agree"] == 1.0 and r2["citations_valid"] == 1.0
    assert r2["ci"][0] <= r2["accuracy"] <= r2["ci"][1]
