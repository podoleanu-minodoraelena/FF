import streamlit as st
import networkx as nx
import matplotlib.pyplot as plt
import collections

# ═══════════════════════════════════════════════
# BACKEND - FORD FULKERSON
# ═══════════════════════════════════════════════

class Graph:
    def __init__(self):
        self.edges = []  # (u, v, cap, flow)

    def add_edge(self, u, v, cap):
        self.edges.append([u, v, cap, 0])

    def build_residual(self):
        residual = {}
        for u, v, cap, flow in self.edges:
            residual[(u, v)] = residual.get((u, v), 0) + (cap - flow)
            residual[(v, u)] = residual.get((v, u), 0) + flow
        return residual

    def bfs(self, src, dst, residual):
        parent = {src: None}
        q = collections.deque([src])

        while q:
            u = q.popleft()
            for (a, b), cap in residual.items():
                if a == u and cap > 0 and b not in parent:
                    parent[b] = u
                    q.append(b)

        if dst not in parent:
            return None

        path = []
        cur = dst
        while cur is not None:
            path.append(cur)
            cur = parent[cur]
        return path[::-1]

    def max_flow(self, src, dst):
        flow = 0
        paths = []

        while True:
            residual = self.build_residual()
            path = self.bfs(src, dst, residual)

            if not path:
                break

            delta = min(residual[(path[i], path[i+1])] for i in range(len(path)-1))

            for i in range(len(path)-1):
                u, v = path[i], path[i+1]

                for e in self.edges:
                    if e[0] == u and e[1] == v:
                        e[3] += delta
                    if e[0] == v and e[1] == u:
                        e[3] -= delta

            flow += delta
            paths.append((path, delta))

        return flow, paths


# ═══════════════════════════════════════════════
# STREAMLIT UI
# ═══════════════════════════════════════════════

st.set_page_config(page_title="Ford-Fulkerson", layout="wide")

st.title("🚀 Ford-Fulkerson Visualizer (Streamlit)")

# init graph
if "g" not in st.session_state:
    st.session_state.g = Graph()

g = st.session_state.g

# ═══════════════════════════════════════════════
# INPUT SECTION
# ═══════════════════════════════════════════════

st.subheader("➕ Adaugă muchii")

col1, col2, col3 = st.columns(3)

with col1:
    u = st.text_input("From (ex: x1)")
with col2:
    v = st.text_input("To (ex: x2)")
with col3:
    c = st.number_input("Capacity", min_value=1, value=10)

if st.button("Adaugă muchie"):
    if u and v:
        g.add_edge(u, v, c)
        st.success(f"Adăugat: {u} → {v} [{c}]")

st.divider()

# ═══════════════════════════════════════════════
# SOURCE / SINK
# ═══════════════════════════════════════════════

st.subheader("▶ Ford-Fulkerson")

src = st.text_input("Sursă", "x1")
dst = st.text_input("Destinație", "x10")

run = st.button("Rulează algoritmul")

# ═══════════════════════════════════════════════
# RUN ALGORITHM
# ═══════════════════════════════════════════════

if run:
    flow, paths = g.max_flow(src, dst)
    st.success(f"Flux maxim = {flow}")

    st.subheader("📌 Pași algoritm")

    for i, (p, d) in enumerate(paths, 1):
        st.write(f"Pas {i}: {' → '.join(p)} | Δ = {d}")

# ═══════════════════════════════════════════════
# GRAPH VISUALIZATION
# ═══════════════════════════════════════════════

st.subheader("📊 Grafic")

G = nx.DiGraph()

for u, v, cap, flow in g.edges:
    G.add_edge(u, v, label=f"{flow}/{cap}")

pos = nx.spring_layout(G, seed=42)

fig, ax = plt.subplots(figsize=(7, 5))

nx.draw(
    G, pos,
    ax=ax,
    with_labels=True,
    node_color="#8ecae6",
    node_size=1200,
    font_size=10,
    arrows=True
)

edge_labels = {(u, v): d["label"] for u, v, d in G.edges(data=True)}

nx.draw_networkx_edge_labels(
    G,
    pos,
    edge_labels=edge_labels,
    font_size=9
)

st.pyplot(fig)

# ═══════════════════════════════════════════════
# EDGE LIST
# ═══════════════════════════════════════════════

st.subheader("📋 Muchii")

for u, v, cap, flow in g.edges:
    st.write(f"{u} → {v} | flow: {flow} / {cap}")