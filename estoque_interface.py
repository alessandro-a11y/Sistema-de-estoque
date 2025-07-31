import tkinter as tk
from tkinter import messagebox
import sqlite3
import matplotlib.pyplot as plt

DB = "estoque.db"

def conectar_db():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT UNIQUE NOT NULL,
            atual INTEGER NOT NULL,
            maximo INTEGER NOT NULL
        )
    ''')
    conn.commit()
    return conn

conn = conectar_db()

def adicionar_produto():
    nome = entry_nome.get().strip().capitalize()
    try:
        maximo = int(entry_max.get())
        if maximo <= 0:
            raise ValueError
    except:
        messagebox.showerror("Erro", "Informe uma quantidade máxima válida.")
        return

    try:
        with conn:
            conn.execute("INSERT INTO produtos (nome, atual, maximo) VALUES (?, ?, ?)", (nome, maximo, maximo))
        atualizar_lista()
        limpar_campos(entry_nome, entry_max)
    except sqlite3.IntegrityError:
        messagebox.showwarning("Aviso", f"O produto '{nome}' já existe.")

def modificar_estoque(operacao):
    nome = entry_nome_op.get().strip().capitalize()
    try:
        qtd = int(entry_qtd_op.get())
        if qtd <= 0:
            raise ValueError
    except:
        messagebox.showerror("Erro", "Informe uma quantidade válida.")
        return

    cur = conn.cursor()
    cur.execute("SELECT atual, maximo FROM produtos WHERE nome=?", (nome,))
    res = cur.fetchone()
    if not res:
        messagebox.showerror("Erro", f"Produto '{nome}' não encontrado.")
        return

    atual, maximo = res
    if operacao == "add":
        novo = min(atual + qtd, maximo)
    else:
        if qtd > atual:
            messagebox.showerror("Erro", "Estoque insuficiente.")
            return
        novo = atual - qtd

    with conn:
        conn.execute("UPDATE produtos SET atual=? WHERE nome=?", (novo, nome))
    atualizar_lista()
    limpar_campos(entry_nome_op, entry_qtd_op)

def remover_produto():
    nome = entry_remover.get().strip().capitalize()
    if not nome:
        return
    with conn:
        cur = conn.execute("DELETE FROM produtos WHERE nome=?", (nome,))
        if cur.rowcount == 0:
            messagebox.showerror("Erro", f"Produto '{nome}' não encontrado.")
        else:
            messagebox.showinfo("Removido", f"Produto '{nome}' removido.")
    atualizar_lista()
    entry_remover.delete(0, tk.END)

def buscar():
    termo = entry_busca.get().strip().lower()
    lista_estoque.delete(0, tk.END)
    cur = conn.cursor()
    for nome, atual, maximo in cur.execute("SELECT nome, atual, maximo FROM produtos"):
        if termo in nome.lower():
            percentual = atual / maximo * 100
            alerta = "⚠️" if percentual < 30 else ""
            lista_estoque.insert(tk.END, f"{nome} - {atual}/{maximo} {alerta}")

def mostrar_grafico():
    cur = conn.cursor()
    cur.execute("SELECT nome, atual FROM produtos")
    dados = cur.fetchall()
    if not dados:
        messagebox.showwarning("Aviso", "Nenhum produto no estoque.")
        return

    nomes, quantidades = zip(*dados)
    plt.figure(figsize=(10, 5))
    plt.bar(nomes, quantidades, color='teal')
    plt.title("Estoque Atual")
    plt.xlabel("Produto")
    plt.ylabel("Quantidade")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

def atualizar_lista():
    lista_estoque.delete(0, tk.END)
    cur = conn.cursor()
    for nome, atual, maximo in cur.execute("SELECT nome, atual, maximo FROM produtos"):
        percentual = atual / maximo * 100
        alerta = "⚠️" if percentual < 30 else ""
        lista_estoque.insert(tk.END, f"{nome} - {atual}/{maximo} {alerta}")

def limpar_campos(*campos):
    for campo in campos:
        campo.delete(0, tk.END)

# === INTERFACE ===

root = tk.Tk()
root.title("Sistema de Estoque Profissional")
root.geometry("700x500")

# Adicionar Produto
frame_add = tk.LabelFrame(root, text="Adicionar Produto")
frame_add.pack(padx=10, pady=5, fill="x")

tk.Label(frame_add, text="Nome:").pack(side="left")
entry_nome = tk.Entry(frame_add)
entry_nome.pack(side="left", padx=5)

tk.Label(frame_add, text="Qtd Máx:").pack(side="left")
entry_max = tk.Entry(frame_add, width=6)
entry_max.pack(side="left", padx=5)

tk.Button(frame_add, text="Adicionar", command=adicionar_produto).pack(side="left", padx=10)

# Operações
frame_op = tk.LabelFrame(root, text="Entrada / Saída")
frame_op.pack(padx=10, pady=5, fill="x")

tk.Label(frame_op, text="Nome:").pack(side="left")
entry_nome_op = tk.Entry(frame_op)
entry_nome_op.pack(side="left", padx=5)

tk.Label(frame_op, text="Qtd:").pack(side="left")
entry_qtd_op = tk.Entry(frame_op, width=6)
entry_qtd_op.pack(side="left", padx=5)

tk.Button(frame_op, text="Adicionar", command=lambda: modificar_estoque("add")).pack(side="left", padx=5)
tk.Button(frame_op, text="Remover", command=lambda: modificar_estoque("remove")).pack(side="left", padx=5)

# Remoção
frame_del = tk.LabelFrame(root, text="Remover Produto")
frame_del.pack(padx=10, pady=5, fill="x")

tk.Label(frame_del, text="Nome:").pack(side="left")
entry_remover = tk.Entry(frame_del)
entry_remover.pack(side="left", padx=5)
tk.Button(frame_del, text="Remover Produto", command=remover_produto).pack(side="left", padx=5)

# Busca
frame_busca = tk.LabelFrame(root, text="Buscar Produto")
frame_busca.pack(padx=10, pady=5, fill="x")

entry_busca = tk.Entry(frame_busca)
entry_busca.pack(side="left", fill="x", expand=True, padx=5)
tk.Button(frame_busca, text="Buscar", command=buscar).pack(side="left", padx=5)
tk.Button(frame_busca, text="Todos", command=atualizar_lista).pack(side="left", padx=5)

# Lista
frame_lista = tk.LabelFrame(root, text="Estoque Atual")
frame_lista.pack(padx=10, pady=10, fill="both", expand=True)

lista_estoque = tk.Listbox(frame_lista, font=("Courier", 12))
lista_estoque.pack(fill="both", expand=True)

# Gráfico
tk.Button(root, text="📊 Mostrar Gráfico de Estoque", command=mostrar_grafico).pack(pady=5)

# Iniciar
atualizar_lista()
root.mainloop()

