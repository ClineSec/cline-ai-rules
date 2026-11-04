from helpdesk.kb_index import chunk_article


def test_chunk_article_splits_on_word_count():
    text = " ".join(f"w{i}" for i in range(10))
    assert chunk_article(text, size=4) == ["w0 w1 w2 w3", "w4 w5 w6 w7", "w8 w9"]
