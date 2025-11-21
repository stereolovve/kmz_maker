"""
Extensão dos services com geração de logs
"""
import os
from datetime import datetime


def save_processing_log(log_lines, log_path):
    """Salva arquivo de log do processamento"""
    try:
        with open(log_path, 'w', encoding='utf-8') as f:
            f.writelines(log_lines)
        return True
    except Exception as e:
        print(f"Erro ao salvar log: {e}")
        return False


def add_log_to_services():
    """
    Adiciona logs aos métodos de processamento
    Modifica process_excel_com_rotas e process_excel_simples
    """
    pass
