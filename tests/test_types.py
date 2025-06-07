import pytest
from modulink import types

def test_ctx_type():
    # Ctx is a type alias for Dict[str, Any], so we create a dict
    ctx: types.Ctx = {}
    assert isinstance(ctx, dict)

def test_create_context():
    ctx = types.create_context(foo="bar")
    assert ctx["foo"] == "bar"

def test_create_http_context():
    ctx = types.create_http_context(method="GET", path="/", headers={}, query={}, body={})
    assert ctx["method"] == "GET"
    assert ctx["path"] == "/"
