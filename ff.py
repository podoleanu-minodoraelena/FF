import streamlit as st
import collections
import graphviz
import pandas as pd

# --- LOGICA FORD-FULKERSON ---
class FordFulkersonStreamlit:
    def __init__(self, edges_data):
        self.edges = []
        for e in edges_data:
            self.edges.append({
                "src": str(e["src"]),
                "dst": str(e["dst"]),
                "cap": int(e["cap"]),
                "flow": 0
            })
        self.residual = {}
        self.max_flow = 0
        self.paths_found = []
        self.min_cut_S = set()

    def build_residual(self):
        self.residual = {}
        for e in self.edges:
            u, v = e['src'], e['dst']
            self.residual[(u, v)] = self.residual.get((u, v), 0) + (e['cap'] - e['flow'])
            self.residual[(v, u)] = self.residual.get((v, u), 0) + e['flow']

    def bfs_path(self, src, dst):
        parent = {src: None}
        queue = collections.deque([src])
        while queue:
            u = queue.popleft()
            if u == dst:
                path = []
                while u is not None:
                    path.append(u); u = parent[u]
                return path[::-1]
            for (u_res, v_res), cap in self.residual.items():
                if u_res == u and cap > 0 and v_res not in parent:
                    parent[v_res] = u
                    queue.append(v_res)
        return None

    def find_min_cut(self, src):
        # Nodurile accesibile din sursă în graful rezidual final
        visited = {src}
        queue = collections.deque([src])
        while queue:
            u = queue.popleft()
            for (u_res, v_res), cap in self.residual.items():
                if u_res == u and cap > 0 and v_res not in visited:
                    visited.add(v_res)
                    queue.append(v_res)
        return visited

    def solve(self, src, dst):
        iteration = 1
        while True:
            self.build_residual()
            path = self.bfs_path(src, dst)
            if not path: break
            
            # Capacitatea drumului de ameliorare (notată cu miu)
            miu_val = min(self.residual[(path[i], path[i+1])] for i in range(len(path)-1))
            
            for i in range(len(path) - 1):
                u_p, v_p = path[i], path[i+1]
                for e in self.edges:
                    if e['src'] == u_p and e['dst'] == v_p: e['flow'] += miu_val; break
                    elif e['src'] == v_p and e['dst'] == u_p: e['flow'] -= miu_val; break
            
            self.max_flow += miu_val
            self.paths_found.append({"id": iteration, "path": path, "miu": miu_val})
            iteration += 1
        
        self.min_cut_S = self.find_min_cut(src)
        return self.edges

# --- INTERFAȚA ---
st.set_page_config(page_title="Ford-Fulkerson Expert", page_icon="📈", layout="wide")

st.markdown("""
    <style>
    .stMetric { border-radius: 10px; border: 1px solid #4f6ef7; padding: 10px; }
    .path-text { font-family: monospace; color: #f7a435; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

st.title("📈 Analiză Avansată: Flux Maxim & Tăietură Minimă")

if 'initial_data' not in st.session_state:
    st.session_state.initial_data = [
        {"src": "x1", "dst": "x2", "cap": 20}, {"src": "x1", "dst": "x3", "cap": 30},
        {"src": "x1", "dst": "x4", "cap": 40}, {"src": "x2", "dst": "x7", "cap": 10},
        {"src": "x2", "dst": "x5", "cap": 12}, {"src": "x3", "dst": "x5", "cap": 8},
        {"src": "x3", "dst": "x8", "cap": 15}, {"src": "x3", "dst": "x6", "cap": 10},
        {"src": "x4", "dst": "x6", "cap": 9}, {"src": "x4", "dst": "x9", "cap": 11},
        {"src": "x5", "dst": "x7", "cap": 10}, {"src": "x5", "dst": "x8", "cap": 9},
        {"src": "x6", "dst": "x8", "cap": 12}, {"src": "x6", "dst": "x9", "cap": 8},
        {"src": "x7", "dst": "x10", "cap": 31}, {"src": "x8", "dst": "x10", "cap": 14},
        {"src": "x9", "dst": "x10", "cap": 42}
    ]

col_l, col_r = st.columns([1, 2])

with col_l:
    st.subheader("⚙️ Configurare Rețea")
    src = st.text_input("Sursă (s)", "x1")
    dst = st.text_input("Destinație (t)", "x10")
    edited_df = st.data_editor(st.session_state.initial_data, num_rows="dynamic", use_container_width=True)
    calc_ready = st.button("🚀 EXECUTE FORD-FULKERSON")

if calc_ready:
    ff = FordFulkersonStreamlit(edited_df if isinstance(edited_df, list) else edited_df.to_dict('records'))
    final_edges = ff.solve(src, dst)
    
    st.divider()
    
    # Rândul 1: Metrici principale
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Flux Maxim ($f^*$)", f"{ff.max_flow}")
    m2.metric("Drumuri ($\mu$)", len(ff.paths_found))
    m3.metric("Noduri în S", len(ff.min_cut_S))
    m4.metric("Noduri în T", len(set(e['src'] for e in final_edges) | set(e['dst'] for e in final_edges)) - len(ff.min_cut_S))

    # Rândul 2: Detalii drumuri și Graf
    c1, c2 = st.columns([1, 1.5])
    
    with c1:
        st.write("#### 🛤️ Drumuri de ameliorare ($\mu_i$)")
        for p in ff.paths_found:
            st.markdown(f"**$\mu_{p['id']}$**: <span class='path-text'>{' → '.join(p['path'])}</span> | val: **{p['miu']}**", unsafe_allow_html=True)
        
        st.write("#### ✂️ Tăietura Minimă ($S, T$)")
        st.info(f"**Mulțimea S:** {sorted(list(ff.min_cut_S))}")
        t_set = (set(e['src'] for e in final_edges) | set(e['dst'] for e in final_edges)) - ff.min_cut_S
        st.error(f"**Mulțimea T:** {sorted(list(t_set))}")

    with c2:
        st.write("#### 📊 Topologia Finală a Fluxului")
        dot = graphviz.Digraph()
        dot.attr(rankdir='LR', bgcolor='transparent')
        
        for e in final_edges:
            f, c = e['flow'], e['cap']
            # Colorare bazată pe gradul de utilizare
            usage = (f / c) if c > 0 else 0
            color = "#27c98f" if f > 0 else "#6b7299"
            if f == c: color = "#f75c8d" # Saturat
            
            pen = "3.0" if f > 0 else "1.0"
            dot.edge(e['src'], e['dst'], label=f"{f}/{c}", color=color, fontcolor=color, penwidth=pen)
        
        st.graphviz_chart(dot)

    # Rândul 3: Tabel de analiză
    st.write("#### 📝 Tabel de Analiză a Capacităților")
    analysis_data = []
    for e in final_edges:
        pct = (e['flow'] / e['cap'] * 100) if e['cap'] > 0 else 0
        status = "Saturat" if e['flow'] == e['cap'] else ("Activ" if e['flow'] > 0 else "Neutilizat")
        analysis_data.append({"Arc": f"{e['src']}→{e['dst']}", "Flux": e['flow'], "Capacitate": e['cap'], "Utilizare (%)": f"{pct:.1f}%", "Status": status})
    
    st.table(pd.DataFrame(analysis_data))
