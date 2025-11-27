import tkinter as tk
from tkinter import messagebox
from collections import deque

class MazeEditorGUI:
    def __init__(self, cols=30, rows=20, cell_size=25, tempo_ms=30):
        self.cols = cols
        self.rows = rows
        self.cell_size = cell_size
        self.tempo_ms = tempo_ms

        # Core GUI objects
        self.root = tk.Tk()
        self.root.title("Solucionador de Labirintos (BFS)")

        # Modelo de dados: ' ' caminho, '#' parede, 'S' inicio, 'E' fim
        self.labirinto = [[" " for _ in range(self.cols)] for _ in range(self.rows)]

        # IDs dos retângulos no canvas
        self.grid_cells = [[None for _ in range(self.cols)] for _ in range(self.rows)]

        # Posições especiais
        self.inicio_pos = None
        self.fim_pos = None

        # BFS state
        self.fila = None
        self.visitados = set()
        self.predecessores = {}
        self.bfs_marked = set()  # células que receberam cor de visita/fronteira
        self.job_after = None

        # Ferramenta selecionada
        self.tool_var = tk.StringVar(value='wall')

        # Cores
        self.colors = {
            'wall': '#1E3A5F',         # parede
            'path': '#FFFFFF',         # caminho
            'start': '#4CAF50',        # inicio
            'end': '#F44336',          # fim
            'frontier': '#AED6F1',     # na fila
            'visited': '#D6EAF8',      # visitado
            'final': '#FFD700'         # caminho final
        }

        self._build_ui()
        self._draw_grid_initial()

    def _build_ui(self):
        control_frame = tk.Frame(self.root)
        control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=6, pady=6)

        tk.Label(control_frame, text="Ferramenta:").pack(anchor='w')
        tools = [
            ('Parede (#)', 'wall'),
            ('Caminho ( )', 'path'),
            ('Início (S)', 'start'),
            ('Fim (E)', 'end'),
        ]
        for text, val in tools:
            rb = tk.Radiobutton(control_frame, text=text, variable=self.tool_var, value=val)
            rb.pack(anchor='w')

        tk.Button(control_frame, text='Iniciar Busca (BFS)', command=self.iniciar_busca).pack(fill='x', pady=(8,2))
        tk.Button(control_frame, text='Resetar Busca', command=self.resetar_busca).pack(fill='x', pady=2)
        tk.Button(control_frame, text='Limpar Labirinto', command=self.limpar_labirinto).pack(fill='x', pady=2)

        # Canvas
        canvas_w = self.cols * self.cell_size
        canvas_h = self.rows * self.cell_size
        self.canvas = tk.Canvas(self.root, width=canvas_w, height=canvas_h, bg='white')
        self.canvas.pack(side=tk.RIGHT, padx=6, pady=6)

        # Eventos
        self.canvas.bind('<Button-1>', self.handle_draw)
        self.canvas.bind('<B1-Motion>', self.handle_draw)

        # Keep references to radiobuttons and buttons for enabling/disabling
        self.control_children = control_frame.winfo_children()

    def _draw_grid_initial(self):
        for r in range(self.rows):
            for c in range(self.cols):
                x1 = c * self.cell_size
                y1 = r * self.cell_size
                x2 = x1 + self.cell_size
                y2 = y1 + self.cell_size
                rect = self.canvas.create_rectangle(x1, y1, x2, y2, fill=self.colors['path'], outline='#CCCCCC')
                self.grid_cells[r][c] = rect

    def handle_draw(self, event):
        c = event.x // self.cell_size
        r = event.y // self.cell_size
        if 0 <= r < self.rows and 0 <= c < self.cols:
            self.editar_celula(r, c, self.tool_var.get())

    def editar_celula(self, r, c, tool):
        current = self.labirinto[r][c]
        # If BFS running, ignore edits
        if self.job_after is not None:
            return

        if tool == 'wall':
            self.labirinto[r][c] = '#'
            self._color_cell(r, c, self.colors['wall'])
        elif tool == 'path':
            # If removing S or E, clear positions
            if current == 'S':
                self.inicio_pos = None
            if current == 'E':
                self.fim_pos = None
            self.labirinto[r][c] = ' '
            self._color_cell(r, c, self.colors['path'])
        elif tool == 'start':
            # Clear old start
            if self.inicio_pos is not None:
                r0, c0 = self.inicio_pos
                self.labirinto[r0][c0] = ' '
                self._color_cell(r0, c0, self.colors['path'])
            # If placing on end, clear end
            if self.labirinto[r][c] == 'E':
                self.fim_pos = None
            self.labirinto[r][c] = 'S'
            self.inicio_pos = (r, c)
            self._color_cell(r, c, self.colors['start'])
        elif tool == 'end':
            # Clear old end
            if self.fim_pos is not None:
                r0, c0 = self.fim_pos
                self.labirinto[r0][c0] = ' '
                self._color_cell(r0, c0, self.colors['path'])
            # If placing on start, clear start
            if self.labirinto[r][c] == 'S':
                self.inicio_pos = None
            self.labirinto[r][c] = 'E'
            self.fim_pos = (r, c)
            self._color_cell(r, c, self.colors['end'])

    def _color_cell(self, r, c, color):
        rect = self.grid_cells[r][c]
        self.canvas.itemconfig(rect, fill=color)

    def iniciar_busca(self):
        # Locate S and E
        if self.inicio_pos is None or self.fim_pos is None:
            messagebox.showwarning('Atenção', 'Defina posições de Início (S) e Fim (E) antes de iniciar a busca.')
            return

        # Disable editing controls while BFS runs
        self._set_controls_state('disabled')

        self.fila = deque()
        self.visitados = set()
        self.predecessores = {}
        self.bfs_marked = set()

        s_r, s_c = self.inicio_pos
        self.fila.append((s_r, s_c))
        self.visitados.add((s_r, s_c))
        # mark start as visited but leave green color
        self.job_after = None

        # Start stepping
        self.processar_passo_bfs()

    def processar_passo_bfs(self):
        # If queue empty: not found
        if not self.fila:
            self.job_after = None
            messagebox.showinfo('Resultado', 'Caminho não encontrado.')
            self._set_controls_state('normal')
            return

        r, c = self.fila.popleft()

        # If this is not S/E, color as visited
        if (r, c) != self.inicio_pos and (r, c) != self.fim_pos:
            self._color_cell(r, c, self.colors['visited'])
            self.bfs_marked.add((r, c))

        # Check neighbors
        for dr, dc in ((-1,0),(1,0),(0,-1),(0,1)):
            nr, nc = r + dr, c + dc
            if not (0 <= nr < self.rows and 0 <= nc < self.cols):
                continue
            if (nr, nc) in self.visitados:
                continue
            cell = self.labirinto[nr][nc]
            # Walls are blocked
            if cell == '#':
                continue
            # Mark predecessor and visited
            self.predecessores[(nr, nc)] = (r, c)
            self.visitados.add((nr, nc))
            # If neighbor is the end
            if (nr, nc) == self.fim_pos:
                # reconstruct path
                self._color_cell(nr, nc, self.colors['end'])
                self.reconstruir_caminho()
                self._set_controls_state('normal')
                self.job_after = None
                return
            # Otherwise color frontier and enqueue
            if (nr, nc) != self.inicio_pos:
                self._color_cell(nr, nc, self.colors['frontier'])
                self.bfs_marked.add((nr, nc))
            self.fila.append((nr, nc))

        # Schedule next step
        self.job_after = self.root.after(self.tempo_ms, self.processar_passo_bfs)

    def reconstruir_caminho(self):
        # Trace from end back to start
        node = self.fim_pos
        path = []
        while node != self.inicio_pos and node in self.predecessores:
            path.append(node)
            node = self.predecessores[node]
        path.append(self.inicio_pos)
        # Paint path (exclude S and E colors if desired)
        for (r, c) in path:
            if (r, c) == self.inicio_pos:
                self._color_cell(r, c, self.colors['start'])
            elif (r, c) == self.fim_pos:
                self._color_cell(r, c, self.colors['end'])
            else:
                self._color_cell(r, c, self.colors['final'])
        messagebox.showinfo('Resultado', 'Caminho encontrado!')

    def resetar_busca(self):
        # Cancel any running job
        if self.job_after is not None:
            try:
                self.root.after_cancel(self.job_after)
            except Exception:
                pass
            self.job_after = None

        # Reset colors of visited/fronteira/final but keep paredes e S/E
        for (r, c) in list(self.bfs_marked):
            # don't overwrite walls, S, E
            if self.labirinto[r][c] == '#':
                self._color_cell(r, c, self.colors['wall'])
            else:
                self._color_cell(r, c, self.colors['path'])
        self.bfs_marked.clear()

        # Also clear any path-colored cells (final)
        for r in range(self.rows):
            for c in range(self.cols):
                if self.labirinto[r][c] == ' ':
                    rect = self.grid_cells[r][c]
                    current_color = self.canvas.itemcget(rect, 'fill')
                    if current_color == self.colors['final']:
                        self._color_cell(r, c, self.colors['path'])
        # Clear BFS structures
        self.fila = None
        self.visitados = set()
        self.predecessores = {}
        # Re-enable controls
        self._set_controls_state('normal')

    def limpar_labirinto(self):
        # Cancel any running job
        if self.job_after is not None:
            try:
                self.root.after_cancel(self.job_after)
            except Exception:
                pass
            self.job_after = None

        self.labirinto = [[" " for _ in range(self.cols)] for _ in range(self.rows)]
        self.inicio_pos = None
        self.fim_pos = None
        self.bfs_marked.clear()
        self.fila = None
        self.visitados = set()
        self.predecessores = {}
        # Redraw colors
        for r in range(self.rows):
            for c in range(self.cols):
                self._color_cell(r, c, self.colors['path'])
        self._set_controls_state('normal')

    def _set_controls_state(self, state):
        # state: 'normal' or 'disabled'
        for child in self.control_children:
            try:
                child.configure(state=state)
            except Exception:
                pass

    def run(self):
        self.root.mainloop()


if __name__ == '__main__':
    app = MazeEditorGUI()
    app.run()
