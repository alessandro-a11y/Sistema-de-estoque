import os
import shutil
import sys
import argparse
from fastapi import FastAPI, HTTPException
import uvicorn
import threading
import tkinter as tk
from tkinter import messagebox, ttk
import sqlite3
import matplotlib.pyplot as plt

# --- 1. Lógica do Banco de Dados ---
class DatabaseManager:
    """Gerencia as operações do banco de dados SQLite."""

    def __init__(self, db_name="estoque.db"):
        self.db_name = db_name
        self.conn = self._connect()
        self._setup_table()

    def _connect(self):
        """Conecta-se ao banco de dados."""
        try:
            return sqlite3.connect(self.db_name)
        except sqlite3.Error as e:
            messagebox.showerror("Erro de Conexão", f"Não foi possível conectar ao banco de dados: {e}")
            sys.exit(1)

    def _setup_table(self):
        """Cria a tabela de produtos se ela não existir."""
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS produtos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT UNIQUE NOT NULL,
                atual INTEGER NOT NULL,
                maximo INTEGER NOT NULL
            )
        ''')
        self.conn.commit()

    def add_product(self, name, current, maximum):
        """Adiciona um novo produto ao estoque."""
        try:
            with self.conn:
                self.conn.execute(
                    "INSERT INTO produtos (nome, atual, maximo) VALUES (?, ?, ?)",
                    (name, current, maximum)
                )
            return True, "Produto adicionado com sucesso."
        except sqlite3.IntegrityError:
            return False, f"Erro: O produto '{name}' já existe."
        except sqlite3.Error as e:
            return False, f"Erro ao adicionar o produto: {e}"

    def update_stock(self, name, quantity, operation="add"):
        """Modifica a quantidade de estoque de um produto."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT atual, maximo FROM produtos WHERE nome=?", (name,))
            res = cursor.fetchone()
            if not res:
                return False, f"Erro: Produto '{name}' não encontrado."

            current, maximum = res
            new_stock = current
            if operation == "add":
                new_stock = min(current + quantity, maximum)
            elif operation == "remove":
                if quantity > current:
                    return False, "Erro: Estoque insuficiente."
                new_stock = current - quantity
            
            with self.conn:
                self.conn.execute("UPDATE produtos SET atual=? WHERE nome=?", (new_stock, name))
            return True, f"Estoque de '{name}' atualizado."
        except sqlite3.Error as e:
            return False, f"Erro ao atualizar o estoque: {e}"

    def remove_product(self, name):
        """Remove um produto do estoque."""
        try:
            with self.conn:
                cursor = self.conn.execute("DELETE FROM produtos WHERE nome=?", (name,))
                if cursor.rowcount == 0:
                    return False, f"Erro: Produto '{name}' não encontrado."
            return True, f"Produto '{name}' removido com sucesso."
        except sqlite3.Error as e:
            return False, f"Erro ao remover o produto: {e}"

    def fetch_all_products(self):
        """Retorna todos os produtos do banco de dados."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT nome, atual, maximo FROM produtos ORDER BY nome")
        return cursor.fetchall()

# --- 2. Lógica da Aplicação (App Logic) ---
class InventoryApp:
    """Contém a lógica de negócio e as funções para manipular o estoque."""

    def __init__(self, db_manager, gui):
        self.db = db_manager
        self.gui = gui
        self.gui.set_controller(self)
        self.update_list()

    def add_product(self, name, maximum_stock):
        if not name or maximum_stock <= 0:
            messagebox.showerror("Erro", "Nome e quantidade máxima devem ser válidos.")
            return

        success, msg = self.db.add_product(name, maximum_stock, maximum_stock)
        if not success:
            messagebox.showwarning("Aviso", msg)
        
        self.update_list()
        self.gui.clear_add_fields()

    def modify_stock(self, name, quantity, operation):
        if not name or quantity <= 0:
            messagebox.showerror("Erro", "Nome e quantidade devem ser válidos.")
            return

        success, msg = self.db.update_stock(name, quantity, operation)
        if not success:
            messagebox.showerror("Erro", msg)

        self.update_list()
        self.gui.clear_stock_fields()

    def remove_product(self, name):
        if not name:
            return
        
        success, msg = self.db.remove_product(name)
        if not success:
            messagebox.showerror("Erro", msg)
        else:
            messagebox.showinfo("Removido", msg)
        
        self.update_list()
        self.gui.clear_remove_field()

    def update_list(self, search_term=""):
        self.gui.clear_list()
        all_products = self.db.fetch_all_products()
        
        filtered_products = [
            (name, current, maximum) for name, current, maximum in all_products
            if search_term.lower() in name.lower()
        ]
        
        for name, current, maximum in filtered_products:
            percent = (current / maximum) * 100
            alert = "⚠️" if percent < 30 else ""
            self.gui.list_product(f"{name} - {current}/{maximum} {alert}")

    def show_chart(self):
        products = self.db.fetch_all_products()
        if not products:
            messagebox.showwarning("Aviso", "Nenhum produto no estoque para exibir no gráfico.")
            return

        names, quantities = zip(*[(p[0], p[1]) for p in products])
        
        plt.figure(figsize=(10, 6))
        plt.bar(names, quantities, color='teal')
        plt.title("Estoque Atual de Produtos")
        plt.xlabel("Produto")
        plt.ylabel("Quantidade em Estoque")
        plt.xticks(rotation=45, ha="right")
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        plt.tight_layout()
        plt.show()

# --- 3. Interface Gráfica (GUI) ---
class InventoryGUI:
    """Cria e gerencia a interface do usuário com Tkinter."""

    def __init__(self, root):
        self.root = root
        self.root.title("Sistema de Estoque Profissional")
        self.root.geometry("750x600")
        self.root.configure(bg="#f0f0f0")
        self.controller = None
        self._create_widgets()

    def set_controller(self, controller):
        self.controller = controller

    def _create_widgets(self):
        # Frame principal com padding
        main_frame = ttk.Frame(self.root, padding="15 15 15 15")
        main_frame.pack(fill="both", expand=True)

        # Adicionar Produto
        frame_add = ttk.LabelFrame(main_frame, text="📦 Adicionar Novo Produto", padding="10 10")
        frame_add.pack(padx=5, pady=5, fill="x")
        
        ttk.Label(frame_add, text="Nome:").grid(row=0, column=0, sticky="W", padx=5, pady=5)
        self.entry_name = ttk.Entry(frame_add, width=30)
        self.entry_name.grid(row=0, column=1, sticky="EW", padx=5, pady=5)
        
        ttk.Label(frame_add, text="Qtd. Máxima:").grid(row=0, column=2, sticky="W", padx=5, pady=5)
        self.entry_max = ttk.Entry(frame_add, width=10)
        self.entry_max.grid(row=0, column=3, sticky="EW", padx=5, pady=5)
        
        ttk.Button(frame_add, text="Adicionar", command=self._handle_add_product).grid(row=0, column=4, padx=10, pady=5)

        # Operações de Estoque
        frame_op = ttk.LabelFrame(main_frame, text="🔄 Entrada / Saída de Estoque", padding="10 10")
        frame_op.pack(padx=5, pady=5, fill="x")

        ttk.Label(frame_op, text="Nome do Produto:").grid(row=0, column=0, sticky="W", padx=5, pady=5)
        self.entry_name_op = ttk.Entry(frame_op, width=30)
        self.entry_name_op.grid(row=0, column=1, sticky="EW", padx=5, pady=5)

        ttk.Label(frame_op, text="Quantidade:").grid(row=0, column=2, sticky="W", padx=5, pady=5)
        self.entry_qtd_op = ttk.Entry(frame_op, width=10)
        self.entry_qtd_op.grid(row=0, column=3, sticky="EW", padx=5, pady=5)
        
        ttk.Button(frame_op, text="Adicionar", command=lambda: self._handle_modify_stock("add")).grid(row=0, column=4, padx=5, pady=5)
        ttk.Button(frame_op, text="Remover", command=lambda: self._handle_modify_stock("remove")).grid(row=0, column=5, padx=5, pady=5)

        # Remoção de Produto
        frame_del = ttk.LabelFrame(main_frame, text="🗑️ Remover Produto", padding="10 10")
        frame_del.pack(padx=5, pady=5, fill="x")

        ttk.Label(frame_del, text="Nome:").grid(row=0, column=0, sticky="W", padx=5, pady=5)
        self.entry_remove = ttk.Entry(frame_del, width=40)
        self.entry_remove.grid(row=0, column=1, sticky="EW", padx=5, pady=5)
        
        ttk.Button(frame_del, text="Remover", command=self._handle_remove_product).grid(row=0, column=2, padx=10, pady=5)

        # Busca e Lista de Estoque
        frame_list_search = ttk.Frame(main_frame)
        frame_list_search.pack(padx=5, pady=5, fill="both", expand=True)

        frame_search = ttk.LabelFrame(frame_list_search, text="🔍 Buscar Produto", padding="10 10")
        frame_search.pack(fill="x", pady=5)
        
        self.entry_search = ttk.Entry(frame_search)
        self.entry_search.pack(side="left", fill="x", expand=True, padx=5)
        
        ttk.Button(frame_search, text="Buscar", command=self._handle_search).pack(side="left", padx=5)
        ttk.Button(frame_search, text="Limpar Busca", command=self.clear_search).pack(side="left", padx=5)

        frame_list = ttk.LabelFrame(frame_list_search, text="📊 Estoque Atual", padding="10 10")
        frame_list.pack(fill="both", expand=True, pady=5)

        self.listbox = tk.Listbox(frame_list, font=("Courier", 12), bg="#ffffff", bd=0, highlightthickness=0)
        self.listbox.pack(fill="both", expand=True, padx=5, pady=5)
        
        scrollbar = ttk.Scrollbar(self.listbox, orient="vertical", command=self.listbox.yview)
        self.listbox.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        
        # Botão de Gráfico
        ttk.Button(main_frame, text="📈 Mostrar Gráfico de Estoque", command=self._handle_show_chart).pack(pady=10)
        
    def _handle_add_product(self):
        name = self.entry_name.get().strip().capitalize()
        try:
            maximum = int(self.entry_max.get())
            if maximum <= 0:
                raise ValueError
        except (ValueError, tk.TclError):
            messagebox.showerror("Erro de Entrada", "A quantidade máxima deve ser um número inteiro positivo.")
            return
        self.controller.add_product(name, maximum)

    def _handle_modify_stock(self, operation):
        name = self.entry_name_op.get().strip().capitalize()
        try:
            quantity = int(self.entry_qtd_op.get())
            if quantity <= 0:
                raise ValueError
        except (ValueError, tk.TclError):
            messagebox.showerror("Erro de Entrada", "A quantidade deve ser um número inteiro positivo.")
            return
        self.controller.modify_stock(name, quantity, operation)

    def _handle_remove_product(self):
        name = self.entry_remove.get().strip().capitalize()
        self.controller.remove_product(name)

    def _handle_search(self):
        search_term = self.entry_search.get().strip()
        self.controller.update_list(search_term)

    def _handle_show_chart(self):
        self.controller.show_chart()

    def clear_add_fields(self):
        self.entry_name.delete(0, tk.END)
        self.entry_max.delete(0, tk.END)

    def clear_stock_fields(self):
        self.entry_name_op.delete(0, tk.END)
        self.entry_qtd_op.delete(0, tk.END)

    def clear_remove_field(self):
        self.entry_remove.delete(0, tk.END)

    def clear_search(self):
        self.entry_search.delete(0, tk.END)
        self.controller.update_list()

    def clear_list(self):
        self.listbox.delete(0, tk.END)

    def list_product(self, product_string):
        self.listbox.insert(tk.END, product_string)

# --- 4. Inicialização do Aplicativo ---
if __name__ == "__main__":
    root = tk.Tk()
    db_manager = DatabaseManager()
    gui = InventoryGUI(root)
    app = InventoryApp(db_manager, gui)
    root.mainloop()