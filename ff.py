import streamlit as st
import collections
import graphviz
import pandas as pd

# --- LOGICA FORD-FULKERSON ---
class FordFulkersonStreamlit:
    def __init__(self, edges_data):
        # Primim datele editate (fără coloana flow, o adăugăm noi intern)
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

    def build_residual(self):
        self.residual = {}
        for e in self.edges:
            u, v = e['src'], e['dst']
            fwd, bwd = (u, v), (v, u)
            self.residual[fwd] = self.residual.get(fwd, 0) + (e['cap'] - e['flow'])
            self.residual[bwd] = self.residual.get(bwd, 0) + e['flow']

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

    def solve(self, src, dst):
        while True:
            self.build_residual()
            path = self.bfs_path(src, dst)
            if not path: break
            delta = min(self.residual[(path[i], path[i+1])] for i in range(len(path)-1))
            for i in range(len(path) - 1):
                u_p, v_p = path[i], path[i+1]
                for e in self.edges:
                    if e['src'] == u_p and e['dst'] == v_p: e['flow'] += delta; break
                    elif e['src'] == v_p and e['dst'] == u_p: e['flow'] -= delta; break
            self.max_flow += delta
            self.paths_found.append({"path": path, "delta": delta})
        return self.edges

# --- INTERFAȚA STREAMLIT ---
st.set_page_config(page_title="Ford-Fulkerson Pro", page_icon="⚡", layout="wide")

# CSS pentru un look mai atractiv
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #1a1c24; padding: 15px; border-radius: 10px; border: 1px solid #4f6ef7; }
    </style>
    """, unsafe_allow_value=True)

st.title("⚡ Ford-Fulkerson Network Optimizer")
st.write("Optimizează fluxul de date în rețele complexe prin algoritmul Edmonds-Karp.")

# Datele tale predefinite (FĂRĂ coloana Flow)
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

# Organizare în coloane pentru input
col_tab, col_cfg = st.columns([2, 1])

with col_cfg:
    st.sidebar.header("🚀 Control Panel")
    source = st.sidebar.text_input("Nod Sursă (s)", "x1")
    sink = st.sidebar.text_input("Nod Destinație (t)", "x10")
    run_btn = st.sidebar.button("⚡ CALCULEAZĂ FLUX MAXIM", use_container_width=True)
    
    st.sidebar.markdown("---")
    st.sidebar.info("Modifică valorile din tabelul din dreapta pentru a simula scenarii diferite.")

with col_tab:
    st.write("### 🛠️ Configurare Capacități Rețea")
    # Utilizatorul vede doar sursa, destinația și capacitatea
    edited_df = st.data_editor(
        st.session_state.initial_data, 
        num_rows="dynamic",
        column_config={
            "src": "Sursă",
            "dst": "Destinație",
            "cap": st.column_config.NumberColumn("Capacitate Maximă", min_value=1)
        },
        use_container_width=True
    )

if run_btn:
    ff = FordFulkersonStreamlit(edited_df)
    final_edges = ff.solve(source, sink)
    
    st.divider()
    
    # Rezultate Vizuale
    m1, m2, m3 = st.columns(3)
    m1.metric("FLUX TOTAL", f"{ff.max_flow} unități")
    m2.metric("DRUMURI GĂSITE", len(ff.paths_found))
    m3.metric("EFICIENȚĂ", "Maximă")

    res_col1, res_col2 = st.columns([1, 2])
    
    with res_col1:
        st.write("#### 🛤️ Analiza Drumurilor")
        for idx, p in enumerate(ff.paths_found):
            with st.expander(f"Drum Ameliorare #{idx+1} (+{p['delta']})"):
                st.write(" → ".join(p['path']))

    with col2:
        st.write("#### 📊 Topologia Rețelei Rezultate")
        dot = graphviz.Digraph()
        dot.attr(rankdir='LR', bgcolor='transparent')
        
        # Stil noduri
        dot.attr('node', shape='circle', style='filled', color='#4f6ef7', fontcolor='white', fillcolor='#1e2240')
        
        for e in final_edges:
            f, c = e['flow'], e['cap']
            # Colorare dinamică
            if f == 0:
                color, width, style = "#6b7299", "1.0", "dashed"
            elif f == c:
                color, width, style = "#f75c8d", "3.0", "solid" # Saturat (Roz neon)
            else:
                color, width, style = "#27c98f", "2.5", "solid" # Activ (Verde neon)
            
            dot.edge(e['src'], e['dst'], label=f"{f}/{c}", color=color, fontcolor=color, penwidth=width, style=style)
        
        st.graphviz_chart(dot)
    
    st.toast("Calcul finalizat cu succes!", icon="💰")
