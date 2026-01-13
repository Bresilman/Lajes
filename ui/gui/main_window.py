import sys
import os
import math
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QLineEdit, QComboBox, 
                             QPushButton, QTabWidget, QGroupBox, QTextEdit, 
                             QFormLayout, QMessageBox, QCheckBox, QFileDialog)
from PyQt6.QtCore import Qt

# Importações dos Modelos e Serviços
from app.models.value_objects import Materiais, Carregamento, ClasseAgressividade, CondicaoContorno
from app.models.solid import LajeMacica
from app.models.ribbed import LajeTrelicada
from app.engines.analytic import AnalyticEngine
from app.controllers.slab_controller import SlabController
from app.services.report_formatter import ReportFormatter
from app.services.catalog_service import catalog_service
from app.services.memorial_service import MemorialService
from ui.gui.tabs.floor_editor import FloorEditorTab

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyLaje 2024 - Sistema Integrado de Engenharia")
        self.setGeometry(50, 50, 1300, 850)
        self.current_result = None 
        
        # Referências para sincronização com o Editor de Pavimento
        self.laje_pavimento_ref = None 
        self.laje_pavimento_idx = -1

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        self.main_tabs = QTabWidget()
        
        # Aba 1: Editor de Pavimento (Grelha Global)
        self.tab_floor_editor = FloorEditorTab()
        # CONEXÃO: Recebe a laje do editor para detalhamento
        self.tab_floor_editor.laje_selecionada_signal.connect(self.importar_laje_para_calculadora)
        self.main_tabs.addTab(self.tab_floor_editor, "1. Editor de Pavimento (Grelha)")
        
        # Aba 2: Calculadora Detalhada (Laje Individual)
        self.tab_single_calc = QWidget()
        self.setup_single_calc_ui()
        self.main_tabs.addTab(self.tab_single_calc, "2. Calculadora Detalhada")
        
        self.main_layout.addWidget(self.main_tabs)

    def setup_single_calc_ui(self):
        layout = QHBoxLayout(self.tab_single_calc)
        
        # --- PAINEL DE ENTRADA (Esquerda) ---
        self.left_panel = QWidget()
        self.left_layout = QVBoxLayout(self.left_panel)
        self.left_panel.setFixedWidth(450)
        
        self.combo_tipo = QComboBox()
        self.combo_tipo.addItems(["Laje Maciça", "Laje Treliçada"])
        self.combo_tipo.currentIndexChanged.connect(self.toggle_inputs_por_tipo)
        self.left_layout.addWidget(QLabel("<b>Tipo de Estrutura:</b>"))
        self.left_layout.addWidget(self.combo_tipo)

        self.calc_tabs = QTabWidget()
        self.setup_tab_geometria()
        self.setup_tab_cargas_materiais()
        self.setup_tab_detalhes()
        self.left_layout.addWidget(self.calc_tabs)

        # Botões de Ação
        self.btn_calcular = QPushButton("Calcular Análise Detalhada")
        self.btn_calcular.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 10px;")
        self.btn_calcular.clicked.connect(self.run_calculation)
        
        self.btn_otimizar = QPushButton("Otimizar Espessura (h)")
        self.btn_otimizar.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold; padding: 10px;")
        self.btn_otimizar.clicked.connect(self.run_optimization)

        # Botão de Sincronização (Voltar para o Pavimento)
        self.btn_sync = QPushButton("Salvar Alterações no Pavimento")
        self.btn_sync.setStyleSheet("background-color: #9C27B0; color: white; font-weight: bold; padding: 10px;")
        self.btn_sync.clicked.connect(self.sincronizar_com_pavimento)
        self.btn_sync.setEnabled(False) 

        # Botões de Exportação
        hbox_export = QHBoxLayout()
        self.btn_export_json = QPushButton("JSON (Integração)")
        self.btn_export_json.clicked.connect(self.export_data_json)
        self.btn_export_json.setEnabled(False)
        
        self.btn_export_memorial = QPushButton("Memorial (Markdown)")
        self.btn_export_memorial.clicked.connect(self.export_memorial_md)
        self.btn_export_memorial.setEnabled(False)
        
        hbox_export.addWidget(self.btn_export_json)
        hbox_export.addWidget(self.btn_export_memorial)

        self.left_layout.addWidget(self.btn_calcular)
        self.left_layout.addWidget(self.btn_otimizar)
        self.left_layout.addWidget(self.btn_sync)
        self.left_layout.addLayout(hbox_export)
        self.left_layout.addStretch()

        # --- PAINEL DE RESULTADOS (Direita) ---
        self.right_panel = QWidget()
        self.right_layout = QVBoxLayout(self.right_panel)
        self.text_report = QTextEdit()
        self.text_report.setReadOnly(True)
        self.text_report.setStyleSheet("font-family: 'Consolas', monospace; font-size: 11px; background-color: #f9f9f9;")
        self.right_layout.addWidget(QLabel("<b>Resultados Detalhados:</b>"))
        self.right_layout.addWidget(self.text_report)

        layout.addWidget(self.left_panel)
        layout.addWidget(self.right_panel)
        self.toggle_inputs_por_tipo()

    def importar_laje_para_calculadora(self, data_packet):
        """
        Recebe os dados do Editor e preenche os campos desta aba.
        CORREÇÃO: Lida com a tupla (laje_pos, row_idx).
        """
        # Desempacota a tupla recebida do sinal
        if isinstance(data_packet, tuple):
            laje_pos, row_idx = data_packet
            self.laje_pavimento_idx = row_idx
        else:
            # Fallback caso receba apenas o objeto (compatibilidade)
            laje_pos = data_packet
            self.laje_pavimento_idx = -1

        self.laje_pavimento_ref = laje_pos
        self.btn_sync.setEnabled(True)
        
        laje = laje_pos.laje
        
        # 1. Troca para a aba da Calculadora
        self.main_tabs.setCurrentIndex(1)
        
        # 2. Preenche Geometria
        self.input_lx.setText(str(laje.lx))
        self.input_ly.setText(str(laje.ly))
        
        # 3. Preenche Bordas
        self.chk_esq.setChecked(laje.bordas.get('esquerda') == "engastado")
        self.chk_dir.setChecked(laje.bordas.get('direita') == "engastado")
        self.chk_top.setChecked(laje.bordas.get('topo') == "engastado")
        self.chk_bot.setChecked(laje.bordas.get('fundo') == "engastado")
        
        # 4. Preenche Cargas
        # Nota: Mostramos a soma (Base + Paredes) para que o cálculo bata
        total_g = laje.carregamento.g_revestimento + laje.carregamento.g_paredes
        self.input_g.setText(f"{total_g:.2f}")
        self.input_q.setText(str(laje.carregamento.q_acidental))
        
        if laje.carregamento.g_paredes > 0:
            self.statusBar().showMessage(f"Laje importada com carga adicional de paredes: {laje.carregamento.g_paredes:.2f} kN/m²", 8000)

        # 5. Preenche Tipo e Espessura
        if isinstance(laje, LajeMacica):
            self.combo_tipo.setCurrentText("Laje Maciça")
            self.input_h_macica.setText(f"{laje.h * 100:.1f}")
        elif isinstance(laje, LajeTrelicada):
            self.combo_tipo.setCurrentText("Laje Treliçada")
            self.input_h_capa.setText(f"{laje.h_capa * 100:.1f}")
            self.input_b_sapata.setText(f"{laje.largura_sapata * 100:.1f}")
        
        # Executa um cálculo inicial
        self.run_calculation()

    def sincronizar_com_pavimento(self):
        """Salva as alterações (ex: nova espessura) de volta no objeto do pavimento."""
        if not self.laje_pavimento_ref: return
        
        nova_laje = self.get_user_data()
        if nova_laje:
            # Preserva carga de parede original
            g_paredes_original = self.laje_pavimento_ref.laje.carregamento.g_paredes
            nova_laje.carregamento.g_paredes = g_paredes_original
            
            # Recalcula g_base (subtraindo parede) para não duplicar na tabela
            g_input_calculadora = nova_laje.carregamento.g_revestimento
            g_base_real = g_input_calculadora - g_paredes_original
            nova_laje.carregamento.g_revestimento = g_base_real
            
            # Atualiza referência
            self.laje_pavimento_ref.laje = nova_laje
            
            # Atualiza visual da tabela na outra aba
            self.tab_floor_editor.atualizar_linha_tabela(self.laje_pavimento_idx, nova_laje)
            
            QMessageBox.information(self, "Sincronizado", 
                f"Laje {self.laje_pavimento_ref.id} atualizada!\n"
                f"Nova espessura: {nova_laje.h*100:.1f} cm")

    # --- Métodos de UI ---
    def setup_tab_geometria(self):
        self.tab_geo = QWidget()
        layout = QFormLayout()
        self.input_lx = QLineEdit("4.00")
        self.input_ly = QLineEdit("5.00")
        self.group_bordas = QGroupBox("Condições de Apoio")
        vbox_bordas = QVBoxLayout()
        self.chk_esq = QCheckBox("Esquerda (Contínua/Engastada)")
        self.chk_dir = QCheckBox("Direita (Contínua/Engastada)")
        self.chk_top = QCheckBox("Topo (Contínua/Engastada)")
        self.chk_bot = QCheckBox("Fundo (Contínua/Engastada)")
        vbox_bordas.addWidget(self.chk_esq); vbox_bordas.addWidget(self.chk_dir)
        vbox_bordas.addWidget(self.chk_top); vbox_bordas.addWidget(self.chk_bot)
        self.group_bordas.setLayout(vbox_bordas)
        layout.addRow("Vão Lx (m):", self.input_lx)
        layout.addRow("Vão Ly (m):", self.input_ly)
        layout.addRow(self.group_bordas)
        self.tab_geo.setLayout(layout)
        self.calc_tabs.addTab(self.tab_geo, "Vãos")

    def setup_tab_cargas_materiais(self):
        self.tab_mat = QWidget()
        layout = QFormLayout()
        self.input_g = QLineEdit("1.0")
        self.input_q = QLineEdit("2.0")
        self.input_fck = QComboBox()
        self.input_fck.addItems(["20", "25", "30", "35", "40"])
        self.input_fck.setCurrentText("25")
        
        self.combo_agregado = QComboBox()
        self.combo_agregado.addItem("Basalto (Alfa=1.2)", 1.2)
        self.combo_agregado.addItem("Granito (Alfa=1.0)", 1.0)
        self.combo_agregado.addItem("Calcário (Alfa=0.9)", 0.9)
        self.combo_agregado.setCurrentIndex(1)

        layout.addRow("Carga Perm. Total (kN/m²):", self.input_g)
        layout.addRow("Carga Acid. (kN/m²):", self.input_q)
        layout.addRow("fck do Concreto:", self.input_fck)
        layout.addRow("Tipo de Agregado:", self.combo_agregado)
        self.tab_mat.setLayout(layout)
        self.calc_tabs.addTab(self.tab_mat, "Cargas/Mat.")

    def setup_tab_detalhes(self):
        self.tab_det = QWidget()
        self.layout_det = QFormLayout()
        self.input_h_macica = QLineEdit("12")
        self.combo_enchimento = QComboBox()
        for e in catalog_service.get_todos_enchimentos():
            self.combo_enchimento.addItem(f"{e['modelo']}", e['modelo'])
        self.input_h_capa = QLineEdit("4")
        self.input_b_sapata = QLineEdit("12.5")
        
        self.lbl_h_macica = QLabel("Espessura (cm):")
        self.lbl_enchimento = QLabel("Enchimento:")
        self.lbl_capa = QLabel("Capa (cm):")
        self.lbl_sapata = QLabel("Nervura (cm):")
        
        self.layout_det.addRow(self.lbl_h_macica, self.input_h_macica)
        self.layout_det.addRow(self.lbl_enchimento, self.combo_enchimento)
        self.layout_det.addRow(self.lbl_capa, self.input_h_capa)
        self.layout_det.addRow(self.lbl_sapata, self.input_b_sapata)
        self.tab_det.setLayout(self.layout_det)
        self.calc_tabs.addTab(self.tab_det, "Detalhamento")

    def toggle_inputs_por_tipo(self):
        is_macica = self.combo_tipo.currentText() == "Laje Maciça"
        self.lbl_h_macica.setVisible(is_macica); self.input_h_macica.setVisible(is_macica)
        self.lbl_enchimento.setVisible(not is_macica); self.combo_enchimento.setVisible(not is_macica)
        self.lbl_capa.setVisible(not is_macica); self.input_h_capa.setVisible(not is_macica)
        self.lbl_sapata.setVisible(not is_macica); self.input_b_sapata.setVisible(not is_macica)

    def get_user_data(self):
        """Coleta dados da GUI e instancia os Objetos de Domínio."""
        try:
            fck = float(self.input_fck.currentText())
            alfa_e = self.combo_agregado.currentData()
            eci = alfa_e * 5600 * math.sqrt(fck)
            ecs = 0.85 * eci 
            
            mat = Materiais(fck=fck, fyk=500, Ecs=ecs/1000.0) 
            
            cargas = Carregamento(
                g_revestimento=float(self.input_g.text()), 
                q_acidental=float(self.input_q.text())
            )
            
            bordas = {
                'esquerda': CondicaoContorno.ENGASTADO if self.chk_esq.isChecked() else CondicaoContorno.APOIADO,
                'direita': CondicaoContorno.ENGASTADO if self.chk_dir.isChecked() else CondicaoContorno.APOIADO,
                'topo': CondicaoContorno.ENGASTADO if self.chk_top.isChecked() else CondicaoContorno.APOIADO,
                'fundo': CondicaoContorno.ENGASTADO if self.chk_bot.isChecked() else CondicaoContorno.APOIADO,
            }
            lx, ly = float(self.input_lx.text()), float(self.input_ly.text())
            
            if self.combo_tipo.currentText() == "Laje Maciça":
                h = float(self.input_h_macica.text()) / 100.0
                return LajeMacica(h=h, lx=lx, ly=ly, materiais=mat, caa=ClasseAgressividade.II, bordas=bordas, carregamento=cargas)
            else:
                mod = self.combo_enchimento.currentData()
                ench = catalog_service.get_modelo_enchimento(mod)
                return LajeTrelicada(lx=lx, ly=ly, materiais=mat, caa=ClasseAgressividade.II, bordas=bordas, carregamento=cargas,
                                     h_capa=float(self.input_h_capa.text())/100.0, largura_sapata=float(self.input_b_sapata.text())/100.0,
                                     dados_enchimento=ench)
        except Exception as e:
            QMessageBox.warning(self, "Erro", f"Verifique os dados de entrada: {e}")
            return None

    def run_calculation(self):
        laje = self.get_user_data()
        if not laje: return
        
        self.current_result = SlabController(laje, AnalyticEngine()).run_analysis()
        self.text_report.setText(ReportFormatter.format_as_text(self.current_result))
        
        self.btn_export_json.setEnabled(True)
        self.btn_export_memorial.setEnabled(True)

    def run_optimization(self):
        laje = self.get_user_data()
        if not laje: return
        
        self.text_report.setText("Calculando altura ótima...")
        QApplication.processEvents()
        
        h_opt = SlabController(laje, AnalyticEngine()).optimize_thickness()
        if h_opt:
            self.input_h_macica.setText(f"{h_opt*100:.1f}")
            self.run_calculation()
        else:
            self.text_report.setText("Não foi possível otimizar nos limites atuais.")

    def export_data_json(self):
        if not self.current_result: return
        path, _ = QFileDialog.getSaveFileName(self, "Salvar JSON (Integração)", f"laje_detalhe.json", "JSON (*.json)")
        if path: 
            ReportFormatter.save_json(self.current_result, path)
            QMessageBox.information(self, "Sucesso", "Arquivo JSON gerado com sucesso.")

    def export_memorial_md(self):
        if not self.current_result: return
        path, _ = QFileDialog.getSaveFileName(self, "Salvar Memorial", "memorial_calculo.md", "Markdown (*.md)")
        if path:
            conteudo = MemorialService.gerar_markdown([self.current_result])
            if MemorialService.salvar_arquivo(conteudo, path):
                QMessageBox.information(self, "Sucesso", f"Memorial salvo em:\n{path}")