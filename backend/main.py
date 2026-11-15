from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse, parse_qs
from datetime import datetime
import json, os, sqlite3
from database import inicializar, registrar_log, buscar_logs, listar_lancamentos, salvar_lancamento, remover_lancamento
from funcionarios import buscar_funcionario
from relatorio import gerar_excel, MESES
from salarios import resultados, exportar_salarios

ROOT=Path(__file__).resolve().parent.parent
os.chdir(ROOT)

class Servidor(SimpleHTTPRequestHandler):
    def json(self, dados, status=200):
        body=json.dumps(dados,ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type','application/json; charset=utf-8')
        self.send_header('Content-Length',str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def body_json(self):
        size=int(self.headers.get('Content-Length','0'))
        if size > 10000: raise ValueError('Dados enviados muito grandes')
        return json.loads(self.rfile.read(size) or b'{}')

    def do_GET(self):
        rota=urlparse(self.path)
        if rota.path=='/api/logs': return self.json(buscar_logs())
        if rota.path=='/api/lancamentos': return self.json(listar_lancamentos())
        if rota.path=='/api/salarios':
            periodo=parse_qs(rota.query).get('periodo',['Outubro de 2026'])[0]
            if periodo not in [f'{m} de 2026' for m in MESES]: return self.json({'erro':'Período inválido'},400)
            try: return self.json(resultados(periodo))
            except ValueError as e: return self.json({'erro':str(e)},400)
        if rota.path=='/api/funcionario':
            id_=parse_qs(rota.query).get('id',[''])[0].strip()
            func=buscar_funcionario(id_)
            if not func:
                registrar_log('Consulta de funcionário','DIVERGENCIA','ID não encontrado: '+id_,id_)
                return self.json({'erro':'Funcionário não encontrado'},404)
            return self.json(func)
        return super().do_GET()

    def do_POST(self):
        rota=urlparse(self.path).path
        if rota=='/api/exportar-salarios':
            try:
                dados=self.body_json(); periodo=dados.get('periodo','Outubro de 2026')
                if periodo not in [f'{m} de 2026' for m in MESES]: raise ValueError('Período inválido')
                conteudo=exportar_salarios(periodo)
                self.send_response(200)
                self.send_header('Content-Type','application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                self.send_header('Content-Disposition','attachment; filename=folha_salarial_simulada.xlsx')
                self.send_header('Content-Length',str(len(conteudo)))
                self.end_headers(); self.wfile.write(conteudo)
                registrar_log('Exportação de folha salarial','SUCESSO',f'Planilha simulada gerada: {periodo}; verificar status dos impostos')
            except ValueError as e:
                registrar_log('Exportação de folha salarial','DIVERGENCIA',str(e))
                self.json({'erro':str(e)},400)
            except Exception as e:
                registrar_log('Exportação de folha salarial','ERRO',str(e))
                self.json({'erro':'Erro interno ao exportar folha'},500)
            return
        if rota=='/api/exportar':
            try:
                dados=self.body_json()
                mes=dados.get('mes','Outubro de 2026')
                if mes not in [f'{m} de 2026' for m in MESES]: raise ValueError('Período inválido')
                arquivo=gerar_excel(mes)
                conteudo=arquivo.read_bytes()
                self.send_response(200)
                self.send_header('Content-Type','application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                self.send_header('Content-Disposition',f'attachment; filename="{arquivo.name}"')
                self.send_header('Content-Length',str(len(conteudo)))
                self.end_headers()
                self.wfile.write(conteudo)
                registrar_log('Exportação de ponto','SUCESSO',f'Relatório gerado: {mes}')
            except Exception as e:
                registrar_log('Exportação de ponto','ERRO',str(e))
                return self.json({'erro':str(e)},400)
            return
        if rota=='/api/lancamentos':
            dados={}
            try:
                dados=self.body_json()
                id_=str(dados.get('funcionario_id','')).strip()
                funcionario=buscar_funcionario(id_)
                if not funcionario: raise ValueError('ID do funcionário não existe no cadastro')
                nome=str(dados.get('nome','')).strip()
                if nome.casefold()!=funcionario['nome'].casefold():
                    raise ValueError('Nome divergente do cadastro do funcionário')
                periodo=str(dados.get('periodo',''))
                if periodo not in [f'{m} de 2026' for m in MESES]: raise ValueError('Período inválido')
                valores={}
                for campo in ('horas_trabalhadas','he50','he100','faltas','atestados'):
                    valor=float(dados.get(campo,''))
                    if not (0 <= valor <= 744): raise ValueError(f'Valor inválido: {campo}')
                    if campo in ('faltas','atestados') and not valor.is_integer():
                        raise ValueError(f'{campo} deve ser inteiro')
                    valores[campo]=int(valor) if campo in ('faltas','atestados') else valor
                salvar_lancamento(dict(funcionario_id=id_,nome=funcionario['nome'],periodo=periodo,**valores))
                registrar_log('Lançamento de folha','SUCESSO',f'Lançamento registrado: {periodo}',id_)
                return self.json({'mensagem':'Lançamento registrado com sucesso'},201)
            except (ValueError,TypeError,sqlite3.IntegrityError) as e:
                mensagem=('Já existe lançamento para este funcionário e período' if isinstance(e,sqlite3.IntegrityError) else str(e))
                registrar_log('Lançamento de folha','DIVERGENCIA',mensagem,str(dados.get('funcionario_id','')))
                return self.json({'erro':mensagem},400)
            except Exception as e:
                registrar_log('Lançamento de folha','ERRO',str(e))
                return self.json({'erro':'Erro interno ao registrar lançamento'},500)
        if rota=='/api/remover-lancamento':
            try:
                id_=int(self.body_json()['id'])
                if not remover_lancamento(id_): return self.json({'erro':'Lançamento não encontrado'},404)
                registrar_log('Remoção de lançamento','SUCESSO',f'Lançamento {id_} removido')
                return self.json({'mensagem':'Removido'})
            except Exception as e:
                return self.json({'erro':str(e)},400)
        return self.json({'erro':'Rota não encontrada'},404)

if __name__=='__main__':
    inicializar()
    print('Servidor disponível em http://localhost:8000')
    HTTPServer(('127.0.0.1',8000),Servidor).serve_forever()
