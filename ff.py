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

    def solve(self, src, dst):
        iteration = 1
        while True:
            self.build_residual()
            path = self.bfs_path(src, dst)
            if not path: break
            
            miu_val = min(self.residual[(path[i], path[i+1])] for i in range(len(path)-1))
            
            for i in range(len(path) - 1):
                u_p, v_p = path[i], path[i+1]
                for e in self.edges:
                    if e['src'] == u_p and e['dst'] == v_p: e['flow'] += miu_val; break
                    elif e['src'] == v_p and e['dst'] == u_p: e['flow'] -= miu_val; break
            
            self.max_flow += miu_val
            self.paths_found.append({"id": iteration, "path": path, "miu": miu_val})
            iteration += 1
        return self.edges

# --- INTERFAȚA STREAMLIT ---
st.set_page_config(page_title="Algoritmul Ford-Fulkerson", page_icon="⚡", layout="wide")

# CSS pentru stilul Dark & Neon
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    div[data-testid="stMetric"] { 
        background-color: #1a1c24; 
        padding: 15px; 
        border-radius: 12px; 
        border: 1px solid #4f6ef7; 
    }
    .path-box {
        background-color: #1e2240;
        padding: 10px;
        border-radius: 8px;
        margin-bottom: 5px;
        border-left: 4px solid #f7a435;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("⚡ Ford-Fulkerson Network Optimizer")

# Date implicite
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

col_edit, col_ctrl = st.columns([2, 1])

with col_ctrl:
    st.sidebar.header("🚀 Panou Control")
    source = st.sidebar.text_input("Sursă (s)", "x1")
    sink = st.sidebar.text_input("Destinație (t)", "x10")
    run_btn = st.sidebar.button("⚡ CALCULEAZĂ FLUX MAXIM")

with col_edit:
    st.write("### 🛠️ Configurare Capacități")
    edited_df = st.data_editor(st.session_state.initial_data, num_rows="dynamic", use_container_width=True)

if run_btn:
    ff = FordFulkersonStreamlit(edited_df if isinstance(edited_df, list) else edited_df.to_dict('records'))
    final_edges = ff.solve(source, sink)
    
    st.balloons() # Efectul de baloane cerut
    st.divider()
    
    # Metrici
    m1, m2, m3 = st.columns(3)
    m1.metric("FLUX MAXIM", f"{ff.max_flow}")
    m2.metric("DRUMURI (μ)", len(ff.paths_found))
    m3.metric("EFICIENȚĂ", "Optimizat")

    c1, c2 = st.columns([1, 2])
    
    with c1:
        st.write("#### 🛤️ Drumuri de Ameliorare")
        for p in ff.paths_found:
            st.markdown(f"""<div class='path-box'><b>μ_{p['id']}</b>: {' → '.join(p['path'])} <br>val: <b>{p['miu']}</b></div>""", unsafe_allow_html=True)

    with c2:
        st.write("#### 📊 Vizualizare Graf")
        dot = graphviz.Digraph()
        dot.attr(rankdir='LR', bgcolor='#0e1117')
        dot.attr('node', shape='circle', style='filled', color='#4f6ef7', fontcolor='white', fillcolor='#1e2240')
        
        for e in final_edges:
            f, c = e['flow'], e['cap']
            if f == 0: color, width, style = "#6b7299", "1.0", "dashed"
            elif f == c: color, width, style = "#f75c8d", "3.5", "solid"
            else: color, width, style = "#27c98f", "2.5", "solid"
            
            dot.edge(e['src'], e['dst'], label=f"{f}/{c}", color=color, fontcolor=color, penwidth=width, style=style)
        
        st.graphviz_chart(dot)

    # TABELUL FINAL DE ANALIZĂ
    st.write("### 📝 Analiză Detaliată a Arcelor")
    analysis_list = []
    for e in final_edges:
        utilizare = (e['flow'] / e['cap'] * 100) if e['cap'] > 0 else 0
        status = "🔴 SATURAT" if e['flow'] == e['cap'] else ("🟢 ACTIV" if e['flow'] > 0 else "⚪ NEUTILIZAT")
        analysis_list.append({
            "Arc (Sursă → Dest)": f"{e['src']} → {e['dst']}",
            "Flux": e['flow'],
            "Capacitate": e['cap'],
            "Utilizare": f"{utilizare:.1f}%",
            "Status": status
        })
    
    st.dataframe(pd.DataFrame(analysis_list), use_container_width=True)
