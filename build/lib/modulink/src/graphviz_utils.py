def to_graphviz(chain, dot=None, prefix="", seen=None, level="all", color_map=None, color_idx=0, id_map=None):
    """
    Visualize a chain (and optionally subchains) as a Graphviz Digraph.
    level: 'all' (default) - expand all subchains and show all links and connections
           'chain'         - show only top-level chains as nodes, connections between chains
           'links'         - flatten all chains and show only links as nodes
    Uses pastel/comfort colors to distinguish main and subchains.
    Node labels are always the function/link/chain name, never an internal ID.
    """
    try:
        from graphviz import Digraph
    except ImportError:
        raise RuntimeError("graphviz is required for visualization.")
    pastel_colors = [
        "#A3C9E2", "#F7CAC9", "#B5EAD7", "#FFDAC1", "#E2F0CB", "#C7CEEA", "#FFF1BA", "#FFB7B2", "#B5B2FF", "#B2F7EF"
    ]
    if dot is None:
        dot = Digraph(comment="Chain Visualization")
    if seen is None:
        seen = set()
    if color_map is None:
        color_map = {}
    if id_map is None:
        id_map = {}
    # Assign a color to this chain
    chain_id = id(chain)
    if chain_id not in color_map:
        color_map[chain_id] = pastel_colors[color_idx % len(pastel_colors)]
    chain_color = color_map[chain_id]
    # Helper to get a unique node id but always use a readable label
    def node_id(name):
        if name not in id_map:
            id_map[name] = f"n{len(id_map)+1}"
        return id_map[name]
    # Chain-level node (for 'chain' level)
    if level == "chain":
        chain_name = prefix.rstrip('_') or getattr(chain, '__name__', 'chain')
        nid = node_id(chain_name)
        if nid not in seen:
            dot.node(nid, label=chain_name, shape='box', style='filled', fillcolor=chain_color)
            seen.add(nid)
    # Add nodes for each link (for 'all' and 'links' levels)
    if level in ("all", "links"):
        for link in chain._links:
            label = getattr(link, '__name__', str(link))
            nid = node_id(f"{prefix}{label}")
            if nid not in seen:
                # Always set label explicitly
                dot.node(nid, label=label, style='filled', fillcolor=chain_color)
                seen.add(nid)
    # Add edges for sequential links (for 'all' and 'links' levels)
    if level in ("all", "links"):
        for i in range(len(chain._links) - 1):
            src_label = getattr(chain._links[i], '__name__', str(chain._links[i]))
            tgt_label = getattr(chain._links[i+1], '__name__', str(chain._links[i+1]))
            src = node_id(f"{prefix}{src_label}")
            tgt = node_id(f"{prefix}{tgt_label}")
            dot.edge(src, tgt)
    # Add edges for explicit connections (branching)
    for conn in getattr(chain, '_connections', []):
        # Handle source
        if hasattr(conn['source'], '_links'):
            sub_prefix = f"{prefix}{getattr(conn['source'], '__name__', 'subchain')}_"
            to_graphviz(conn['source'], dot, sub_prefix, seen, level=level, color_map=color_map, color_idx=color_idx+1, id_map=id_map)
            if level == "all" or level == "links":
                src_label = getattr(conn['source']._links[-1], '__name__', str(conn['source']._links[-1]))
                src = node_id(f"{sub_prefix}{src_label}")
            elif level == "chain":
                src_label = sub_prefix.rstrip('_')
                src = node_id(src_label)
        else:
            src_label = getattr(conn['source'], '__name__', str(conn['source']))
            src = node_id(f"{prefix}{src_label}")
        # Handle target
        if hasattr(conn['target'], '_links'):
            sub_prefix = f"{prefix}{getattr(conn['target'], '__name__', 'subchain')}_"
            to_graphviz(conn['target'], dot, sub_prefix, seen, level=level, color_map=color_map, color_idx=color_idx+1, id_map=id_map)
            if level == "all" or level == "links":
                tgt_label = getattr(conn['target']._links[0], '__name__', str(conn['target']._links[0]))
                tgt = node_id(f"{sub_prefix}{tgt_label}")
            elif level == "chain":
                tgt_label = sub_prefix.rstrip('_')
                tgt = node_id(tgt_label)
        else:
            tgt_label = getattr(conn['target'], '__name__', str(conn['target']))
            tgt = node_id(f"{prefix}{tgt_label}")
        # Label
        label = ''
        if 'condition' in conn:
            cond = conn['condition']
            if hasattr(cond, '__name__'):
                label = cond.__name__
            elif hasattr(cond, '__class__') and cond.__class__.__name__ == 'function':
                label = 'lambda' if (getattr(cond, '__name__', '') == '<lambda>') else 'function'
            else:
                label = 'condition'
        dot.edge(src, tgt, label=label)
    return dot
