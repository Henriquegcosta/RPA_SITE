"""Relatório de ponto DEMONSTRATIVO, com horários fictícios determinísticos."""
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter
from datetime import datetime, date, timedelta
from pathlib import Path
from hashlib import sha256
from funcionarios import FUNCIONARIOS, buscar_funcionario

# Cenários negativos intencionais para testar o RPA sem interromper a execução.
# Desative para exportar apenas funcionários cadastrados.
INCLUIR_CENARIOS_ERRO = True
IDS_INEXISTENTES_TESTE = ('9001', '9002')

MESES = ['Janeiro','Fevereiro','Março','Abril','Maio','Junho','Julho','Agosto','Setembro','Outubro','Novembro','Dezembro']


def horas(n):
    return f'{n // 60:02d}:{n % 60:02d}'


def minutos(h):
    hh, mm = map(int, h.split(':'))
    return hh * 60 + mm


def buscar_registros(mes):
    """Gera um dia de ponto fictício por funcionário, no mês escolhido."""
    nome_mes, ano_texto = mes.rsplit(' de ', 1)
    if nome_mes not in MESES:
        raise ValueError('Mês inválido')
    ano = int(ano_texto)
    numero = MESES.index(nome_mes) + 1
    registros = []
    for id_ in sorted(FUNCIONARIOS, key=lambda x: (not str(x).isdigit(), str(x))):
        identificador = str(id_)
        # Hash estável: mesma pessoa e mês produzem os mesmos horários.
        digest = sha256(f'{ano}-{numero:02d}-{identificador}'.encode()).digest()
        dia = 1 + digest[0] % 25
        data = date(ano, numero, dia).strftime('%d/%m/%Y')
        inicio = 6 * 60 + (digest[1] % 3) * 60 + digest[2] % 12
        pausa = inicio + 4 * 60 + digest[3] % 25
        volta = pausa + 60
        saida = volta + 4 * 60 + digest[4] % 55
        registros.append((identificador, data, horas(inicio), horas(pausa), horas(volta), horas(saida)))
    if INCLUIR_CENARIOS_ERRO:
        # IDs que NÃO existem no cadastro: o RPA deve registrar falha na busca
        # e continuar com os demais, sem abortar o processamento.
        for identificador in IDS_INEXISTENTES_TESTE:
            if buscar_funcionario(identificador) is not None:
                continue  
            digest = sha256(f'{ano}-{numero:02d}-{identificador}'.encode()).digest()
            dia = 1 + digest[0] % 25
            data = date(ano, numero, dia).strftime('%d/%m/%Y')
            inicio = 7 * 60
            pausa = inicio + 4 * 60
            volta = pausa + 60
            saida = volta + 4 * 60 + 15
            registros.append((identificador, data, horas(inicio), horas(pausa), horas(volta), horas(saida)))
    return registros


def gerar_excel(mes):
    registros = buscar_registros(mes)
    wb = Workbook()
    ws = wb.active
    ws.title = 'Ponto'
    ws.append(['ID','Funcionário','Data','Entrada','Saída almoço','Volta almoço','Saída',
               'Horas trabalhadas','Horas extras','Fez hora extra?','Faltas','Observação'])
    for id_, data, entrada, pausa, volta, saida in registros:
        funcionario = buscar_funcionario(id_)
        trabalhadas = (minutos(pausa)-minutos(entrada)) + (minutos(saida)-minutos(volta))
        extras = max(0, trabalhadas-480)  # Regra fictícia: 8h/dia
        ws.append([id_, funcionario['nome'] if funcionario else 'Não cadastrado', data,
                   entrada, pausa, volta, saida, horas(trabalhadas), horas(extras),
                   'Sim' if extras else 'Não', 0, ('TESTE DE ERRO — ID não cadastrado' if funcionario is None else 'SIMULAÇÃO — ponto fictício; faltas definidas como zero')])
    for cel in ws[1]:
        cel.font = Font(bold=True, color='FFFFFF')
        cel.fill = PatternFill('solid', fgColor='1F4E78')
    ws.freeze_panes = 'A2'
    ws.auto_filter.ref = ws.dimensions
    for col in ws.columns:
        ws.column_dimensions[get_column_letter(col[0].column)].width = min(65, max(len(str(c.value or '')) for c in col)+3)
    aviso = wb.create_sheet('Avisos')
    aviso.append(['SIMULAÇÃO: horários, horas extras e faltas fictícios. Não usar em folha oficial.'])
    aviso.append(['Cada funcionário recebe um único registro demonstrativo por mês.'])
    aviso.append(['IDs 9001 e 9002 são testes de erro de cadastro, caso não existam em funcionarios.py.'])
    aviso.append(['Duplicidade é testada executando novamente o RPA com o mesmo mês; não inserir IDs duplicados no Excel.'])
    aviso.column_dimensions['A'].width = 95
    arquivo = Path(__file__).resolve().parent / ('relatorio_ponto_'+datetime.now().strftime('%Y%m%d_%H%M%S_%f')+'.xlsx')
    wb.save(arquivo)
    return arquivo
