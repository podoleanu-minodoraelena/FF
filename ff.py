import streamlit as st
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import collections

# ═══════════════════════════════════════
# INIT SESSION STATE
# ═══════════════════════════════════════

if "edges" not in st.session_state:
    st.session_state.edges = [
        ("x1","x2",20),
        ("x1","x3",30),
        ("x1","x4",40),
        ("x2","x7",10),
        ("x2","x5",12),
        ("x3","x5",8),
        ("x3","x8",15),
        ("x3","x6",10),
        ("x4","x6",9),
        ("x4","x9",11),
        ("x5","x7",10),
        ("x5","x8",9),
        ("x6","x8",12),
        ("x6","x9",8),
        ("x7","x10",31),
        ("x8","x10",14),
        ("x9","x10",42),
    ]

# ═══════════════════════════════════════
# FORD-FULKERSON
# ═══════════════════════════════════════

class Graph:
    def __init__(self, edges):
        self.edges = [[u, v, c, 0] for u, v, c in edges]

    def build_residual(self):
        r = {}
        for u, v, c, f in self.edges:
            r[(u,v)] = r.get((u,v),0) + (c-f)
            r[(v,u)] = r.get((v,u),0) + f
        return r

    def bfs(self, s, t, r):
        parent = {s: None}
        q = collections.deque([s])

        while q:
            u = q.popleft()
            for (a,b),cap in r.items():
                if a == u and cap > 0 and b not in parent:
                    parent[b] = u
                    q.append(b)

        if t not in parent:
            return None

        path = []
        cur = t
        while cur:
            path.append(cur)
            cur = parent[cur]
        return path[::-1]

    def max_flow(self, s, t):
        flow = 0
        steps = []

        while True:
            r = self.build_residual()
            path = self.bfs(s,t,r)
            if not path:
                break

            delta = min(r[(path[i],path[i+1])] for i in range(len(path)-1))

            for i in range(len(path)-1):
                u,v = path[i], path[i+1]
                for e in self.edges:
                    if e[0]==u and e[1]==v:
                        e[3]+=delta
                    if e[0]==v and e[1]==u:
                        e[3]-=delta

            flow += delta
            steps.append((path,delta))

        return flow, steps


# ═══════════════════════════════════════
# UI
# ═══════════════════════════════════════

st.title("🚀 Ford-Fulkerson Visualizer (Streamlit corect)")

# ── TABLE EDITABIL
st.subheader("📊 Editează graful")

df = pd.DataFrame(st.session_state.edges, columns=["From","To","Capacity"])

edited = st.data_editor(df, num_rows="dynamic")

st.session_state.edges = list(
    zip(edited["From"], edited["To"], edited["Capacity"])
)

# ── ADD EDGE
st.subheader("➕ Adaugă muchie")

c1,c2,c3 = st.columns(3)

with c1:
    u = st.text_input("From")
with c2:
    v = st.text_input("To")
with c3:
    c = st.number_input("Capacity",1,100,10)

if st.button("Adaugă"):
    st.session_state.edges.append((u,v,c))
    st.rerun()

# ── SOURCE / SINK
st.subheader("▶ Ford-Fulkerson")

src = st.text_input("Source", "x1")
dst = st.text_input("Sink", "x10")

run = st.button("Rulează")

# ── RUN
if run:
    g = Graph(st.session_state.edges)
    flow, steps = g.max_flow(src,dst)

    st.success(f"Flux maxim = {flow}")

    st.write("### Pași:")
    for i,(p,d) in enumerate(steps,1):
        st.write(f"{i}. {' → '.join(p)} | Δ={d}")

# ── GRAPH DRAW
st.subheader("📈 Grafic")

G = nx.DiGraph()

for u,v,c in st.session_state.edges:
    G.add_edge(u,v,label=str(c))

pos = nx.spring_layout(G, seed=42)

fig, ax = plt.subplots(figsize=(7,5))

nx.draw(G,pos,ax=ax,with_labels=True,node_color="#8ecae6",
        node_size=1200,arrows=True)

labels = {(u,v):d["label"] for u,v,d in G.edges(data=True)}
nx.draw_networkx_edge_labels(G,pos,edge_labels=labels)

st.pyplot(fig)

# ── LISTĂ
st.subheader("📋 Muchii curente")

for u,v,c in st.session_state.edges:
    st.write(f"{u} → {v} | cap: {c}")
