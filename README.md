# Field Ops Tracker: Aplicativo para Fiscais de Transporte

Um aplicativo web construído com Streamlit, projetado para facilitar as operações de campo em sistemas de transporte público. A ferramenta permite que fiscais e equipes operacionais registrem inspeções, mapeiem atividades e enviem dados estruturados diretamente do campo para um banco de dados.

O aplicativo funciona como a interface de coleta de dados no terreno, integrando-se a APIs externas para alimentar painéis de controle e indicadores de operação.

# Principais Funcionalidades

* Leitura de QR Code: Integração com a câmera do dispositivo móvel para identificar automaticamente estações, plataformas ou veículos escaneados.
* Captura de Geolocalização: Registro de latitude e longitude em segundo plano no momento do envio do formulário, garantindo a auditoria da posição do fiscal.
* Sessão Persistente: Gerenciamento de estado e login através de cookies. Caso o navegador seja fechado ou recarregado, o usuário não perde a etapa atual.
* Integração via API: Comunicação RESTful para autenticação (via JWT) e ingestão de dados em formato JSON.
* Geração de Relatórios: Opção para o fiscal extrair o seu histórico diário de atividades diretamente para um arquivo Excel (.xlsx).

# Tecnologias e Bibliotecas

* Python 3.8+
* Streamlit (Interface Web e Lógica de Frontend)
* Pandas e OpenPyXL (Processamento de dados e planilhas)
* Requests (Comunicação HTTP/API)
* extensões do Streamlit: streamlit-qrcode-scanner, streamlit-js-eval, extra-streamlit-components

## Como Executar Localmente

1. Clone o repositório para a sua máquina:
```bash
git clone [https://github.com/SEU_USUARIO/field-ops-tracker.git](https://github.com/SEU_USUARIO/field-ops-tracker.git)
cd field-ops-tracker
