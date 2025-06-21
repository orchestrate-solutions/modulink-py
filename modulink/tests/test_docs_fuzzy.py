import pytest
from modulink.src.docs import get_doc

def test_fuzzy_exact_match():
    # Should match exactly
    assert "Chain" in get_doc("chain")

def test_fuzzy_typo():
    # Should fuzzy match to 'chain'
    result = get_doc("chian")
    assert "Chain" in result or "Did you mean 'chain'" in result

def test_fuzzy_partial():
    # Should fuzzy match to 'examples'
    result = get_doc("exampl")
    assert "examples" in result.lower() or "Did you mean 'examples'" in result

def test_fuzzy_no_match():
    # Should suggest closest topic
    result = get_doc("notarealtopic")
    assert "Did you mean" in result or "No documentation found" in result
