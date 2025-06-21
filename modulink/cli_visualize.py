import argparse
from modulink.src.chain import Chain
from modulink.src.context import Context
from modulink.src.graphviz_utils import to_graphviz
import inspect
import os
import re

def find_chains(module):
    """Return a dict of all Chain instances in the module."""
    return {name: obj for name, obj in vars(module).items() if isinstance(obj, Chain)}

def collect_all_chains(chain, name_map=None, seen=None):
    """Recursively collect all chains (main and subchains) as (name, chain) tuples, using variable names if possible."""
    if seen is None:
        seen = set()
    if name_map is None:
        name_map = {}
    results = []
    # Use the variable name if available, else fallback to id
    chain_id = id(chain)
    chain_name = name_map.get(chain_id, getattr(chain, '__name__', f'chain_{chain_id}'))
    if chain_id not in seen:
        results.append((chain_name, chain))
        seen.add(chain_id)
        for conn in getattr(chain, '_connections', []):
            for endpoint in ['source', 'target']:
                obj = conn[endpoint]
                if isinstance(obj, Chain):
                    # Try to get the variable name from the parent scope
                    sub_id = id(obj)
                    sub_name = name_map.get(sub_id, getattr(obj, '__name__', f'subchain_{sub_id}'))
                    name_map[sub_id] = sub_name
                    results.extend(collect_all_chains(obj, name_map, seen))
    return results

def collect_all_links(chain, prefix="", seen=None):
    """Recursively collect all links in all chains as (name, link) tuples."""
    if seen is None:
        seen = set()
    results = []
    for link in chain._links:
        name = getattr(link, '__name__', str(link))
        if (id(link), name) not in seen:
            results.append((name, link))
            seen.add((id(link), name))
    for conn in getattr(chain, '_connections', []):
        for endpoint in ['source', 'target']:
            obj = conn[endpoint]
            if isinstance(obj, Chain):
                results.extend(collect_all_links(obj, seen=seen))
    return results

def strip_svg_ext(path):
    return re.sub(r'(\.svg|\.dot)?$', '', path, flags=re.IGNORECASE)

def main():
    parser = argparse.ArgumentParser(description="Visualize ModuLink Next chains.")
    parser.add_argument('--format', choices=['svg', 'dot', 'mermaid'], default='svg', help='Output format')
    parser.add_argument('--output', required=True, help='Output file path or directory')
    parser.add_argument('--chain', required=True, help='Python file containing Chain instances')
    parser.add_argument('--chain-name', help='Name of the Chain to visualize (default: all)')
    parser.add_argument('--level', choices=['all', 'chain', 'links'], default='all', help='Visualization granularity: all (default), chain, or links')
    args = parser.parse_args()

    # Dynamically import the chain module
    import importlib.util
    import sys
    spec = importlib.util.spec_from_file_location("user_chain", args.chain)
    user_chain = importlib.util.module_from_spec(spec)
    sys.modules["user_chain"] = user_chain
    spec.loader.exec_module(user_chain)

    chains = find_chains(user_chain)
    if args.chain_name:
        if args.chain_name not in chains:
            print(f"Chain '{args.chain_name}' not found in {args.chain}.")
            return
        chains = {args.chain_name: chains[args.chain_name]}

    os.makedirs(args.output, exist_ok=True)

    # Build a name map for all chains in the module
    name_map = {id(obj): name for name, obj in chains.items()}

    for name, chain in chains.items():
        if args.level == 'all':
            dot = to_graphviz(chain, level='all')
            out_path = strip_svg_ext(os.path.join(args.output, f"{name}_all.{args.format}"))
            if args.format == 'svg':
                dot.render(out_path, format='svg', cleanup=True)
            else:
                dot.save(out_path)
            print(f"Visualization for full workflow '{name}' written to {out_path}.svg")
        elif args.level == 'chain':
            for cname, cobj in collect_all_chains(chain, name_map=name_map):
                dot = to_graphviz(cobj, level='chain')
                out_path = strip_svg_ext(os.path.join(args.output, f"{cname}_chain.{args.format}"))
                if args.format == 'svg':
                    dot.render(out_path, format='svg', cleanup=True)
                else:
                    dot.save(out_path)
                print(f"Visualization for chain '{cname}' written to {out_path}.svg")
        elif args.level == 'links':
            for lname, lobj in collect_all_links(chain):
                from graphviz import Digraph
                dot = Digraph(comment=f"Link {lname}")
                dot.node(lname)
                out_path = strip_svg_ext(os.path.join(args.output, f"{lname}_link.{args.format}"))
                if args.format == 'svg':
                    dot.render(out_path, format='svg', cleanup=True)
                else:
                    dot.save(out_path)
                print(f"Visualization for link '{lname}' written to {out_path}.svg")
        elif args.format == 'mermaid':
            mermaid = chain.to_mermaid()
            out_path = os.path.join(args.output, f"{name}.mmd")
            with open(out_path, 'w') as f:
                f.write(mermaid)
            print(f"Mermaid visualization for chain '{name}' written to {out_path}")

if __name__ == "__main__":
    main()
