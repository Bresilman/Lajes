import sys
import os
import argparse
import traceback

# --- CONFIGURAÇÃO DE PATH ---
# Garante que a raiz do projeto esteja visível para imports
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

def start_gui():
    """Inicializa a aplicação gráfica PyQt6."""
    
    # 1. Tenta carregar PyQt6 (Dependência Externa)
    try:
        from PyQt6.QtWidgets import QApplication
    except ImportError as e:
        print("\n" + "="*60)
        print("ERRO CRÍTICO: PyQt6 NÃO ENCONTRADO")
        print("="*60)
        print(f"O Python não encontrou a biblioteca gráfica.")
        print(f"Mensagem técnica: {e}")
        print("-" * 60)
        print("SOLUÇÕES PROVÁVEIS (LINUX/POP_OS):")
        print("1. Instale o pacote Python: pip install PyQt6")
        print("2. Instale libs do sistema: sudo apt install libxcb-cursor0 libegl1")
        print("="*60 + "\n")
        sys.exit(1)

    # 2. Tenta carregar módulos locais (Dependência Interna)
    try:
        from ui.gui.main_window import MainWindow
    except ImportError as e:
        print("\n" + "="*60)
        print("ERRO DE ESTRUTURA DO PROJETO")
        print("="*60)
        print(f"O PyQt6 carregou corretamente, mas o Python não achou seus arquivos.")
        print(f"Mensagem técnica: {e}")
        print("-" * 60)
        print(f"Diretório Base (onde está o main.py): {BASE_DIR}")
        print(f"Conteúdo encontrado na pasta: {os.listdir(BASE_DIR)}")
        print("-" * 60)
        print("VERIFICAÇÕES:")
        print("1. Existe uma pasta chamada 'ui' (minúsculo)?")
        print("2. Dentro de 'ui', existe uma pasta 'gui'?")
        print("3. Dentro de 'gui', existe 'main_window.py'?")
        print("NOTA: O Linux diferencia maiúsculas de minúsculas (ui != UI).")
        print("="*60 + "\n")
        sys.exit(1)

    # 3. Executa a GUI
    try:
        app = QApplication(sys.argv)
        app.setStyle("Fusion") 
        window = MainWindow()
        window.show()
        sys.exit(app.exec())
    except Exception as e:
        print(f"Erro durante a execução da GUI: {e}")
        traceback.print_exc()
        sys.exit(1)

def start_cli():
    try:
        from ui.cli import run_cli_interface
        run_cli_interface()
    except Exception as e:
        print(f"Erro no modo CLI: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PyLaje")
    parser.add_argument("--cli", action="store_true", help="Modo Texto")
    args = parser.parse_args()

    if args.cli:
        start_cli()
    else:
        start_gui()