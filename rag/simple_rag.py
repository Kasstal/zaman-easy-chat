import math


class SimpleRAG:
    """
    Lightweight RAG using cosine similarity on term-frequency vectors.
    """

    def __init__(self):
        self.docs = []  # [{'id','title','url','content'}]
        self.vocab = {}
        self.doc_tf = []  # list[dict[token -> tf]]

    def build(self, docs):
        """Build the TF vectors and vocab for all docs."""
        self.docs = docs[:]
        self.vocab = {}
        self.doc_tf = []
        for d in docs:
            tf = {}
            for tok in self._tokens(d['content']):
                tf[tok] = tf.get(tok, 0) + 1
                if tok not in self.vocab:
                    self.vocab[tok] = len(self.vocab)
            self.doc_tf.append(tf)

    def _tokens(self, text):
        return [t for t in "".join(
            ch.lower() if ch.isalnum() else " "
            for ch in text
        ).split() if t]

    def _to_vec(self, tf):
        vec = [0.0] * len(self.vocab)
        for tok, cnt in tf.items():
            idx = self.vocab.get(tok)
            if idx is not None:
                vec[idx] = float(cnt)
        return vec

    def _cos(self, a, b):
        dot = sum(x * y for x, y in zip(a, b))
        na = math.sqrt(sum(x * x for x in a))
        nb = math.sqrt(sum(x * x for x in b))
        return 0.0 if na == 0 or nb == 0 else dot / (na * nb)

    def search(self, query: str, k: int = 5):
        """Return top-k most similar documents for the query."""
        qtf = {}
        for tok in self._tokens(query):
            qtf[tok] = qtf.get(tok, 0) + 1
        qv = self._to_vec(qtf)
        scored = []
        for i, tf in enumerate(self.doc_tf):
            dv = self._to_vec(tf)
            scored.append((self._cos(qv, dv), i))
        scored.sort(reverse=True)
        out = []
        for score, idx in scored[:k]:
            d = self.docs[idx]
            out.append({
                "id": d["id"],
                "score": float(score),
                "title": d.get("title", ""),
                "url": d.get("url"),
                "content": d["content"][:800],
            })
        return out


# ✅ Singleton RAG instance
rag = SimpleRAG()
