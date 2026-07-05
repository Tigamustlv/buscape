# buscape
Um sistema completo de consulta rápida de clientes e operações financeiras, desenvolvido com FastAPI, SQLite e frontend em HTML/CSS/JavaScript puro, focado em performance, simplicidade e escalabilidade.


# 🚀 Sistema de Consulta Inteligente (FastAPI + SQLite + Frontend Dinâmico)

Sistema completo de consulta de clientes e operações financeiras, desenvolvido com foco em **performance, simplicidade e escalabilidade**.

Permite buscas rápidas em grandes volumes de dados simulando cenários reais de operação bancária / financeira.

---

## 🔍 Demonstração

O sistema permite pesquisar por:

- Nome do cliente  
- CPF / Documento  
- Número de contrato  
- Empresa / Originador  

E retorna os resultados de forma instantânea em uma interface dinâmica.

---

## ⚙️ Tecnologias Utilizadas

- ⚡ FastAPI (API backend rápida e leve)
- 🗄️ SQLite (banco de dados local)
- 🌐 HTML5 + CSS3 + JavaScript puro
- 🔄 Fetch API (requisições assíncronas)
- 🎯 CORS Middleware

---

## 🧠 Funcionalidades

- 🔎 Busca em múltiplos campos simultaneamente  
- 📊 Retorno dinâmico em tabela  
- 📈 Contador de resultados em tempo real  
- 🧾 Exibição de cliente, contrato e empresa  
- ⚡ API rápida e leve  
- 💬 Interface estilo sistema corporativo  
- ⌨️ Suporte a tecla ENTER para busca  
- 🧠 Título dinâmico na aba do navegador  

---

## 🖥️ Interface

A interface foi projetada para operação rápida e simples:

- Barra de pesquisa centralizada  
- Feedback imediato de busca  
- Tabela organizada estilo CRM  
- Mensagens de status (buscando, erro, sem resultados)

---

## 🚀 Como executar o projeto

### 1. Instalar dependências

pip install fastapi uvicorn

## 2. Rodar o servidor
uvicorn main:app --reload

## 3. Acessar no navegador
http://127.0.0.1:8000/menu

## 📁 Estrutura do Projeto
  projeto/
  ├── main.py
  ├── index.html
  ├── clientes.db
  └── venv/

## 🔧 Exemplo de busca

Entrada:
João
Saída:
João Silva | Empresa 1 | 100001
João Ferreira | Empresa 2 | 100002
João Andrade | Empresa 3 | 100003


🚀 Possíveis melhorias futuras
📌 Paginação para grandes volumes de dados
⚡ Índices no SQLite para performance
🔎 Autocomplete inteligente
💾 Cache de consultas
🔐 Sistema de login
☁️ Deploy em produção (Docker / Cloud)
