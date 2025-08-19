# migrate_logs.py
import os
from models import db, Processo
from app import app
from datetime import datetime

with app.app_context():
    for modulo in ['cadastro', 'atributos', 'prazos']:
        log_file = f'logs/processos/{modulo}.log'
        if os.path.exists(log_file):
            with open(log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        parts = line.split('|')
                        data_str = parts[0].strip()
                        qtd = int(parts[1].split(':')[1].strip())
                        tempo = float(parts[2].split(':')[1].strip()[:-1])
                        status = parts[3].split(':')[1].strip()
                        usuario = parts[4].split(':')[1].strip()
                        processo = Processo(
                            modulo=modulo,
                            data=datetime.strptime(data_str, '%Y-%m-%d %H:%M:%S'),
                            status=status,
                            qtd_itens=qtd,
                            tempo_execucao=tempo,
                            usuario=usuario
                        )
                        db.session.add(processo)
                    except Exception as e:
                        print(f"Erro ao importar linha: {line} - {str(e)}")
            db.session.commit()