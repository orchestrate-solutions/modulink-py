import pytest
from modulink import utils, core

@pytest.mark.asyncio
async def test_chain_with_middleware_and_error():
    async def link(ctx):
        return {**ctx, "ok": True}
    async def fail(ctx):
        raise RuntimeError("fail")
    chain = utils.chain(link, fail)
    chain.use(lambda ctx: {**ctx, "mw": 1})
    result = await chain({})
    assert "error" in result

@pytest.mark.asyncio
async def test_chain_parallel_execution():
    async def link1(ctx):
        return {**ctx, "a": 1}
    async def link2(ctx):
        return {**ctx, "b": 2}
    parallel_chain = utils.parallel(link1, link2)
    result = await parallel_chain({})
    assert result["a"] == 1
    assert result["b"] == 2
