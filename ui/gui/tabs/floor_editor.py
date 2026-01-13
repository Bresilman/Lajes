from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
                             QTableWidgetItem, QPushButton, QHeaderView, QSplitter,
                             QMessageBox, QLabel, QTabWidget, QFileDialog, QMenu)
from PyQt6.QtCore import Qt, pyqtSignal
from ui.gui.widgets.floor_canvas import FloorCanvas
from app.models.floor_system import GerenciadorPavimento, LajePosicionada
from app.models.value_objects import Materiais, Carregamento, ClasseAgressividade, CargaLinear
from app.models.solid import LajeMacica
from app.services.catalog_service import catalog_service

class FloorEditorTab(QWidget):
    laje_selecionada_signal = pyqtSignal(object)

    def __init__(self):
        super().__init__()
        self.manager = GerenciadorPavimento()
        
        # Dicionário para guardar vínculos manuais: { 'L1': {'direita': 'livre', ...}, ... }
        self.manual_overrides = {} 
        
        self.setup_ui()

    def setup_ui(self):
        main_layout = QHBoxLayout(self)
        
        # --- PAINEL ESQUERDO ---
        left_panel_container = QWidget()
        vbox_left = QVBoxLayout(left_panel_container)
        
        self.tabs_input = QTabWidget()
        
        # 1. ABA LAJES
        tab_lajes = QWidget()
        vbox_l = QVBoxLayout(tab_lajes)
        self.table_lajes = QTableWidget()
        
        cols_l = ["ID", "Lx", "Ly", "h (cm)", "Perm", "Acid", "Pos X", "Pos Y", "V.Esq", "V.Dir", "V.Sup", "V.Inf"]
        self.table_lajes.setColumnCount(len(cols_l))
        self.table_lajes.setHorizontalHeaderLabels(cols_l)
        
        # Menu de contexto
        self.table_lajes.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table_lajes.customContextMenuRequested.connect(self.abrir_menu_contexto)

        vbox_l.addWidget(self.table_lajes)
        
        btn_add_l = QPushButton("Add Laje"); btn_add_l.clicked.connect(self.add_laje_row)
        btn_rem_l = QPushButton("Remover"); btn_rem_l.clicked.connect(lambda: self.remove_row(self.table_lajes))
        hl = QHBoxLayout(); hl.addWidget(btn_add_l); hl.addWidget(btn_rem_l)
        vbox_l.addLayout(hl)
        self.tabs_input.addTab(tab_lajes, "Lajes (Dados)")

        # 2. ABA PAREDES
        tab_paredes = QWidget()
        vbox_p = QVBoxLayout(tab_paredes)
        self.table_paredes = QTableWidget()
        cols_p = ["ID", "X1", "Y1", "X2", "Y2", "Carga (kN/m)"]
        self.table_paredes.setColumnCount(len(cols_p))
        self.table_paredes.setHorizontalHeaderLabels(cols_p)
        vbox_p.addWidget(self.table_paredes)
        
        btn_add_p = QPushButton("Add Parede"); btn_add_p.clicked.connect(self.add_parede_row)
        btn_rem_p = QPushButton("Remover"); btn_rem_p.clicked.connect(lambda: self.remove_row(self.table_paredes))
        hp = QHBoxLayout(); hp.addWidget(btn_add_p); hp.addWidget(btn_rem_p)
        vbox_p.addLayout(hp)
        self.tabs_input.addTab(tab_paredes, "Paredes")

        vbox_left.addWidget(self.tabs_input)

        # Ações
        group_actions = QWidget()
        vbox_act = QVBoxLayout(group_actions)
        
        lbl_hint = QLabel("Dica: Clique com botão direito na tabela para definir bordas livres (balanços).")
        lbl_hint.setStyleSheet("color: gray; font-style: italic; font-size: 10px;")
        vbox_act.addWidget(lbl_hint)

        btn_upd = QPushButton("1. Atualizar Geometria")
        btn_upd.clicked.connect(self.process_geometry)
        
        self.btn_send_to_calc = QPushButton("2. Detalhar Laje Selecionada →")
        self.btn_send_to_calc.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold;")
        self.btn_send_to_calc.clicked.connect(self.enviar_para_calculadora)
        
        btn_export = QPushButton("3. Exportar JSON para Vigas")
        btn_export.clicked.connect(self.export_floor_data)
        
        vbox_act.addWidget(btn_upd)
        vbox_act.addWidget(self.btn_send_to_calc)
        vbox_act.addWidget(btn_export)
        
        vbox_left.addWidget(group_actions)

        # --- PAINEL DIREITO ---
        self.canvas = FloorCanvas()
        split = QSplitter(Qt.Orientation.Horizontal)
        split.addWidget(left_panel_container)
        split.addWidget(self.canvas)
        main_layout.addWidget(split)
        
        # INICIALIZAÇÃO DE DADOS DE EXEMPLO (CORREÇÃO: Chamada restaurada)
        self.add_example_data()

    def add_laje_row(self):
        r = self.table_lajes.rowCount(); self.table_lajes.insertRow(r)
        defaults = [f"L{r+1}", "4.0", "5.0", "12.0", "1.0", "2.0", "0.0", "0.0", "V1", "V2", "V3", "V4"]
        for i, val in enumerate(defaults): self.table_lajes.setItem(r, i, QTableWidgetItem(val))

    def add_parede_row(self):
        r = self.table_paredes.rowCount(); self.table_paredes.insertRow(r)
        data = [f"P{r+1}", "2.0", "0.0", "2.0", "5.0", "3.0"]
        for i, v in enumerate(data): self.table_paredes.setItem(r, i, QTableWidgetItem(v))

    def remove_row(self, table):
        c = table.currentRow()
        if c >= 0: table.removeRow(c); self.process_geometry()

    # MÉTODO RESTAURADO: Adiciona dados iniciais para não abrir vazio
    def add_example_data(self):
        self.add_laje_row()   # Adiciona L1 padrão
        self.add_parede_row() # Adiciona P1 padrão
        self.process_geometry() # Renderiza

    def abrir_menu_contexto(self, position):
        menu = QMenu()
        for borda in ['esquerda', 'direita', 'topo', 'fundo']:
            submenu = menu.addMenu(f"Borda {borda.capitalize()}")
            submenu.addAction("LIVRE (Balanço)", lambda ch, b=borda: self.set_vinculo(b, 'livre'))
            submenu.addAction("Forçar ENGASTE", lambda ch, b=borda: self.set_vinculo(b, 'engastado'))
            submenu.addAction("Automático", lambda ch, b=borda: self.set_vinculo(b, ''))
        menu.exec(self.table_lajes.viewport().mapToGlobal(position))

    def set_vinculo(self, borda, tipo):
        row = self.table_lajes.currentRow()
        if row < 0: return
        laje_id = self.table_lajes.item(row, 0).text()
        
        if laje_id not in self.manual_overrides:
            self.manual_overrides[laje_id] = {}
        self.manual_overrides[laje_id][borda] = tipo
        
        self.process_geometry() 
        tipo_str = tipo.upper() if tipo else "AUTOMÁTICO"
        QMessageBox.information(self, "Vínculo Definido", f"Laje {laje_id} - Borda {borda}: {tipo_str}")

    def process_geometry(self):
        self.manager.limpar()
        try:
            for r in range(self.table_lajes.rowCount()):
                nome = self.table_lajes.item(r,0).text()
                lx = float(self.table_lajes.item(r,1).text())
                ly = float(self.table_lajes.item(r,2).text())
                h_cm = float(self.table_lajes.item(r,3).text())
                g_perm = float(self.table_lajes.item(r,4).text())
                q_acid = float(self.table_lajes.item(r,5).text())
                x = float(self.table_lajes.item(r,6).text())
                y = float(self.table_lajes.item(r,7).text())
                vigas = {
                    'esquerda': self.table_lajes.item(r,8).text(),
                    'direita': self.table_lajes.item(r,9).text(),
                    'topo': self.table_lajes.item(r,10).text(),
                    'fundo': self.table_lajes.item(r,11).text()
                }
                
                mat = Materiais(fck=25, fyk=500, Ecs=25.0)
                cargas = Carregamento(g_revestimento=g_perm, q_acidental=q_acid)
                
                laje = LajeMacica(h=h_cm/100.0, lx=lx, ly=ly, materiais=mat, caa=ClasseAgressividade.II, bordas={}, carregamento=cargas)
                
                overrides = self.manual_overrides.get(nome, {})
                laje_pos = LajePosicionada(nome, laje, x, y, vigas=vigas, vinculos_manuais=overrides)
                self.manager.adicionar_laje(laje_pos)

            for r in range(self.table_paredes.rowCount()):
                n = self.table_paredes.item(r,0).text()
                x1, y1 = float(self.table_paredes.item(r,1).text()), float(self.table_paredes.item(r,2).text())
                x2, y2 = float(self.table_paredes.item(r,3).text()), float(self.table_paredes.item(r,4).text())
                c = float(self.table_paredes.item(r,5).text())
                self.manager.adicionar_parede(CargaLinear(n, x1, y1, x2, y2, c))

            self.manager.distribuir_cargas_paredes()
            self.canvas.update_system(self.manager.lajes, self.manager.paredes)

        except Exception as e: 
            print(f"Erro: {e}")
            QMessageBox.warning(self, "Erro nos Dados", f"Verifique a tabela: {e}")

    def enviar_para_calculadora(self):
        row = self.table_lajes.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Aviso", "Selecione uma laje.")
            return
        self.process_geometry()
        
        # Verificação de segurança de índice
        if row < len(self.manager.lajes):
            laje_pos = self.manager.lajes[row]
            self.laje_selecionada_signal.emit((laje_pos, row))
        else:
            QMessageBox.warning(self, "Erro", "Erro de sincronia. Tente 'Atualizar Geometria' primeiro.")

    def export_floor_data(self):
        self.process_geometry()
        path, _ = QFileDialog.getSaveFileName(self, "Exportar", "vigas.json", "JSON (*.json)")
        if path:
            self.manager.calcular_e_exportar_vigas(path)
            QMessageBox.information(self, "Sucesso", "Exportado.")

    def atualizar_linha_tabela(self, row_idx, laje_atualizada):
        """Atualiza a tabela visual após sincronização da calculadora."""
        if row_idx < 0 or row_idx >= self.table_lajes.rowCount(): return
        self.table_lajes.setItem(row_idx, 3, QTableWidgetItem(f"{laje_atualizada.h * 100:.1f}"))
        self.table_lajes.selectRow(row_idx)