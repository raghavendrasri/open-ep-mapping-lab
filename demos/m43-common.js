// m43 · Shared code for the m43 demos: TF-IDF retrieval, as in labs/python/epml/retrieval.py.
// MIT License. tests/test_m43_demos.py checks that these functions give the Python results.

// Lower-case words of letters and digits, without stop words; -ies -> -y, and a final -s is dropped
// from words longer than three letters (but not from -ss). Same rule as epml.retrieval.tokenize.
export function tokenize(text, stop) {
  const out = [];
  for (let w of text.toLowerCase().match(/[a-z0-9]+/g) || []) {
    if (stop.has(w)) continue;
    if (w.length > 4 && w.endsWith("ies")) w = w.slice(0, -3) + "y";
    else if (w.length > 3 && w.endsWith("s") && !w.endsWith("ss")) w = w.slice(0, -1);
    out.push(w);
  }
  return out;
}

// eq-m43-tfidf: idf_t = ln((1 + N) / (1 + df_t)) + 1; w_td = count_td * idf_t; rows to unit length.
export function buildIndex(docs, stopWords) {
  const stop = new Set(stopWords);
  const toks = docs.map((d) => tokenize(d.text, stop));
  const df = new Map();
  for (const t of toks) for (const w of new Set(t)) df.set(w, (df.get(w) || 0) + 1);
  const n = docs.length;
  const idf = new Map([...df].map(([w, c]) => [w, Math.log((1 + n) / (1 + c)) + 1]));
  const rows = toks.map((t) => unitVector(t, idf));
  return { ids: docs.map((d) => d.id), texts: docs.map((d) => d.text), stop, idf, rows };
}

function unitVector(tokens, idf) {
  const v = new Map();
  for (const w of tokens) if (idf.has(w)) v.set(w, (v.get(w) || 0) + idf.get(w));
  let norm = 0;
  for (const x of v.values()) norm += x * x;
  norm = Math.sqrt(norm);
  if (norm > 0) for (const [w, x] of v) v.set(w, x / norm);
  return v;
}

// eq-m43-cosine on unit vectors is a dot product. Returns [{id, score, words}] for the top k,
// highest first; ties keep document order. words: the query words that the document shares.
export function search(index, query, k = 5) {
  const q = unitVector(tokenize(query, index.stop), index.idf);
  const scored = index.rows.map((row, i) => {
    let s = 0;
    const words = [];
    for (const [w, x] of q) {
      if (row.has(w)) {
        s += x * row.get(w);
        words.push(w);
      }
    }
    return { i, score: s, words };
  });
  scored.sort((a, b) => b.score - a.score || a.i - b.i);
  return scored.slice(0, k).map((r) => ({ id: index.ids[r.i], score: r.score, words: r.words }));
}
