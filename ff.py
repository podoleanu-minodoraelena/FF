import streamlit as st
import collections
import graphviz
import pandas as pd

# --- LOGICA FORD-FULKERSON (Edmonds-Karp) ---
class FordFulkersonStreamlit:
    def __init__(self, edges_data):
        # Reconstruim lista de muchii cu flux initial 0
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
            
            # Găsim capacitatea de ameliorare (gâtul de lupi)
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

# CSS pentru un aspect modern și Dark Mode
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    div[data-testid="stMetric"] { 
        background-color: #1a1c24; 
        padding: 20px; 
        border-radius: 12px; 
        border-left: 5px solid #4f6ef7;
    }
    .stButton>button {
        width: 100%;
        background-color: #4f6ef7;
        color: white;
        border-radius: 8px;
        height: 3em;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("⚡ Ford-Fulkerson Optimizer")
st.write("Vizualizarea fluxului maxim într-o rețea de transport.")

# Datele tale inițiale (FĂRĂ coloana Flow pentru a nu induce în eroare)
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

# Layout coloane: Tabel în stânga, Control în dreapta
col_main, col_ctrl = st.columns([2, 1])

with col_ctrl:
    st.subheader("⚙️ Panou Control")
    source = st.text_input("Nod Sursă (s)", "x1")
    sink = st.text_input("Nod Destinație (t)", "x10")
    run_btn = st.button("CALCULEAZĂ ACUM")
    st.info("Algoritmul va căuta drumuri de ameliorare de la sursă la destinație până când fluxul nu mai poate fi mărit.")

with col_main:
    st.subheader("🛠️ Definire Capacități Rețea")
    # Configurăm tabelul să arate frumos
    edited_df = st.data_editor(
        st.session_state.initial_data, 
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "src": "De la (Nod)",
            "dst": "Către (Nod)",
            "cap": st.column_config.NumberColumn("Capacitate", min_value=1)
        }
    )

if run_btn:
    # Conversie date pentru algoritm
    input_data = edited_df if isinstance(edited_df, list) else edited_df.to_dict('records')
    
    ff = FordFulkersonStreamlit(input_data)
    final_edges = ff.solve(source, sink)
    
    st.divider()
    
    # Afișare Metrici
    m1, m2, m3 = st.columns(3)
    m1.metric("FLUX MAXIM TOTAL", f"{ff.max_flow}")
    m2.metric("DRUMURI GASITE", len(ff.paths_found))
    m3.metric("STATUS", "Optimizat")

    res_l, res_r = st.columns([1, 2])
    
    with res_l:
        st.write("#### 🛤️ Drumuri de Ameliorare")
        if not ff.paths_found:
            st.error("Nu există drum!")
        for idx, p in enumerate(ff.paths_found):
            with st.expander(f"Pasul {idx+1}: Δ={p['delta']}"):
                st.write(" → ".join(p['path']))

    with res_r:
        st.write("#### 📊 Reprezentare Grafică")
        dot = graphviz.Digraph()
        dot.attr(rankdir='LR', bgcolor='transparent')
        
        # Stil pentru noduri
        dot.attr('node', shape='circle', style='filled', color='#4f6ef7', fontcolor='white', fillcolor='#1e2240', width='0.6')
        
        for e in final_edges:
            f, c = e['flow'], e['cap']
            # Colorare inteligentă
            if f == 0:
                color, style, width = "#6b7299", "dashed", "1.0"
            elif f == c:
                color, style, width = "#f75c8d", "solid", "3.5" # Roz neon (Saturat)
            else:
                color, style, width = "#27c98f", "solid", "2.5" # Verde neon (Activ)
            
            label_text = f"{f}/{c}"
            dot.edge(e['src'], e['dst'], label=label_text, color=color, fontcolor=color, penwidth=width, style=style)
        
        st.graphviz_chart(dot)
    
    st.balloons()
