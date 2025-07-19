import tkinter as tk
from tkinter import messagebox
import csv
import os

ARQUIVO_CSV = "estoque.csv"

def carregar_estoque():
    estoque = {}
    if os.path.exists(ARQUIVO_CSV):
        with open(ARQUIVO_CSV, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                nome = row['nome']
                atual = int(row['quantidade_atual'])
                maximo = int(row['quantidade_maxima'])
                estoque[nome] = {'atual': atual, 'maximo': maximo}
    return estoque
def salvar_estoque():
    with open(ARQUIVO_CSV, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['nome', 'quantidade_atual', 'quantidade_maxima']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for nome, dados in estoque.items():
            writer.writerow({
                'nome': nome,
                'quantidade_atual': dados['atual'],
                'quantidade_maxima': dados['maximo']
            })
def atualizar_lista():
    lista_estoque.delete(0, tk.END)
    for nome, dados in estoque.items():
        percentual = (dados['atual'] / dados['maximo']) * 100
        alerta = " " if percentual < 30 else ""
        texto = f"{nome} - {dados['atual']}/{dados['maximo']}{alerta}"
        lista_estoque.insert(tk.END, texto)
def adicionar_produto():
    nome = entry_nome.get().strip()
    try:
        maximo = int(entry_max.get().strip())
    except:
        messagebox.showerror("Erro", "Quantidade máxima inválida.")
        return
    if nome in estoque:
        messagebox.showwarning("Aviso", f"Produto '{nome}' já existe.")
        return
    estoque[nome] = {'atual': maximo, 'maximo': maximo}
    salvar_estoque()
    atualizar_lista()
    entry_nome.delete(0, tk.END)
    entry_max.delete(0, tk.END)

def modificar_estoque(operacao):
    nome = entry_nome_op.get().strip()
    try:
        qtd = int(entry_qtd_op.get().strip())
    except:
        messagebox.showerror("Erro", "Quantidade inválida.")
        return

    if nome not in estoque:
        messagebox.showerror("Erro", f"Produto '{nome}' não encontrado.")
        return

    if operacao == "add":
        estoque[nome]['atual'] = min(estoque[nome]['atual'] + qtd, estoque[nome]['maximo'])
    elif operacao == "remove":
        if qtd > estoque[nome]['atual']:
            messagebox.showerror("Erro", "Estoque insuficiente.")
            return
        estoque[nome]['atual'] -= qtd

    salvar_estoque()
    atualizar_lista()
    entry_nome_op.delete(0, tk.END)
    entry_qtd_op.delete(0, tk.END)

# ========== INTERFACE ==========

estoque = carregar_estoque()

root = tk.Tk()
root.title("Sistema de Estoque ")

# Frame - Adicionar Produto
frame_add = tk.LabelFrame(root, text="Adicionar Novo Produto")
frame_add.pack(padx=10, pady=10, fill="x")

tk.Label(frame_add, text="Nome:").pack(side="left")
entry_nome = tk.Entry(frame_add)
entry_nome.pack(side="left", padx=5)

tk.Label(frame_add, text="Qtd Máx:").pack(side="left")
entry_max = tk.Entry(frame_add, width=6)
entry_max.pack(side="left", padx=5)

tk.Button(frame_add, text="Adicionar", command=adicionar_produto).pack(side="left", padx=10)

# Frame - Operações
frame_op = tk.LabelFrame(root, text="Entrada / Saída de Produtos")
frame_op.pack(padx=10, pady=10, fill="x")

tk.Label(frame_op, text="Nome:").pack(side="left")
entry_nome_op = tk.Entry(frame_op)
entry_nome_op.pack(side="left", padx=5)

tk.Label(frame_op, text="Qtd:").pack(side="left")
entry_qtd_op = tk.Entry(frame_op, width=6)
entry_qtd_op.pack(side="left", padx=5)

tk.Button(frame_op, text="Adicionar Estoque", command=lambda: modificar_estoque("add")).pack(side="left", padx=5)
tk.Button(frame_op, text="Retirar Estoque", command=lambda: modificar_estoque("remove")).pack(side="left", padx=5)

# Lista de Produtos
frame_lista = tk.LabelFrame(root, text="Estoque Atual")
frame_lista.pack(padx=10, pady=10, fill="both", expand=True)

lista_estoque = tk.Listbox(frame_lista, height=10, font=("Arial", 12))
lista_estoque.pack(fill="both", expand=True)

# Iniciar interface
atualizar_lista()
root.mainloop()
