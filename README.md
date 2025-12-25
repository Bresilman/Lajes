PyLaje - Revisão de Estado Atual (v0.1 - Estável)

1. Visão Geral

Software modular em Python para dimensionamento e verificação de lajes de concreto armado (Maciças e Treliçadas/Nervuradas) conforme a NBR 6118:2023. O sistema utiliza uma arquitetura MVC estrita, permitindo fácil expansão para outros elementos estruturais (Vigas, Pilares).

2. Arquitetura Implementada

Padrão: MVC (Model-View-Controller) + Strategy Pattern para motores de cálculo.

Isolamento:

Models: Classes puras de dados (Laje, Materiais) com polimorfismo para cálculo de propriedades geométricas (Inércia T vs Retangular).

Engines: Física pura. Implementação desacoplada (AnalyticEngine) que pode ser substituída por FEM no futuro.

Controllers: Orquestração e fluxo de dados. Gerencia a otimização e a persistência.

DTOs: Uso de AnalysisResult para garantir integridade de dados entre camadas.

Dados Externos:

coefficients_table.json: Tabelas de Marcus/Czerny para momentos e reações.

engineering_catalogs.json: Banco de dados de vigotas, enchimentos (EPS/Cerâmica) e bitolas de aço.

3. Funcionalidades de Engenharia (Validado)

Estado Limite Último (ELU)

[x] Cálculo de Esforços: Momentos fletores ($M_x, M_y$) baseados em tabelas de coeficientes com interpolação linear para a relação de vãos ($\lambda$).

[x] Dimensionamento à Flexão: Cálculo da área de aço ($A_s$) necessária com verificação de ductilidade (Domínios 2, 3 e 4) e armadura mínima.

[x] Verificação de Cisalhamento ($V_{Rd1}$): Verificação para lajes sem armadura transversal.

Destaque: Cálculo correto da largura efetiva ($b_w$) para lajes nervuradas (soma das nervuras), garantindo segurança contra ruptura frágil.

Estado Limite de Serviço (ELS)

[x] Flecha (Deformação Excessiva): Cálculo rigoroso utilizando a Rigidez Equivalente de Branson ($I_{eq}$).

Considera fissuração ($M_a > M_r$).

Considera fluência (flecha diferida $\alpha_{fl}$).

Correção de unidades do Módulo de Elasticidade ($E_{cs}$) para $kN/m^2$.

Polimorfismo de Inércia: Lajes treliçadas usam inércia da Seção T homogeneizada.

[x] Fissuração (ELS-W): Estimativa da abertura máxima de fissuras ($w_k$) baseada na tensão da armadura na combinação frequente.

Recursos de Análise

[x] Otimizador Automático: Algoritmo que itera a espessura ($h$) para encontrar a menor altura que satisfaz simultaneamente ELU e ELS.

[x] Equilíbrio de Cargas (Load Takedown): Cálculo preciso das reações de apoio ($kN/m$) transferidas para as vigas, utilizando o método das áreas de influência (Triângulos e Trapézios).

Validação: A soma das reações iguala a carga total aplicada.

[x] Detalhamento Inteligente: Sugestão automática de bitolas e espaçamentos comerciais (ex: $\phi 6.3$ c/15).

[x] Quantitativos: Estimativa de volume de concreto ($m^3$) e peso de aço ($kg/m^2$) para orçamento.

4. Interface Gráfica (GUI)

[x] Interface responsiva em PyQt6.

[x] Entrada dinâmica: Campos mudam conforme o tipo de laje (Maciça vs Treliçada).

[x] Seleção de Agregado (Basalto, Granito, etc.) impactando o Módulo de Elasticidade.

[x] Exportação para JSON: Gera arquivo padronizado para integração com módulos futuros (Vigas).

5. Próximos Passos (Roadmap)

[ ] Implementação de Editor Visual de Grelha (Continuidade automática entre lajes vizinhas).

[ ] Adição de Cargas Lineares/Pontuais (Paredes sobre a laje).

[ ] Verificação de Punção para apoios pontuais.

Status: Versão estável pronta para commit. Erros críticos de física (unidades de flecha e inércia de nervuradas) foram corrigidos.
