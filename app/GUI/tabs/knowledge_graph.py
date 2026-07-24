import streamlit as st
import os
import sys
import tempfile


def render_knowledge_graph():
    """Render the Knowledge Graph tab: an interactive pyvis network of
    Blackboard entities/findings, with a search filter and an entity
    detail viewer."""
    st.title(":link: Knowledge Graph")
    st.markdown("---")

    try:
        from app.GUI.utils.blackboard import build_graph_data
    except ImportError:
        st.error("Cannot import blackboard utilities.")
        return

    G = build_graph_data()

    if G is None:
        st.warning("NetworkX is not installed. Install with: pip install networkx pyvis")
        st.info("The knowledge graph requires networkx and pyvis for visualization.")
        return

    if G.number_of_nodes() == 0:
        st.info("No entities found in the Blackboard. Run reconnaissance first to populate the knowledge graph.")
        return

    st.markdown(f"**Nodes**: {G.number_of_nodes()} | **Edges**: {G.number_of_edges()}")

    search = st.text_input(":mag: Search entities", placeholder="Filter by name or type...")

    try:
        from pyvis.network import Network
        net = Network(height="600px", width="100%", bgcolor="#0e1117", font_color="#00ff41")
        net.force_atlas_2based()

        color_map = {
            "target": "#ff4444",
            "ip": "#4444ff",
            "technology": "#44ff44",
            "vulnerability": "#ffaa00",
            "finding": "#888888",
            "domain": "#ff44ff",
        }

        for node, data in G.nodes(data=True):
            label = data.get("label", str(node))
            node_type = data.get("type", "unknown")
            color = color_map.get(node_type, "#888888")

            if search and search.lower() not in label.lower() and search.lower() not in node_type.lower():
                continue

            net.add_node(
                str(node),
                label=label,
                title=f"Type: {node_type}",
                color=color,
                size=20 if node_type == "target" else 15,
            )

        for u, v, data in G.edges(data=True):
            label = data.get("label", "related_to")
            net.add_edge(str(u), str(v), title=label, label=label)

        graph_html = net.generate_html()
        st.components.v1.html(graph_html, height=600, scrolling=True)
    except ImportError:
        st.warning("Pyvis is not installed. Install with: pip install pyvis")
        return

    st.markdown("---")
    st.subheader(":clipboard: Entity Details")

    entities = []
    for node, data in G.nodes(data=True):
        entities.append({
            "id": node,
            "name": data.get("label", str(node)),
            "type": data.get("type", "unknown"),
        })

    if entities:
        selected_entity = st.selectbox("Select entity to view details", [e["name"] for e in entities])
        entity_data = next((e for e in entities if e["name"] == selected_entity), None)
        if entity_data:
            node_data = G.nodes[entity_data["id"]]
            st.json(node_data.get("properties", {}))
