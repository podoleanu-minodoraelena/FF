import streamlit as st
import collections
import graphviz
import pandas as pd

# --- LOGICA FORD-FULKERSON ---
class FordFulkersonStreamlit:
    def __init__(self, edges):
        # edges vine ca o listă de dicționare din tabelul Streamlit
        self.edges = edges 
        self.residual = {}
        self.max_flow = 0
        self.paths_found = []

    def build_residual(self):
        self.residual = {}
        for e in self.edges:
            u, v = str(e['src']), str(e['dst'])
            cap = int(e['cap'])
            flow = int(e['flow'])
            
            fwd = (u, v)
            bwd = (v, u)
            
            self.residual[fwd] = self.residual.get(fwd, 0) + (cap - flow)
            self.residual[bwd] = self.residual.get(bwd, 0) + flow

    def bfs_path(self, src, dst):
        parent = {src: None}
        queue = collections.deque([src])
        while queue:
            u = queue.popleft()
            if u == dst:
                path = []
                while u is not None:
                    path.append(u)
                    u = parent[u]
                return path[::-1]
            
            for (u_res, v_res), cap in self.residual.items():
                if u_res == u and cap > 0 and v_res not in parent:
                    parent[v_res] = u
                    queue.append(v_res)
        return None

    def solve(self, src, dst):
        self.max_flow = 0
        self.paths_found = []
        # Resetăm fluxul înainte de calcul
        for e in self.edges: 
            e['flow'] = 0
        
        while True:
            self.build_residual()
            path = self.bfs_path(src, dst)
            if not path: 
                break
            
            # Găsim capacitatea reziduală minimă pe drum (delta)
            delta = min(self.residual[(path[i], path[i+1])] for i in range(len(path)-1))
            
            # Actualizăm fluxurile în muchiile originale
            for i in range(len(path) - 1):
                u_p, v_p = path[i], path[i+1]
                for e in self.edges:
                    if str(e['src']) == u_p and str(e['dst']) == v_p:
                        e['flow'] += delta
                        break
                    elif str(e['src']) == v_p and str(e['dst']) == u_p:
                        e['flow'] -= delta
                        break
            
            self.max_flow += delta
            self.paths_found.append({"path": path, "delta": delta})

# --- INTERFAȚA STREAMLIT ---
st.set_page_config(page_title="Ford-Fulkerson Visualizer", page_icon="🌊", layout="wide")

st.title("🌊 Vizualizator Ford-Fulkerson (Flux Maxim)")
st.markdown("""
Această aplicație calculează fluxul maxim într-o rețea de transport folosind algoritmul **Ford-Fulkerson** (BFS / Edmonds-Karp).
""")

# Datele tale predefinite din problemă
if 'initial_data' not in st.session_state:
    st.session_state.initial_data = [
        {"src": "x1", "dst": "x2", "cap": 20, "flow": 0},
        {"src": "x1", "dst": "x3", "cap": 30, "flow": 0},
        {"src": "x1", "dst": "x4", "cap": 40, "flow": 0},
        {"src": "x2", "dst": "x7", "cap": 10, "flow": 0},
        {"src": "x2", "dst": "x5", "cap": 12, "flow": 0},
        {"src": "x3", "dst": "x5", "cap": 8, "flow": 0},
        {"src": "x3", "dst": "x8", "cap": 15, "flow": 0},
        {"src": "x3", "dst": "x6", "cap": 10, "flow": 0},
        {"src": "x4", "dst": "x6", "cap": 9, "flow": 0},
        {"src": "x4", "dst": "x9", "cap": 11, "flow": 0},
        {"src": "x5", "dst": "x7", "cap": 10, "flow": 0},
        {"src": "x5", "dst": "x8", "cap": 9, "flow": 0},
        {"src": "x6", "dst": "x8", "cap": 12, "flow": 0},
        {"src": "x6", "dst": "x9", "cap": 8, "flow": 0},
        {"src": "x7", "dst": "x10", "cap": 31, "flow": 0},
        {"src": "x8", "dst": "x10", "cap": 14, "flow": 0},
        {"src": "x9", "dst": "x10", "cap": 42, "flow": 0},
    ]

# Sidebar pentru control
st.sidebar.header("⚙️ Setări Noduri")
source = st.sidebar.text_input("Nod Sursă (s)", "x1")
sink = st.sidebar.text_input("Nod Destinație (t)", "x10")

st.write("### 🖋️ Editare Rețea (Capacități)")
# Tabel interactiv
edited_df = st.data_editor(st.session_state.initial_data, num_rows="dynamic")

if st.button("🚀 Calculează Flux Maxim"):
    # Convertim DataFrame-ul editat în listă de dicționare
    edges_list = edited_df if isinstance(edited_df, list) else edited_df.to_dict('records')
    
    ff = FordFulkersonStreamlit(edges_list)
    ff.solve(source, sink)
    
    st.divider()
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.metric("Flux Maxim Total", f"{ff.max_flow}")
        st.write("#### 🛤️ Drumuri de Ameliorare:")
        if not ff.paths_found:
            st.warning("Nu s-a găsit niciun drum de la sursă la destinație.")
        for idx, p in enumerate(ff.paths_found):
            st.write(f"**{idx+1}.** {' → '.join(p['path'])} (Δ={p['delta']})")

    with col2:
        st.write("#### 📊 Vizualizare Graf Rezultat")
        dot = graphviz.Digraph()
        dot.attr(rankdir='LR', bgcolor='#f0f2f6')
        
        for e in edges_list:
            f = e['flow']
            c = e['cap']
            # Logica de colorare
            edge_color = "#27c98f" if f > 0 else "#6b7299" # Verde dacă are flux, gri dacă nu
            if f == c and c > 0: 
                edge_color = "#f75c8d" # Roz/Roșu dacă e saturată
            
            dot.edge(str(e['src']), str(e['dst']), 
                     label=f"{f}/{c}", 
                     color=edge_color, 
                     fontcolor=edge_color,
                     penwidth="2.0" if f > 0 else "1.0")
        
        # FUNCȚIA CORECTĂ:
        st.graphviz_chart(dot)
        
    st.balloons()
