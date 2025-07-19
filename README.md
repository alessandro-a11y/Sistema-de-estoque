# Sistema de Controle de Estoque em Python

## Descrição

Este projeto é um **Sistema de Controle de Estoque** desenvolvido em Python, com interface gráfica simples e intuitiva utilizando a biblioteca **Tkinter**. O sistema permite o cadastro e gerenciamento de produtos, controle de entradas e saídas de estoque, além de emitir alertas automáticos quando o estoque estiver baixo (abaixo de 30% da capacidade máxima). Os dados são armazenados localmente em um arquivo CSV, garantindo persistência mesmo sem conexão com banco de dados ou internet.

---

## Funcionalidades

- **Cadastro de produtos**: Adicione novos produtos com nome e quantidade máxima em estoque.  
- **Gerenciamento de estoque**: Registre entradas e saídas de produtos, atualizando a quantidade disponível.  
- **Alerta de estoque baixo**: O sistema identifica produtos com estoque abaixo de 30% e exibe um alerta visual.  
- **Persistência de dados**: Os dados são salvos e carregados automaticamente de um arquivo CSV local (`estoque.csv`).  
- **Interface gráfica**: Desenvolvida com Tkinter para facilitar o uso, sem necessidade de conhecimentos técnicos.  
- **Simples e leve**: Ideal para pequenos negócios ou uso pessoal que precisam de um controle básico e eficiente.

---

## Tecnologias Utilizadas

- **Python 3.x**  
- **Tkinter** (interface gráfica)  
- **CSV** (para armazenamento local dos dados)

---

## Como Usar

1. Clone ou faça o download do repositório.  
2. Certifique-se de ter o Python 3 instalado no seu sistema.  
3. Execute o arquivo `estoque_interface.py`:

   ```bash
   python estoque_interface.py
Utilize a interface para:

Adicionar novos produtos.

Registrar entrada ou saída de estoque.

Monitorar o estoque atual com alertas automáticos.

Estrutura do Projeto
bash
Copiar
Editar
/sistema_estoque/
│
├── estoque_interface.py    # Código-fonte do sistema com interface Tkinter
├── estoque.csv             # Arquivo CSV com os dados do estoque
└── README.md               # Documentação do projeto
Como Gerar um Executável (.exe)
Para facilitar a distribuição, você pode converter o programa em um executável utilizando ferramentas como PyInstaller ou auto-py-to-exe:

Usando PyInstaller:

bash
Copiar
Editar
pyinstaller --onefile --windowed estoque_interface.py
Usando auto-py-to-exe (interface gráfica para PyInstaller):

bash
Copiar
Editar
auto-py-to-exe
Próximos Passos e Melhorias Futuras
Adicionar suporte a múltiplos usuários com permissões.

Integrar com banco de dados SQL para maior escalabilidade.

Implementar notificações por e-mail para alertas de estoque baixo.

Melhorar a interface gráfica com temas personalizados e responsividade.

Adicionar relatórios exportáveis em PDF ou Excel.

Licença
Este projeto é de uso exclusivo do autor, Lucas (lkznx7).
Não é permitida a cópia, modificação, distribuição ou qualquer outro uso sem autorização expressa do autor.
