import os
import sys
import xml.etree.ElementTree as ET
import tempfile
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from modulink.src.chain import Chain
from modulink.src.context import Context
from modulink.src.graphviz_utils import to_graphviz

def test_chain_svg_output():
    # Example: create a simple chain
    def step1(ctx):
        ctx['a'] = 1
        return ctx
    def step2(ctx):
        ctx['b'] = 2
        return ctx
    chain = Chain(step1, step2)
    # Use the to_graphviz function from graphviz_utils
    with tempfile.TemporaryDirectory() as tmpdir:
        svg_path = os.path.join(tmpdir, 'test_chain')
        dot = to_graphviz(chain)
        dot.render(svg_path, format='svg', cleanup=True)
        svg_file = svg_path + '.svg'
        assert os.path.exists(svg_file), f"SVG file not found: {svg_file}"
        tree = ET.parse(svg_file)
        root = tree.getroot()
        svg_text = ET.tostring(root, encoding='unicode')
        assert 'step1' in svg_text, "SVG should contain node for step1"
        assert 'step2' in svg_text, "SVG should contain node for step2"
    print("SVG output test passed.")

if __name__ == "__main__":
    test_chain_svg_output()
