"""Cálculo DEMONSTRATIVO: não é folha legal/líquida definitiva."""
from decimal import Decimal, ROUND_HALF_UP
from database import listar_lancamentos
from funcionarios import buscar_funcionario
from falazuki import consultar, FalhaTributaria
from relatorio import MESES

def dinheiro(v):
    return Decimal(str(v)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

def calcular_lancamento(lancamento):
    funcionario = buscar_funcionario(lancamento['funcionario_id'])
    if not funcionario or funcionario.get('salario_base') is None:
        raise ValueError('Funcionário sem cadastro salarial: ' + lancamento['funcionario_id'])
    base = dinheiro(funcionario['salario_base'])
    divisor = Decimal(str(funcionario.get('divisor_mensal',220)))
    if divisor <= 0: raise ValueError('Divisor mensal inválido')
    hora = base / divisor
    extra50 = dinheiro(hora * Decimal(str(lancamento['he50'])) * Decimal('1.5'))
    extra100 = dinheiro(hora * Decimal(str(lancamento['he100'])) * Decimal('2'))
    # Regra apenas demonstrativa: falta não justificada = 1/30 do salário-base.
    desconto_faltas = dinheiro(base / Decimal('30') * Decimal(str(lancamento['faltas'])))
    bruto = dinheiro(base + extra50 + extra100 - desconto_faltas)
    if bruto <= 0:
        raise ValueError('Remuneração bruta não positiva; conferir lançamentos')
    periodo = lancamento['periodo']
    mes = MESES.index(periodo.split(' de ')[0]) + 1
    ano = int(periodo.rsplit(' ', 1)[-1])
    data = f'{ano}-{mes:02d}-01'
    dependentes = int(funcionario.get('dependentes',0))
    vt = dinheiro(funcionario.get('vale_transporte_desconto',0))
    outros = dinheiro(funcionario.get('outros_descontos',0))
    registro = dict(id=lancamento['funcionario_id'], nome=funcionario['nome'], periodo=periodo,
        salario_base=float(base), horas_trabalhadas=lancamento['horas_trabalhadas'],
        he50=lancamento['he50'],he100=lancamento['he100'],faltas=lancamento['faltas'],
        atestados=lancamento['atestados'],valor_he50=float(extra50),valor_he100=float(extra100),
        desconto_faltas=float(desconto_faltas),salario_calculado=None,bruto_ajustado=float(bruto),
        inss=None,irrf=None,vale_transporte=float(vt),outros_descontos=float(outros),
        dependentes=dependentes,status='PENDENTE — API')
    try:
        impostos=consultar(bruto,dependentes,data)
        final=dinheiro(impostos['liquido_api']-vt-outros)
        registro.update(inss=float(impostos['inss']),irrf=float(impostos['irrf']),
            salario_calculado=float(final),status='SUCESSO')
    except FalhaTributaria as erro:
        registro['status']='PENDENTE — '+str(erro)
    return registro

def resultados(periodo):
    return [calcular_lancamento(l) for l in listar_lancamentos() if l['periodo']==periodo]

def exportar_salarios(periodo):
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill
    from openpyxl.utils import get_column_letter
    from io import BytesIO
    dados=resultados(periodo)
    if not dados: raise ValueError('Não há lançamentos para o período selecionado')
    wb=Workbook(); ws=wb.active; ws.title='Folha salarial'
    campos=[('id','ID'),('nome','Funcionário'),('periodo','Período'),('salario_base','Salário-base'),
      ('he50','HE 50% (h)'),('he100','HE 100% (h)'),('valor_he50','Valor HE 50%'),
      ('valor_he100','Valor HE 100%'),('faltas','Faltas'),('atestados','Atestados'),
      ('desconto_faltas','Desconto faltas'),('bruto_ajustado','Bruto ajustado'),
      ('dependentes','Dependentes'),('inss','INSS'),('irrf','IRRF'),
      ('vale_transporte','Vale-transporte'),('outros_descontos','Outros descontos'),
      ('salario_calculado','Líquido estimado'),('status','Status')]
    ws.append([titulo for _,titulo in campos])
    for d in dados: ws.append([d.get(chave) for chave,_ in campos])
    for c in ws[1]:
        c.font=Font(bold=True,color='FFFFFF');c.fill=PatternFill('solid',fgColor='1F4E78')
    moeda={'salario_base','valor_he50','valor_he100','desconto_faltas','bruto_ajustado',
           'inss','irrf','vale_transporte','outros_descontos','salario_calculado'}
    for i,(chave,_) in enumerate(campos,1):
        if chave in moeda:
            for col in ws.iter_cols(min_col=i,max_col=i,min_row=2):
                for c in col:c.number_format='"R$" #,##0.00'
    ws.freeze_panes='C2';ws.auto_filter.ref=ws.dimensions
    for col in ws.columns:
        ws.column_dimensions[get_column_letter(col[0].column)].width=min(48,max(len(str(c.value or '')) for c in col)+3)
    obs=wb.create_sheet('Avisos')
    for linha in ['SIMULAÇÃO — NÃO UTILIZAR PARA PAGAMENTO',
      'INSS e IRRF dependem de retorno válido da API FalaZuki.',
      'Sem resposta tributária válida, o salário líquido fica em branco.',
      'Faltas e horas extras seguem regras ilustrativas; DSR, convenção coletiva e demais verbas exigem validação.',
      'Vale-transporte e outros descontos devem ser cadastrados por funcionário.',
      'API: https://www.falazuki.com/produtos/api']:
        obs.append([linha])
    obs.column_dimensions['A'].width=110
    buffer=BytesIO();wb.save(buffer);return buffer.getvalue()
