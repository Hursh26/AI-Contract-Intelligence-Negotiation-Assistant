from ml.preprocessing import normalize_text, split_into_clauses, split_sentences


def test_normalize_preserves_legal_punctuation():
    text = "  The Tenant shall pay $1,200/month.\r\n\r\n  "
    result = normalize_text(text)
    assert result == "The Tenant shall pay $1,200/month."


def test_split_sentences_needs_no_download():
    assert split_sentences("First sentence. Second sentence.") == ["First sentence.", "Second sentence."]


def test_numbered_clauses_keep_heading():
    text = "1. Payment\nThe Tenant shall pay $1,200 per month.\n\n2. Termination\nEither party may terminate with 30 days written notice."
    clauses = split_into_clauses(text)
    assert [c["id"] for c in clauses] == ["1", "2"]
    assert clauses[0]["text"].startswith("1. Payment")
