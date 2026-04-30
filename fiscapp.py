import streamlit as st
import requests
import json
import os
import time
import extra_streamlit_components as stx
import pandas as pd
import io
from dotenv import load_dotenv
from datetime import datetime, timedelta
from streamlit_qrcode_scanner import qrcode_scanner
from streamlit_js_eval import get_geolocation

# Configurações iniciais e Variáveis de Ambiente
load_dotenv()
URL_API = os.getenv("URL_API", "http://localhost:8000")
TITULO_APP = os.getenv("TITULO_APP", "App de Operações de Campo")
ICONE_APP = os.getenv("ICONE_APP", "📊")

st.set_page_config(page_title=TITULO_APP, page_icon=ICONE_APP)

# Mock de Configurações Genéricas (Pode virar um banco de dados ou API no futuro)
OPCOES_ATIVIDADE = ["Check-in", "Inspeção", "Manutenção", "Segurança", "Suporte"]
DADOS_ZONAS = {
    'ZONA_A': ['Setor 1', 'Setor 2'],
    'ZONA_B': ['Setor 2'],
    'ZONA_C': ['Setor 1', 'Setor 3'],
}
TODOS_SETORES = sorted(list(set(setor for sublista in DADOS_ZONAS.values() for setor in sublista)))

# Gerenciamento de Sessão e Cookies
NOME_COOKIE_SESSAO = "sessao_app_operacoes"
gerenciador_cookies = stx.CookieManager(key="gerenciador_cookies_app")

def atualizar_cookie_sessao(token, nome, id_usuario, etapa, dados_pendentes):
    payload = {
        "token": token,
        "nome": nome,
        "id_usuario": id_usuario,
        "etapa": etapa,
        "dados": dados_pendentes
    }
    expiracao = datetime.now() + timedelta(days=1)
    gerenciador_cookies.set(
        NOME_COOKIE_SESSAO, 
        json.dumps(payload), 
        expires_at=expiracao,
        key=f"sessao_{datetime.now().timestamp()}"
    )

def limpar_sessao():
    passado = datetime.now() - timedelta(days=2)
    gerenciador_cookies.set(NOME_COOKIE_SESSAO, "", expires_at=passado, key="logout")

# Funções de Integração com API
def obter_cabecalhos():
    token = st.session_state.get('token_jwt')
    cabecalhos = {'Content-Type': 'application/json'}
    if token:
        cabecalhos['Authorization'] = f'Bearer {token}'
    return cabecalhos

def autenticar_usuario(usuario, senha):
    try:
        resposta = requests.post(f"{URL_API}/login", json={"usuario": usuario, "senha": senha}, timeout=10)
        if resposta.status_code == 200:
            dados = resposta.json()
            return True, "Sucesso", dados
        return False, "Credenciais inválidas", None
    except Exception as e:
        return False, f"Erro de conexão: {e}", None

def enviar_registro(payload):
    try:
        resposta = requests.post(f"{URL_API}/registro", json=payload, headers=obter_cabecalhos(), timeout=5)
        return (True, "Sucesso") if resposta.status_code == 200 else (False, f"Erro da API: {resposta.status_code}")
    except Exception as e:
        return False, str(e)

