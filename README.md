PyLaje 🏗️

Sistema Integrado para Dimensionamento de Lajes em Concreto Armado (NBR 6118:2023)

O PyLaje é um software open-source de engenharia estrutural desenvolvido em Python. Ele combina a agilidade do dimensionamento tabular (Métodos de Marcus/Bares) com a precisão de verificações refinadas de norma (Flecha de Branson, Fissuração, Cisalhamento em Nervuradas).

O sistema opera com uma arquitetura MVC (Model-View-Controller) robusta e foca na interoperabilidade, gerando inputs precisos para softwares de vigas e pórticos.

🚀 Funcionalidades Principais

1. Engenharia e Norma

Lajes Maciças e Nervuradas (Treliçadas): Cálculo preciso da inércia (Seção T vs Retangular).

Verificações ELU:

Flexão normal com tabelas de coeficientes interpoladas.

Verificação de Cisalhamento ($V_{Rd1}$) com largura efetiva real ($b_w$).

Verificações ELS:

Flecha Realista: Método da rigidez equivalente de Branson (fissuração) + Fluência.

Fissuração: Estimativa de abertura de fissuras ($w_k$).

Otimizador Automático: Algoritmo que itera a altura ($h$) para encontrar a solução mais econômica.

2. Modelagem de Pavimento

Editor de Grelha: Tabela inteligente para definição de múltiplas lajes.

Continuidade Automática: Detecção de lajes vizinhas para gerar engastes e aliviar momentos.

Cargas de Alvenaria: Ferramenta para desenhar paredes sobre a laje com distribuição automática de carga equivalente ($kN/m \to kN/m^2$).

Balanços: Suporte a bordas livres (marquises) com cálculo isostático.

3. Integração e Exportação

JSON para Vigas: Exporta reações de apoio ($kN/m$) e momentos de torção ($kNm/m$) com coordenadas globais para importação em softwares de pórtico.

Memorial de Cálculo: Gera relatórios detalhados em Markdown com fórmulas e quantitativos.

🛠️ Instalação e Uso

Pré-requisitos

Python 3.10 ou superior.

No Linux, bibliotecas gráficas do Qt podem ser necessárias (libxcb-cursor0).

Instalação

# Clone o repositório
git clone [https://github.com/seu-usuario/PyLaje.git](https://github.com/seu-usuario/PyLaje.git)
cd PyLaje

# Crie um ambiente virtual (Recomendado)
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# ou .venv\Scripts\activate  # Windows

# Instale as dependências
pip install -r requirements.txt


Executando

# Modo Gráfico (GUI)
python main.py

# Modo Texto (CLI - Para testes rápidos)
python main.py --cli


🧩 Estrutura do Projeto (MVC)

PyLaje/
├── app/
│   ├── models/       # Dados (Laje, Materiais, Geometria)
│   ├── engines/      # Física (AnalyticEngine NBR 6118)
│   ├── controllers/  # Orquestração (SlabController)
│   └── services/     # IO (Memorial, JSON Export, Catálogos)
├── config/           # Tabelas de Coeficientes e Settings
├── ui/               # Interface Gráfica (PyQt6)
│   ├── gui/widgets/  # Canvas de Desenho
│   └── gui/tabs/     # Abas de Editor e Calculadora
└── main.py           # Entry Point


📊 Exemplo de Fluxo de Trabalho

Aba Editor: Defina a geometria das lajes (L1, L2) e desenhe as paredes de alvenaria.

Processamento: O sistema detecta que L1 e L2 são vizinhas e cria um engaste entre elas.

Refinamento: Envie a L1 para a "Calculadora Detalhada", escolha o agregado (Basalto/Granito) e otimize a altura.

Sincronização: Salve os dados otimizados de volta ao pavimento.

Exportação: Gere o arquivo vigas.json com as cargas prontas para o dimensionamento das vigas.

🤝 Contribuição

Contribuições são bem-vindas! Sinta-se à vontade para abrir Issues ou Pull Requests para adicionar novos métodos de cálculo (ex: FEM) ou melhorias na UI.

📄 Licença

Este projeto está sob a licença MIT.
