# Tubify - Design System & Documentação de UX/UI

## 1. Visão Geral do Produto
- **Nome:** Tubify
- **Slogan:** Transforme vídeos em conhecimento
- **Público-alvo:** Estudantes, universitários, autodidatas
- **Proposta de Valor:** Resumos automáticos de vídeos do YouTube usando IA para economizar tempo e facilitar o estudo.
- **Identidade Visual:** Verde (#16A34A) e Branco (#FFFFFF). Estilo clean, minimalista e moderno.

---

## 2. Sitemap (Estrutura das Páginas)

### 1. Home (Landing Page)
Página principal focada em conversão e demonstração de valor imediato.
- **Header:** Logo Tubify (esquerda), Links de navegação (Como funciona, Planos), Botão "Entrar" (Outline), Botão "Começar Agora" (Solid Green).
- **Hero Section:**
  - Headline: "Transforme horas de vídeo em minutos de leitura."
  - Subheadline: "A ferramenta de IA que resume vídeos do YouTube para você estudar melhor e mais rápido."
  - **Input Principal:** Campo grande e centralizado para colar URL do YouTube.
  - CTA: Botão "Gerar Resumo Grátis".
- **Social Proof:** "Usado por +10.000 estudantes" (logotipos de universidades ou avatares).
- **Features (Cards):**
  - "Economize Tempo": Ícone de relógio.
  - "Foco no Essencial": Ícone de alvo.
  - "Exportação PDF/Notion": Ícone de download.
- **Footer:** Links úteis, Copyright, Redes Sociais.

### 2. Resultado do Resumo (Viewer)
Página onde o usuário consome o conteúdo gerado.
- **Header Simplificado:** Logo e Menu de Usuário.
- **Conteúdo Principal:**
  - **Vídeo Embed:** Player do YouTube (lado esquerdo ou topo).
  - **Card de Resumo:** Texto estruturado em tópicos (bullets), timestamps clicáveis.
  - **Barra de Ações:** Botões para Copiar Texto, Baixar PDF, Salvar no Notion (Premium).
- **Sidebar/Bottom (Upsell):** "Gostou? Crie sua conta para salvar este resumo." (Para visitantes).

### 3. Login / Cadastro
Foco em simplicidade e benefícios.
- **Layout Split:**
  - Esquerda: Imagem ilustrativa ou depoimento de usuário.
  - Direita: Formulário.
- **Formulário:**
  - "Crie sua conta gratuita"
  - Google Login (Destaque)
  - Email / Senha
- **Benefícios (Bullet points visuais):** "Histórico ilimitado", "Resumos mais longos", "Sem anúncios".

### 4. Dashboard (Área Logada)
O hub central do usuário.
- **Sidebar (Esquerda):**
  - Botão "Novo Resumo" (Destaque).
  - Menu: Meus Resumos, Favoritos, Configurações.
  - Card de Status: "Plano Gratuito" -> Botão "Upgrade".
- **Área Principal:**
  - **Input Rápido:** "Cole um link aqui para resumir..."
  - **Estatísticas:** "Vídeos resumidos hoje: 2/5", "Tempo economizado: 45min".
  - **Grid de Resumos Recentes:** Cards com thumbnail do vídeo, título e data.

### 5. Planos (Pricing)
Comparativo claro focando em valor.
- **Toggle:** Mensal / Anual (Desconto).
- **Cards de Planos:**
  - **Visitante/Free:** "Para curiosos". 3 resumos/dia. Limite de 15min/vídeo.
  - **Pro (Destaque):** "Para estudantes sérios". Ilimitado. Vídeos longos. Exportação. Badge "Mais Popular".
- **FAQ:** Perguntas frequentes sobre cancelamento e limites.

---

## 3. Guia de Estilo (UI)

### Paleta de Cores
- **Primary Green:** `#16A34A` (Botões principais, destaques, ícones ativos)
- **Light Green:** `#86EFAC` (Backgrounds sutis, hovers, badges)
- **White:** `#FFFFFF` (Background de cards e página)
- **Text Dark:** `#374151` (Títulos e corpo de texto principal)
- **Text Light:** `#6B7280` (Legendas, textos secundários)
- **Background Gray:** `#F3F4F6` (Fundo da aplicação)

### Tipografia
- **Font Family:** 'Inter', sans-serif (Moderno, legível, excelente para UI).
- **Headings:** Bold (600/700). Ex: H1 32px, H2 24px.
- **Body:** Regular (400). 16px para leitura confortável.
- **Buttons:** Medium (500).

### Componentes Chave
- **Cards:** Background branco, `border-radius: 12px`, sombra suave (`box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1)`).
- **Botões:**
  - *Primary:* Fundo `#16A34A`, Texto Branco, `border-radius: 8px`, Hover darken.
  - *Secondary:* Borda `#16A34A`, Texto `#16A34A`, Fundo Transparente.
- **Inputs:** Borda cinza claro (`#E5E7EB`), Focus ring verde (`#16A34A`).

---

## 4. Wireframes Textuais (Estrutura Visual)

### A. Home Page
```
+---------------------------------------------------------------+
| [Logo Tubify]                            [Login] [CRIAR CONTA]|
+---------------------------------------------------------------+
|                                                               |
|           TRANSFORME VÍDEOS EM CONHECIMENTO                   |
|      A IA que resume seus estudos em segundos                 |
|                                                               |
|      [ Cole o link do YouTube aqui...            ] [ RESUMIR ]|
|                                                               |
|      [Icon] Rápido    [Icon] Preciso    [Icon] Gratuito       |
|                                                               |
+---------------------------------------------------------------+
| COMO FUNCIONA                                                 |
| [Passo 1: Copie] -> [Passo 2: Cole] -> [Passo 3: Aprenda]     |
+---------------------------------------------------------------+
```

### B. Dashboard (Logado)
```
+----------------+----------------------------------------------+
| [Logo]         |  Olá, Rafael!                                |
|                |                                              |
| + NOVO RESUMO  |  [ Input URL Rápido...              ] [Go]   |
|                |                                              |
| [Icon] Home    |  SEUS RESUMOS RECENTES                       |
| [Icon] Salvos  |  +----------------+  +----------------+      |
| [Icon] Config  |  | [Thumb]        |  | [Thumb]        |      |
|                |  | Aula de Python |  | História da... |      |
| ---------------|  | 10 min econom..|  | 5 min econom...|      |
| [Plano FREE]   |  +----------------+  +----------------+      |
| [Upgrade PRO]  |                                              |
+----------------+----------------------------------------------+
```

### C. Página de Resumo
```
+---------------------------------------------------------------+
| [Logo]                                       [Menu Usuário]   |
+---------------------------------------------------------------+
|  < Voltar                                                     |
|                                                               |
|  TÍTULO DO VÍDEO: Introdução ao Machine Learning              |
|                                                               |
|  +-----------------------+   +-----------------------------+  |
|  |                       |   | RESUMO GERADO PELA IA       |  |
|  | [ PLAYER YOUTUBE    ] |   |                             |  |
|  | [                   ] |   | • Tópico Principal 1        |  |
|  |                       |   |   Explicação detalhada...   |  |
|  +-----------------------+   |                             |  |
|                              | • Tópico Principal 2        |  |
|  [Copiar] [Baixar PDF]       |   Explicação detalhada...   |  |
|                              +-----------------------------+  |
+---------------------------------------------------------------+
```
