"""Fonte temporária de cadastro"""
FUNCIONARIOS = {
 '1042': {'id':'1042','salario_base':2400,'divisor_mensal':220,'dependentes':0,'vale_transporte_desconto':0,'outros_descontos':0,'nome':'Ana Souza'},
 '1043': {'id':'1043','salario_base':2250,'divisor_mensal':220,'dependentes':0,'vale_transporte_desconto':0,'outros_descontos':0,'nome':'Bruno Lima'},
 '1044': {'id':'1044','salario_base':2800,'divisor_mensal':220,'dependentes':1,'vale_transporte_desconto':0,'outros_descontos':0,'nome':'Carla Mendes'},
 '1045': {'id':'1045','salario_base':2500,'divisor_mensal':220,'dependentes':2,'vale_transporte_desconto':0,'outros_descontos':0,'nome':'Diego Alves'},
 '1046': {'id':'1046','salario_base':1500,'divisor_mensal':220,'dependentes':0,'vale_transporte_desconto':0,'outros_descontos':0,'nome':'Elaine Costa'},
 '1047': {'id':'1047','salario_base':1200,'divisor_mensal':220,'dependentes':0,'vale_transporte_desconto':0,'outros_descontos':0,'nome':'Fábio Rocha'},
 '1048': {'id':'1048','salario_base':3200,'divisor_mensal':220,'dependentes':3,'vale_transporte_desconto':72,'outros_descontos':0,'nome':'José Antonio'},
 '1048': {'id':'1048','salario_base':3200,'divisor_mensal':220,'dependentes':3,'vale_transporte_desconto':72,'outros_descontos':0,'nome':'Henrique Antonio'},
 '1049': {'id':'1049','salario_base':7200,'divisor_mensal':270,'dependentes':1,'vale_transporte_desconto':92,'outros_descontos':0,'nome':'Pedro Antonio'},
 '1050': {'id':'1050','salario_base':3200,'divisor_mensal':220,'dependentes':3,'vale_transporte_desconto':72,'outros_descontos':0,'nome':'José Antonio'},
}

def buscar_funcionario(identificador):
    return FUNCIONARIOS.get(str(identificador).strip())
