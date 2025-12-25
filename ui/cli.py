from app.models.ribbed import LajeTrelicada
from app.models.value_objects import Materiais, Carregamento, ClasseAgressividade, CondicaoContorno
from app.engines.analytic import AnalyticEngine
from app.controllers.slab_controller import SlabController
from app.services.report_formatter import ReportFormatter
from app.services.catalog_service import catalog_service

def run_cli_interface():
    """
    Executa a simulação via terminal (Modo Texto).
    Útil para testes rápidos ou debug sem abrir janelas.
    """
    print(">>> INICIANDO PYLAJE EM MODO CLI (TEXTO) <<<")

    # 1. Setup inicial
    lajota = catalog_service.get_modelo_enchimento("H8_25_30")
    if not lajota:
        # Fallback caso o JSON não esteja populado
        lajota = {"altura_h_cm": 8.0, "largura_b_cm": 25.0, "peso_unitario_kg": 3.4}

    # 2. Criar o Modelo
    mat = Materiais(fck=25, fyk=500, Ecs=23.8)
    cargas = Carregamento(g_revestimento=1.2, q_acidental=2.0)
    
    # Exemplo com bordas mistas para testar coeficientes
    bordas = {
        'esquerda': "engastado", 'direita': "apoiado",
        'topo': "apoiado", 'fundo': "apoiado"
    }

    laje = LajeTrelicada(
        lx=3.80, ly=4.50,
        materiais=mat,
        caa=ClasseAgressividade.II,
        bordas=bordas,
        carregamento=cargas,
        h_capa=0.04,
        largura_sapata=0.125,
        dados_enchimento=lajota
    )

    # 3. Inicializar Controller
    engine = AnalyticEngine()
    controller = SlabController(laje, engine)

    # 4. Executar Análise
    print("Analisando laje treliçada...")
    resultado = controller.run_analysis()

    # 5. Exibir
    relatorio = ReportFormatter.format_as_text(resultado)
    print(relatorio)

    # 6. Otimização
    print("\nBuscando espessura econômica...")
    h_otimo = controller.optimize_thickness()
    if h_otimo:
        print(f"Sugestão de projeto: h = {h_otimo*100:.0f} cm")
    else:
        print("Não foi possível otimizar dentro dos limites.")