# Helpers de Processamento de Dados
def exportar_para_excel(dados_json):
    if not dados_json: return None
    df = pd.DataFrame(dados_json)
    saida = io.BytesIO()
    with pd.ExcelWriter(saida, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Relatorio_Diario')
    return saida.getvalue()

# LÓGICA DE INTERFACE E ESTADO

# Inicialização do State
if 'logado' not in st.session_state: st.session_state['logado'] = False
if 'etapa_atual' not in st.session_state: st.session_state['etapa_atual'] = 'scan'

# Recuperação de Sessão via Cookie
if not st.session_state['logado']:
    cookie_bruto = gerenciador_cookies.get(NOME_COOKIE_SESSAO)
    if cookie_bruto:
        try:
            dados_sessao = json.loads(cookie_bruto) if isinstance(cookie_bruto, str) else cookie_bruto
            st.session_state.update({
                'logado': True,
                'token_jwt': dados_sessao.get('token'),
                'nome_usuario': dados_sessao.get('nome'),
                'id_usuario': dados_sessao.get('id_usuario'),
                'etapa_atual': dados_sessao.get('etapa', 'scan'),
                'dados_pendentes': dados_sessao.get('dados')
            })
            st.rerun()
        except:
            limpar_sessao()

# Tela de Login
if not st.session_state['logado']:
    st.title("🔐 Autenticação")
    input_usuario = st.text_input("ID do Usuário")
    input_senha = st.text_input("Senha", type="password")
    
    if st.button("Entrar", use_container_width=True):
        sucesso, mensagem, dados = autenticar_usuario(input_usuario, input_senha)
        if sucesso:
            st.session_state.update({
                'logado': True,
                'nome_usuario': dados.get('nome_usuario'),
                'id_usuario': input_usuario,
                'token_jwt': dados.get('token')
            })
            atualizar_cookie_sessao(dados.get('token'), dados.get('nome_usuario'), input_usuario, "scan", None)
            st.rerun()
        else:
            st.error(mensagem)

# Área Principal (Usuário Logado)
else:
    # Captura de Geolocalização para auditoria em segundo plano
    geo = get_geolocation(component_key='auditoria_geo')
    if geo:
        st.session_state['coordenadas'] = geo.get('coords')

    # Cabeçalho do App
    with st.container():
        col1, col2 = st.columns([3, 1])
        col1.write(f"👤 **Usuário:** {st.session_state['nome_usuario']}")
        if col2.button("Sair"):
            limpar_sessao()
            st.session_state.clear()
            st.rerun()
    st.divider()

    # Controle de Fluxo de Telas
    etapa = st.session_state['etapa_atual']

    if etapa == 'scan':
        st.subheader("📷 Ler QR Code")
        dados_qr = qrcode_scanner(key='scanner_principal')
        
        if dados_qr:
            try:
                dados_processados = json.loads(dados_qr)
                st.session_state['dados_pendentes'] = dados_processados
                st.session_state['etapa_atual'] = 'formulario'
                atualizar_cookie_sessao(
                    st.session_state['token_jwt'], 
                    st.session_state['nome_usuario'], 
                    st.session_state['id_usuario'], 
                    "formulario", 
                    dados_processados
                )
                st.rerun()
            except:
                st.error("Formato de QR Code inválido.")

        # Histórico Rápido
        with st.expander("📊 Meu Histórico de Hoje"):
            if st.button("Gerar Relatório do Dia"):
                st.info("Buscando registros...") # Aqui entra a chamada da API

    elif etapa == 'formulario':
        dados_ativos = st.session_state.get('dados_pendentes', {})
        st.subheader(f"📍 Local: {dados_ativos.get('id', 'Desconhecido')}")
        
        atividade_selecionada = st.selectbox("Ação", OPCOES_ATIVIDADE)
        em_deslocamento = st.checkbox("Em trânsito?")
        
        col_cancelar, col_confirmar = st.columns(2)
        if col_cancelar.button("Cancelar", use_container_width=True):
            st.session_state['etapa_atual'] = 'scan'
            st.rerun()
            
        if col_confirmar.button("Confirmar", type="primary", use_container_width=True):
            # Payload genérico montado para envio
            coords = st.session_state.get('coordenadas', {})
            payload = {
                "timestamp": datetime.now().isoformat(),
                "id_usuario": st.session_state['id_usuario'],
                "id_local": dados_ativos.get('id'),
                "acao": atividade_selecionada,
                "latitude": coords.get('latitude'),
                "longitude": coords.get('longitude'),
                "em_movimento": em_deslocamento
            }
            
            sucesso, msg_resposta = enviar_registro(payload)
            if sucesso:
                st.session_state['etapa_atual'] = 'sucesso'
                st.rerun()
            else:
                st.error(msg_resposta)

    elif etapa == 'sucesso':
        st.success("Registro enviado com sucesso!")
        if st.button("Novo Escaneamento", type="primary"):
            st.session_state['etapa_atual'] = 'scan'
            atualizar_cookie_sessao(
                st.session_state['token_jwt'], 
                st.session_state['nome_usuario'], 
                st.session_state['id_usuario'], 
                "scan", 
                None
            )
            st.rerun()