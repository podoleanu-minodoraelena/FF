import streamlit as st
import collections
import graphviz

# --- LOGICA FORD-FULKERSON ---
class FordFulkersonStreamlit:
    def __init__(self, nodes, edges):
        self.nodes = nodes
        self.edges = edges # [{src, dst, cap, flow}]
        self.residual = {}
        self.max_flow = 0
        self.paths_found = []

    def build_residual(self):
        self.residual = {}
        for e in self.edges:
            fwd = (e['src'], e['dst'])
            bwd = (e['dst'], e['src'])
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
                    path.append(u)
                    u = parent[u]
                return path[::-1]
            
            # Verificăm vecinii în graful rezidual
            for (u_res, v_res), cap in self.residual.items():
                if u_res == u and cap > 0 and v_res not in parent:
                    parent[v_res] = u
                    queue.append(v_res)
        return None

    def solve(self, src, dst):
        self.max_flow = 0
        self.paths_found = []
        for e in self.edges: e['flow'] = 0
        
        while True:
            self.build_residual()
            path = self.bfs_path(src, dst)
            if not path: break
            
            # Găsim capacitatea de ameliorare (delta)
            delta = min(self.residual[(path[i], path[i+1])] for i in range(len(path)-1))
            
            # Actualizăm fluxurile
            for i in range(len(path) - 1):
                u, v = path[i], path[i+1]
                # Actualizăm în lista de margini originale
                for e in self.edges:
                    if e['src'] == u and e['dst'] == v:
                        e['flow'] += delta
                        break
                    if e['src'] == v and e['dst'] == u:
                        e['flow'] -= delta
                        break
            
            self.max_flow += delta
            self.paths_found.append({"path": path, "delta": delta})

# --- INTERFAȚA STREAMLIT ---
st.set_page_config(page_title="Ford-Fulkerson Visualizer", page_icon="🌊")
st.title("🌊 Vizualizator Ford-Fulkerson (Flux Maxim)")

# Datele tale predefinite (Matricea din PDF)
if 'edges' not in st.session_state:
    st.session_state.edges = [
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

st.sidebar.header("⚙️ Configurare")
src_node = st.sidebar.text_input("Sursă (s)", "x1")
dst_node = st.sidebar.text_input("Destinație (t)", "x10")

st.write("### 🖋️ Muchii și Capacități (Poți să le modifici)")
# Editor de tabel pentru a permite modificarea capacităților live
edited_df = st.data_editor(st.session_state.edges, num_rows="dynamic")

if st.button("🚀 Calculează Fluxul Maxim"):
    ff = FordFulkersonStreamlit(None, edited_df)
    ff.solve(src_node, dst_node)
    
    st.divider()
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.metric("Flux Maxim Total", f"{ff.max_flow}")
        st.write("#### 🛤️ Drumuri de ameliorare:")
        for idx, p in enumerate(ff.paths_found):
            st.write(f"**{idx+1}.** {' → '.join(p['path'])} (+{p['delta']})")

    with col2:
        st.write("#### 📊 Graful Rezultat")
        dot = graphviz.Digraph()
        dot.attr(rankdir='LR', bgcolor='#0e1117')
        
        for e in edited_df:
            color = "#27c98f" if e['flow'] > 0 else "#6b7299"
            if e['flow'] == e['cap'] and e['cap'] > 0: color = "#f75c8d" # Saturat
            
            label = f"{e['flow']}/{e['cap']}"
            dot.edge(e['src'], e['dst'], label=label, color=color, fontcolor=color)
        
        st.graphviz_dot_widget(dot)
        
    st.snow() # Efect vizual de succes
