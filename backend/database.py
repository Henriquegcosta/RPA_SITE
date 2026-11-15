import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).resolve().parent / 'logs.db'

def conectar():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn

def inicializar():
    with conectar() as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS logs (
          id INTEGER PRIMARY KEY AUTOINCREMENT, funcionario TEXT,
          operacao TEXT NOT NULL, status TEXT NOT NULL,
          mensagem TEXT, data_hora TEXT NOT NULL)''')
        conn.execute('''CREATE TABLE IF NOT EXISTS lancamentos (
          id INTEGER PRIMARY KEY AUTOINCREMENT, funcionario_id TEXT NOT NULL,
          nome TEXT NOT NULL, periodo TEXT NOT NULL,
          horas_trabalhadas REAL NOT NULL, he50 REAL NOT NULL, he100 REAL NOT NULL,
          faltas INTEGER NOT NULL, atestados INTEGER NOT NULL,
          UNIQUE(funcionario_id, periodo))''')

def registrar_log(operacao, status, mensagem='', funcionario=None):
    with conectar() as conn:
        conn.execute('INSERT INTO logs (funcionario,operacao,status,mensagem,data_hora) VALUES (?,?,?,?,?)',
          (funcionario,operacao,status,mensagem,datetime.now().strftime('%d/%m/%Y %H:%M:%S')))

def buscar_logs():
    with conectar() as conn:
        return [dict(r) for r in conn.execute('SELECT * FROM logs ORDER BY id DESC')]

def listar_lancamentos():
    with conectar() as conn:
        return [dict(r) for r in conn.execute('SELECT * FROM lancamentos ORDER BY id DESC')]

def salvar_lancamento(d):
    with conectar() as conn:
        conn.execute('''INSERT INTO lancamentos
          (funcionario_id,nome,periodo,horas_trabalhadas,he50,he100,faltas,atestados)
          VALUES (:funcionario_id,:nome,:periodo,:horas_trabalhadas,:he50,:he100,:faltas,:atestados)''',d)

def remover_lancamento(id_lancamento):
    with conectar() as conn:
        cursor=conn.execute('DELETE FROM lancamentos WHERE id=?',(id_lancamento,))
        return cursor.rowcount > 0
