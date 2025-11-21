import sqlite3
import sys
import os
from contextlib import contextmanager
from dataclasses import dataclass, asdict
from typing import List, Tuple, Any
import tkinter as tk
from tkinter import messagebox, ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd # Para manipulação de dados em gráfico

# --- 1. Modelo de Dados e Lógica de Banco de Dados (MODELO) ---
@dataclass
class Product:
    """Modelo de dados para um produto."""
    name: str
    current_stock: int
    max_stock: int
    id: int = None

@contextmanager
def get_db_cursor(db_name: str):
    """Context Manager para conectar ao banco de dados e obter o cursor."""
    conn = None
    try:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        yield conn, cursor
    except sqlite3.Error as e:
        messagebox.showerror("Erro de Conexão", f"Não foi possível conectar ao banco de dados: {e}")
        sys.exit(1)
    finally:
        if conn:
            conn.close()

class DatabaseManager:
    """Gerencia as operações do banco de dados SQLite."""

    def __init__(self, db_name="estoque_avancado.db"):
        self.db_name = db_name
        self._setup_table()

    def _setup_table(self):
        with get_db_cursor(self.db_name) as (conn, cursor):
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS produtos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT UNIQUE NOT NULL,
                    atual INTEGER NOT NULL,
                    maximo INTEGER NOT NULL
                )
            ''')
            conn.commit()

    def _execute_query(self, query: str, params: Tuple[Any, ...] = ()) -> bool:
        try:
            with get_db_cursor(self.db_name) as (conn, cursor):
                cursor.execute(query, params)
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.IntegrityError:
            raise ValueError("Erro de Integridade: Produto com este nome já existe.")
        except sqlite3.Error as e:
            raise sqlite3.Error(f"Erro ao executar a operação no BD: {e}")

    def add_product(self, product: Product) -> Product:
        self._execute_query(
            "INSERT INTO produtos (nome, atual, maximo) VALUES (?, ?, ?)",
            (product.name, product.current_stock, product.max_stock)
        )
        with get_db_cursor(self.db_name) as (conn, cursor):
            cursor.execute("SELECT id FROM produtos WHERE nome=?", (product.name,))
            product.id = cursor.fetchone()[0]
        return product

    def update_stock(self, product_id: int, quantity: int, operation: str) -> bool:
        with get_db_cursor(self.db_name) as (conn, cursor):
            cursor.execute("SELECT atual, maximo FROM produtos WHERE id=?", (product_id,))
            res = cursor.fetchone()
            if not res:
                raise LookupError("Produto não encontrado.")

            current, maximum = res
            new_stock = current

            if operation == "add":
                new_stock = min(current + quantity, maximum)
            elif operation == "remove":
                if quantity > current:
                    raise ValueError("Estoque insuficiente para a remoção.")
                new_stock = current - quantity
            else:
                raise ValueError("Operação inválida.")
            
            cursor.execute("UPDATE produtos SET atual=? WHERE id=?", (new_stock, product_id))
            conn.commit()
            return True

    def edit_product(self, product_id: int, new_name: str, new_max: int) -> bool:
        return self._execute_query(
            "UPDATE produtos SET nome=?, maximo=? WHERE id=?",
            (new_name, new_max, product_id)
        )

    def remove_product(self, product_id: int) -> bool:
        return self._execute_query("DELETE FROM produtos WHERE id=?", (product_id,))

    def fetch_all_products(self) -> List[Product]:
        with get_db_cursor(self.db_name) as (conn, cursor):
            cursor.execute("SELECT id, nome, atual, maximo FROM produtos ORDER BY nome")
            return [Product(name=r[1], current_stock=r[2], max_stock=r[3], id=r[0]) for r in cursor.fetchall()]

    def get_product_by_name(self, name: str) -> Product:
        with get_db_cursor(self.db_name) as (conn, cursor):
            cursor.execute("SELECT id, nome, atual, maximo FROM produtos WHERE nome=?", (name,))
            r = cursor.fetchone()
            if r:
                return Product(name=r[1], current_stock=r[2], max_stock=r[3], id=r[0])
            raise LookupError("Produto não encontrado.")
            
    def get_product_by_id(self, id: int) -> Product:
        with get_db_cursor(self.db_name) as (conn, cursor):
            cursor.execute("SELECT id, nome, atual, maximo FROM produtos WHERE id=?", (id,))
            r = cursor.fetchone()
            if r:
                return Product(name=r[1], current_stock=r[2], max_stock=r[3], id=r[0])
            raise LookupError("Produto não encontrado.")

# --- 2. Lógica da Aplicação (CONTROLADOR) ---
class InventoryApp:
    """Controlador: Contém a lógica de negócio e gerencia as interações entre DB e GUI."""

    def __init__(self, db_manager: DatabaseManager, gui):
        self.db = db_manager
        self.gui = gui
        self.gui.set_controller(self)
        self.update_list()

    def add_product(self, name: str, maximum_stock: int):
        try:
            if not name or maximum_stock <= 0:
                raise ValueError("Nome e quantidade máxima devem ser válidos.")
            
            new_product = Product(name=name.capitalize(), current_stock=maximum_stock, max_stock=maximum_stock)
            self.db.add_product(new_product)
            self.gui.show_info("Sucesso", f"Produto '{name.capitalize()}' adicionado.")
            self.update_list()
            self.gui.clear_add_fields()

        except ValueError as e:
            self.gui.show_error("Erro de Validação", str(e))
        except sqlite3.IntegrityError:
             self.gui.show_warning("Aviso", f"Erro: O produto '{name.capitalize()}' já existe.")
        except Exception as e:
            self.gui.show_error("Erro", f"Erro ao adicionar produto: {e}")

    def modify_stock(self, name: str, quantity: int, operation: str):
        try:
            if not name or quantity <= 0:
                raise ValueError("Nome do produto e quantidade devem ser válidos.")

            product = self.db.get_product_by_name(name.capitalize())
            self.db.update_stock(product.id, quantity, operation)

            self.gui.show_info("Sucesso", f"Estoque de '{name.capitalize()}' atualizado.")
            self.update_list()
            self.gui.clear_stock_fields()

        except ValueError as e:
            self.gui.show_error("Erro de Estoque", str(e))
        except LookupError as e:
            self.gui.show_error("Erro de Busca", str(e))
        except Exception as e:
            self.gui.show_error("Erro", f"Erro ao modificar estoque: {e}")

    def remove_product(self, product_id: int, name: str):
        if not product_id:
            return
        
        if messagebox.askyesno("Confirmação", f"Tem certeza que deseja remover o produto '{name}'?"):
            try:
                self.db.remove_product(product_id)
                self.gui.show_info("Removido", f"Produto '{name}' removido com sucesso.")
                self.update_list()
            except Exception as e:
                self.gui.show_error("Erro", f"Erro ao remover produto: {e}")

    def edit_product(self, product_id: int, new_name: str, new_max: int):
        try:
            if not new_name or new_max <= 0:
                raise ValueError("Nome e quantidade máxima devem ser válidos.")
            
            self.db.edit_product(product_id, new_name.capitalize(), new_max)
            self.gui.show_info("Sucesso", f"Produto '{new_name.capitalize()}' editado com sucesso.")
            self.update_list()
            self.gui.destroy_edit_window()
            
        except ValueError as e:
            self.gui.show_error("Erro de Validação", str(e))
        except Exception as e:
            self.gui.show_error("Erro", f"Erro ao editar produto: {e}")

    def update_list(self, search_term=""):
        all_products = self.db.fetch_all_products()
        
        filtered_products = [
            p for p in all_products
            if search_term.lower() in p.name.lower()
        ]
        
        data = []
        for p in filtered_products:
            percent = (p.current_stock / p.max_stock) * 100
            alert = "⚠️ Baixo" if percent < 30 else ("🟢 OK" if percent > 60 else "🟡 Médio")
            data.append((p.id, p.name, p.current_stock, p.max_stock, f"{percent:.1f}%", alert))
            
        self.gui.refresh_list(data)
        self.gui.update_chart(all_products)

# --- 3. Interface Gráfica (VISÃO) ---
class InventoryGUI:
    """Cria e gerencia a interface do usuário com Tkinter."""

    def __init__(self, root):
        self.root = root
        self.root.title("💎 Sistema de Estoque Profissional - V2.0")
        self.root.geometry("1000x800")
        self.root.configure(bg="#e8e8e8")
        self.controller = None
        self.edit_window = None
        
        self._setup_style()
        self._create_widgets()

    def set_controller(self, controller):
        self.controller = controller

    def _setup_style(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TFrame", background="#e8e8e8")
        style.configure("TLabelFrame", background="#ffffff", borderwidth=2, relief="groove", font=('Arial', 10, 'bold'))
        style.configure("TLabel", background="#ffffff", font=('Arial', 10))
        style.configure("TEntry", fieldbackground="#f9f9f9")
        style.configure("Treeview.Heading", font=('Arial', 10, 'bold'), background="#34495E", foreground="white")
        style.configure("Treeview", font=('Arial', 10), rowheight=25)
        style.map('TButton', background=[('active', '#3498DB')], foreground=[('active', 'white')])
        style.configure("Custom.TButton", background="#3498DB", foreground="white", font=('Arial', 10, 'bold'))

    def _create_widgets(self):
        # Frame principal e Notebook para abas
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill="both", expand=True)

        notebook = ttk.Notebook(main_frame)
        notebook.pack(pady=10, padx=10, fill="both", expand=True)

        # --- Aba 1: Gestão de Estoque ---
        frame_gestion = ttk.Frame(notebook, padding="10")
        notebook.add(frame_gestion, text="📦 Gestão de Estoque")
        
        # Grid para frames de Input e Lista
        input_frame = ttk.Frame(frame_gestion)
        input_frame.pack(fill="x", pady=5)
        
        list_frame = ttk.Frame(frame_gestion)
        list_frame.pack(fill="both", expand=True, pady=10)

        # Adicionar Produto
        frame_add = ttk.LabelFrame(input_frame, text="➕ Adicionar Novo Produto", padding="10")
        frame_add.grid(row=0, column=0, padx=5, pady=5, sticky="EW")
        
        ttk.Label(frame_add, text="Nome:").pack(side="left", padx=5)
        self.entry_name = ttk.Entry(frame_add, width=20)
        self.entry_name.pack(side="left", padx=5)
        
        ttk.Label(frame_add, text="Qtd. Máxima:").pack(side="left", padx=5)
        self.entry_max = ttk.Entry(frame_add, width=10)
        self.entry_max.pack(side="left", padx=5)
        
        ttk.Button(frame_add, text="Adicionar", style="Custom.TButton", command=self._handle_add_product).pack(side="left", padx=10)

        # Operações de Estoque
        frame_op = ttk.LabelFrame(input_frame, text="🔄 Entrada / Saída Rápida", padding="10")
        frame_op.grid(row=1, column=0, padx=5, pady=5, sticky="EW")

        ttk.Label(frame_op, text="Nome:").pack(side="left", padx=5)
        self.entry_name_op = ttk.Entry(frame_op, width=20)
        self.entry_name_op.pack(side="left", padx=5)

        ttk.Label(frame_op, text="Qtd:").pack(side="left", padx=5)
        self.entry_qtd_op = ttk.Entry(frame_op, width=10)
        self.entry_qtd_op.pack(side="left", padx=5)
        
        ttk.Button(frame_op, text="➕ Entrada", style="Custom.TButton", command=lambda: self._handle_modify_stock("add")).pack(side="left", padx=5)
        ttk.Button(frame_op, text="➖ Saída", style="Custom.TButton", command=lambda: self._handle_modify_stock("remove")).pack(side="left", padx=5)

        # Busca
        frame_search = ttk.LabelFrame(input_frame, text="🔍 Buscar", padding="10")
        frame_search.grid(row=0, column=1, rowspan=2, padx=5, pady=5, sticky="NS")
        
        self.entry_search = ttk.Entry(frame_search, width=25)
        self.entry_search.pack(side="top", pady=5)
        self.entry_search.bind("<KeyRelease>", lambda event: self._handle_search())
        
        ttk.Button(frame_search, text="Limpar Busca", command=self.clear_search).pack(side="top", pady=5)


        # Treeview (Lista de Estoque)
        columns = ("id", "nome", "atual", "maximo", "percent", "alerta")
        self.tree = ttk.Treeview(list_frame, columns=columns, show='headings')
        self.tree.heading("id", text="ID", anchor=tk.CENTER)
        self.tree.heading("nome", text="Produto")
        self.tree.heading("atual", text="Atual", anchor=tk.CENTER)
        self.tree.heading("maximo", text="Máximo", anchor=tk.CENTER)
        self.tree.heading("percent", text="% Utilizado", anchor=tk.CENTER)
        self.tree.heading("alerta", text="Status", anchor=tk.CENTER)
        
        self.tree.column("id", width=40, anchor=tk.CENTER)
        self.tree.column("nome", width=250)
        self.tree.column("atual", width=80, anchor=tk.CENTER)
        self.tree.column("maximo", width=80, anchor=tk.CENTER)
        self.tree.column("percent", width=100, anchor=tk.CENTER)
        self.tree.column("alerta", width=100, anchor=tk.CENTER)

        self.tree.pack(side="left", fill="both", expand=True)
        
        # Scrollbar para o Treeview
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        
        # Botoes de Acao na Lista
        action_frame = ttk.Frame(list_frame, padding="5")
        action_frame.pack(side="bottom", fill="x")
        
        ttk.Button(action_frame, text="✏️ Editar Produto", command=self._handle_show_edit).pack(side="left", padx=10)
        ttk.Button(action_frame, text="🗑️ Remover Selecionado", command=self._handle_remove_product).pack(side="left", padx=10)
        
        
        # --- Aba 2: Dashboard/Gráfico ---
        frame_dashboard = ttk.Frame(notebook, padding="10")
        notebook.add(frame_dashboard, text="📈 Dashboard de Estoque")
        
        # Configurar o gráfico embutido
        self.fig, self.ax = plt.subplots(figsize=(8, 6))
        self.canvas = FigureCanvasTkAgg(self.fig, master=frame_dashboard)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(fill=tk.BOTH, expand=True)


    def _handle_add_product(self):
        name = self.entry_name.get().strip()
        try:
            maximum = int(self.entry_max.get())
            if maximum <= 0:
                raise ValueError
        except (ValueError, tk.TclError):
            self.show_error("Erro de Entrada", "A quantidade máxima deve ser um número inteiro positivo.")
            return
        self.controller.add_product(name, maximum)

    def _handle_modify_stock(self, operation):
        name = self.entry_name_op.get().strip()
        try:
            quantity = int(self.entry_qtd_op.get())
            if quantity <= 0:
                raise ValueError
        except (ValueError, tk.TclError):
            self.show_error("Erro de Entrada", "A quantidade deve ser um número inteiro positivo.")
            return
        self.controller.modify_stock(name, quantity, operation)

    def _handle_remove_product(self):
        selected_item = self.tree.focus()
        if not selected_item:
            self.show_warning("Aviso", "Selecione um produto para remover.")
            return
        
        values = self.tree.item(selected_item, 'values')
        product_id = int(values[0])
        product_name = values[1]
        self.controller.remove_product(product_id, product_name)

    def _handle_search(self):
        search_term = self.entry_search.get().strip()
        self.controller.update_list(search_term)

    def _handle_show_edit(self):
        selected_item = self.tree.focus()
        if not selected_item:
            self.show_warning("Aviso", "Selecione um produto para editar.")
            return
            
        values = self.tree.item(selected_item, 'values')
        product_id = int(values[0])
        current_name = values[1]
        current_max = values[3]
        
        self._create_edit_window(product_id, current_name, int(current_max))

    def _create_edit_window(self, product_id, name, maximum):
        if self.edit_window and self.edit_window.winfo_exists():
            self.edit_window.focus()
            return
            
        self.edit_window = tk.Toplevel(self.root)
        self.edit_window.title("✏️ Editar Produto")
        self.edit_window.geometry("350x150")
        self.edit_window.configure(bg="#ffffff")
        self.edit_window.resizable(False, False)

        frame = ttk.Frame(self.edit_window, padding="15")
        frame.pack(fill="both", expand=True)

        # Nome
        ttk.Label(frame, text="Novo Nome:").grid(row=0, column=0, sticky="W", pady=5)
        entry_name = ttk.Entry(frame, width=30)
        entry_name.insert(0, name)
        entry_name.grid(row=0, column=1, padx=5, pady=5)

        # Qtd. Máxima
        ttk.Label(frame, text="Nova Qtd. Máxima:").grid(row=1, column=0, sticky="W", pady=5)
        entry_max = ttk.Entry(frame, width=15)
        entry_max.insert(0, str(maximum))
        entry_max.grid(row=1, column=1, padx=5, pady=5)

        def save_changes():
            new_name = entry_name.get().strip()
            try:
                new_max = int(entry_max.get())
                if new_max <= 0:
                    raise ValueError
                self.controller.edit_product(product_id, new_name, new_max)
            except (ValueError, tk.TclError):
                self.show_error("Erro de Entrada", "A quantidade máxima deve ser um número inteiro positivo.")

        ttk.Button(frame, text="Salvar Alterações", style="Custom.TButton", command=save_changes).grid(row=2, column=0, columnspan=2, pady=10)

    def destroy_edit_window(self):
        if self.edit_window and self.edit_window.winfo_exists():
            self.edit_window.destroy()
            self.edit_window = None

    def update_chart(self, products: List[Product]):
        if not products:
            self.ax.clear()
            self.ax.text(0.5, 0.5, "Nenhum dado de estoque para exibir.", 
                         ha='center', va='center', fontsize=12, color='gray')
            self.ax.set_xticks([])
            self.ax.set_yticks([])
            self.canvas.draw()
            return

        df = pd.DataFrame([asdict(p) for p in products])
        df['percent'] = (df['current_stock'] / df['max_stock']) * 100

        self.ax.clear()
        
        # Usar as cores baseadas no percentual de alerta
        colors = ['#E74C3C' if p < 30 else ('#F39C12' if p < 60 else '#2ECC71') for p in df['percent']]
        
        self.ax.bar(df['name'], df['current_stock'], color=colors)
        self.ax.set_title("Estoque Atual de Produtos (Qtd)", fontsize=14)
        self.ax.set_xlabel("Produto", fontsize=10)
        self.ax.set_ylabel("Quantidade em Estoque", fontsize=10)
        self.ax.tick_params(axis='x', rotation=45, ha="right", labelsize=8)
        self.ax.grid(axis='y', linestyle='--', alpha=0.6)
        self.fig.tight_layout(pad=3.0)
        self.canvas.draw()

    def refresh_list(self, data: List[Tuple[Any, ...]]):
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        for row in data:
            product_id, name, current, maximum, percent, status = row
            tags = ()
            if status == "⚠️ Baixo":
                tags = ('low_stock',)
                self.tree.tag_configure('low_stock', background='#FADBD8') # Vermelho claro
            elif status == "🟡 Médio":
                tags = ('medium_stock',)
                self.tree.tag_configure('medium_stock', background='#FCF3CF') # Amarelo claro
            
            self.tree.insert('', tk.END, values=row, tags=tags)

    def clear_add_fields(self):
        self.entry_name.delete(0, tk.END)
        self.entry_max.delete(0, tk.END)

    def clear_stock_fields(self):
        self.entry_name_op.delete(0, tk.END)
        self.entry_qtd_op.delete(0, tk.END)

    def clear_search(self):
        self.entry_search.delete(0, tk.END)
        self.controller.update_list()

    def show_error(self, title, message):
        messagebox.showerror(title, message)

    def show_warning(self, title, message):
        messagebox.showwarning(title, message)

    def show_info(self, title, message):
        messagebox.showinfo(title, message)

# --- 4. Inicialização do Aplicativo ---
if __name__ == "__main__":
    root = tk.Tk()
    db_manager = DatabaseManager()
    gui = InventoryGUI(root)
    app = InventoryApp(db_manager, gui)
    root.mainloop()