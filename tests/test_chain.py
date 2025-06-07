import pytest
from modulink import utils, core

@pytest.mark.asyncio
async def test_chain_composition():
    async def link1(ctx):
        return {**ctx, "a": 1}
    async def link2(ctx):
        return {**ctx, "b": 2}
    chain = utils.chain(link1, link2)
    result = await chain({})
    assert result["a"] == 1
    assert result["b"] == 2

@pytest.mark.asyncio
async def test_chain_middleware():
    async def link(ctx):
        return {**ctx, "x": 42}
    chain = utils.chain(link)
    chain.use(lambda ctx: {**ctx, "mw": True})
    result = await chain({})
    assert result["x"] == 42
    assert result["mw"] is True

@pytest.mark.asyncio
async def test_chain_error_propagation():
    async def fail(ctx):
        raise ValueError("fail")
    chain = utils.chain(fail)
    result = await chain({})
    assert "error" in result
