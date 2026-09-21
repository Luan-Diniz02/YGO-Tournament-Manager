# Context — Liga YGO Marabá

Regras, decisões de arquitetura e padrões visuais estabelecidos para o projeto.
Este documento deve ser consultado antes de qualquer nova implementação.

---

## Arquitetura de Páginas

### Mapa de rotas públicas

| Rota | Template | Propósito |
|---|---|---|
| `/` | `index.html` | Landing page com acesso rápido às seções e card da temporada ativa |
| `/dashboard` | `dashboard_estatisticas.html` | Ranking unificado + estatísticas comparativas (filtrável por temporada) |
| `/ranking` | — | **Redireciona para `/dashboard`** (não tem template próprio) |
| `/dashboard/duelista/<nome>` | `dashboard_duelista.html` | Perfil individual — drill-down exclusivo |
| `/visualizar_torneios` | `visualizar_torneios.html` | Lista de todos os torneios cadastrados (com coluna de temporada) |
| `/torneio/<id>` | `painel_torneio.html` | Resultados de um torneio específico |

### Mapa de rotas administrativas (`/admin/*` — protegidas por sessão)

| Rota | Método | Propósito |
|---|---|---|
| `/admin/cadastrar_torneio` | GET / POST | Formulário de criação de torneio |
| `/admin/torneio/<id>/editar` | GET / POST | Edição de torneio (GET retorna JSON, POST aplica) |
| `/admin/torneio/<id>/excluir` | POST | Exclusão de torneio |
| `/admin/buscar_duelista` | GET / POST | Busca + edição/reativação de duelistas |
| `/admin/alterar/<nome>` | GET / POST | Formulário de edição de duelista |
| `/admin/temporadas` | GET | Listagem e gerenciamento de temporadas |
| `/admin/temporadas/cadastrar` | POST | Criação de nova temporada |
| `/admin/temporadas/<id>/ativar` | POST | Define uma temporada como ativa (atual) |
| `/admin/temporadas/<id>/editar` | POST | Edição de nome, datas e status de temporada |
| `/admin/temporadas/<id>/excluir` | POST | Exclusão de temporada (torneios não são apagados) |

### Regra de responsabilidade das páginas

- **`/dashboard`** é a única lista comparativa pública. Mostra todos os duelistas com:
  posição no ranking, pontos, V/D, Win Rate, Top Cut, Títulos e Conversão Top→Título.
- **`/ranking`** não tem template — existe apenas para compatibilidade de links externos,
  redirecionando imediatamente para `/dashboard`.
- **`/dashboard/duelista/<nome>`** é o destino de drill-down. Deve conter **apenas**
  informações exclusivas do contexto individual: histórico torneio a torneio, conquistas
  contextuais, win rate por torneio. Não duplicar dados já visíveis no ranking.

---

## Temporadas

### Modelo de dados

A tabela `temporadas` agrupa torneios em períodos competitivos:

```sql
CREATE TABLE temporadas (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    nome       VARCHAR(120) NOT NULL,
    data_inicio DATE,
    data_fim    DATE,
    ativa      TINYINT(1) NOT NULL DEFAULT 0,  -- apenas uma pode ser ativa
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

A coluna `temporada_id` em `torneios` usa `ON DELETE SET NULL`:
- Ao excluir uma temporada, os torneios **não são apagados**
- A coluna `temporada_id` dos torneios vinculados passa para `NULL`
- Esses torneios ficam visíveis apenas no filtro "Geral (All-time)"

### Vínculo torneio-temporada

O vínculo é **híbrido**:
- Ao cadastrar um torneio, a temporada ativa é pré-selecionada no dropdown
- O admin pode alterar ou deixar sem temporada ("Geral / Sem Temporada")
- Ao editar um torneio (modal), o campo Temporada é pré-preenchido com o vínculo atual

### Filtro de ranking por temporada

O ranking (`/dashboard`) filtra por temporada usando uma **subquery** — nunca um `LEFT JOIN` no `torneios` com filtro na cláusula de JOIN (que não filtra `torneio_participantes`). Além disso, o backend omite automaticamente qualquer duelista que possua 0 participações na temporada vigente, assegurando que o ranking liste somente os jogadores ativos no filtro selecionado:

```sql
-- ✅ Correto — subquery pré-filtra as participações antes dos SUM()
FROM duelistas d
LEFT JOIN (
    SELECT tp.*
    FROM torneio_participantes tp
    JOIN torneios t ON t.id = tp.torneio_id
    WHERE t.temporada_id = %s
) tp_f ON tp_f.duelista_id = d.id
```

```sql
-- ❌ Errado — tp entra SEM filtro; o filtro no JOIN de torneios não impede que
--             tp.vitorias, tp.derrotas etc. somem todos os torneios
FROM duelistas d
LEFT JOIN torneio_participantes tp ON tp.duelista_id = d.id
LEFT JOIN torneios t ON t.id = tp.torneio_id AND t.temporada_id = %s
```

O `temporada_atual` passado ao template é **sempre `str`** para garantir que a comparação Jinja2 `temporada_atual == temp.id|string` funcione corretamente no `<select>`.

---

## Padrão Visual (UI)

### Card headers

Todas as páginas usam **`card-header bg-dark text-white`** como cabeçalho de seção.
Não usar `bg-primary`, `bg-warning`, `bg-info`, `bg-secondary` ou `dashboard-hero-card`.

```html
<!-- ✅ Correto -->
<div class="card-header bg-dark text-white d-flex justify-content-between align-items-center">
    <h4 class="mb-0"><i class="fas fa-medal"></i> Título da Seção</h4>
    <span class="badge bg-light text-dark">N itens</span>
</div>

<!-- ❌ Evitar -->
<div class="card-header bg-primary text-white"> ... </div>
<div class="card dashboard-hero-card"> ... </div>
```

### Tabelas

- Desktop: `<table class="table table-hover mb-0">` com `<thead class="table-dark">`
- Mobile: `.mobile-cards-container.p-3` com `.mobile-card.shadow-sm.border-0`
- Wrapper do card pai: `wrapper-transparent-mobile` em páginas com tabela/lista

### Botão de perfil individual

O botão para acessar o perfil de um duelista usa **`fa-user`** (não `fa-chart-line`).

```html
<a href="{{ url_for('public.dashboard_duelista', nome=duelista.nome) }}"
   class="btn btn-outline-primary btn-sm" title="Ver perfil de {{ duelista.nome }}">
    <i class="fas fa-user"></i>
</a>
```

### Inputs e formulários

O `border-radius` de todos os inputs é controlado globalmente via variáveis Bootstrap
no `style.css`. **Não adicionar `border-radius` inline em inputs.**

```css
/* style.css — :root */
--bs-border-radius:    10px;
--bs-border-radius-sm: 8px;
```

### Validação de campos (`script.js`)

A validação "apenas letras e espaços" aplica-se **somente** a `input[name="nome_duelista"]`.
Campos `name="nome"` (temporadas, torneios) **não** têm essa restrição — aceitam hífens,
números e qualquer caractere.

### Botões

Todos os botões têm `border-radius: 25px` via regra global no `style.css`.
Use as classes Bootstrap padrão (`btn-primary`, `btn-outline-secondary`, etc.)
com os gradientes já definidos no CSS.

### Suporte a Temas (Dark Mode & Light Mode)

- **Alternância Dinâmica**: Alternância instantânea entre temas Claro e Escuro através do atributo `data-bs-theme="dark|light"` no elemento `<html>`.
- **Persistência**: Armazenamento no `localStorage` sob a chave `'ygo-theme'`, com fallback inteligente para a preferência do sistema operacional (`prefers-color-scheme`).
- **Polyfill Bootstrap 5.3**: Como a aplicação utiliza Bootstrap 5.1.3 via CDN, o `style.css` implementa polyfill completo para os utilitários semânticos contextuais (`.bg-*-subtle`, `.border-*-subtle`, `.text-*-emphasis`), garantindo retrocompatibilidade total e fundos/bordas consistentes em ambos os temas sem elementos transparentes.
- **Harmonia Dourada e Acessibilidade WCAG AA**:
  - **Ícones Ouro**: Ícones comemorativos de troféu e medalhas (`i.text-warning`, `.fa-trophy`, `.fa-medal`, `.ranking-position-1 i`) mantêm dourado puro vibrante (`#f59e0b` / `--ygo-gold`, e `#fbbf24` em headers escuros), eliminando a aparência bronze/amarronzada em qualquer tema.
  - **Textos de Aviso**: `.text-warning` textual no tema claro utiliza dourado âmbar de alta legibilidade (`#d97706` / `--ygo-gold-dark`), atingindo contraste WCAG AA sobre branco sem descaracterizar a identidade de ouro.
  - **Informações e Sucesso**: `.text-info` no modo claro utiliza `#0369a1` (azul ciano profundo) e `.text-success` utiliza `#047857` (verde esmeralda profundo). Botões `.btn-info` contam com tipografia em alto contraste com o fundo esportivo.
- **Refinamento Dark Mode**:
  - Bordas estruturais padrão (`.border`, `.border-top`, `.border-bottom`, `.border-start`, `.border-end`) utilizam a variável temática `var(--ygo-border)`, eliminando vazamentos de bordas cinza-claras do Bootstrap.
  - Linhas de tabela de duelistas inativos (`.table-danger`) utilizam fundo vermelho escuro translúcido (`rgba(239, 68, 68, 0.15)`) com texto atenuado, evitando estouros de contraste com o rosa claro legado do Bootstrap.
  - A limpeza dos campos de busca (`script.js`) reseta `borderColor = ''`, respeitando a estilização do tema ativo em vez de fixar valores hexadecimais legados.
- **Gráficos Reativos (Chart.js)**:
  - Os gráficos de Rosca e Linha no perfil individual (`dashboard_duelista.html`) detectam o tema inicial para definir paletas de grade, legendas e eixos, além de escutarem o evento global `themeChanged` para atualizar as cores instantaneamente na troca de tema sem necessidade de recarregar a página.

### Alertas e Mensagens de Confirmação

- **Contraste no Dark Mode**: Os alertas (`.alert`, `.alert-success`, `.alert-danger`, `.alert-info`, `.alert-warning`) utilizam fonte branca (`#ffffff`) sobre os fundos temáticos, ícones em destaque vibrante e botão de fechar (`.btn-close`) com filtro invertido, eliminando conflitos de cor e garantindo legibilidade imediata (WCAG AAA).
- **Permanência de Avisos**: Alertas de confirmação crítica (como avisos de exclusão de torneios/temporadas e ativação de temporadas em modais) e estados informativos são permanentes e **não somem automaticamente**, assegurando tempo adequado de leitura e prevenção contra erros acidentais. Mensagens flash contam com botão de fechar (`.btn-close`) para dispensa manual.

### Tela Inicial (Hub Vivo da Liga)

- **Hero sem Redundâncias**: Apresentação visual limpa da liga sem replicar botões que já existem na barra de navegação superior.
- **Chamada Focal da Temporada**: Card da temporada ativa com atalho direto e único para a classificação da corrida atual (`Ranking da Temporada`).
- **Métricas Rápidas**: Painel consolidado com contadores de `Torneios Realizados`, `Duelistas Registrados` e `Partidas Disputadas`.
- **Destaques Vivos**: Cards dinâmicos exibindo o **Líder Atual da Liga** (com pontos, Win Rate, títulos e link para perfil) e o **Último Torneio Realizado** (com data, participantes, campeão consagrado e link direto).
- **Ações Administrativas**: Exibidas exclusivamente para administradores logados, mantendo a tela pública livre de botões de login duplicados.

### Pódio Top 3 (Showcase)

- Exibido no topo da página de ranking (`/dashboard`) quando existirem ao menos 3 duelistas.
- Estrutura visual: 2º Lugar (esquerda), 1º Lugar (centro elevado em destaque dourado) e 3º Lugar (direita).

### Visualização de Dados e Cartões Compartilháveis

- **Chart.js no perfil individual (`dashboard_duelista.html`)**:
  - **Gráfico de Rosca (Distribuição de Partidas)**: Exibe a proporção de Vitórias vs Derrotas com as porcentagens correspondentes nas legendas (`Vitórias (X%)`, `Derrotas (Y%)`) e tooltips, preservando o centro do anel desobstruído para evitar duplicação cognitiva com o cartão superior de Win Rate.
  - **Gráfico de Linha (Evolução de Pontos por Torneio)**: Escala do eixo Y com graduação em intervalos de 3 pontos (`stepSize: 3`), alinhado aos múltiplos de pontuação de rodadas oficiais.
  - **Histórico de Torneios**: Na coluna de Posição (desktop e mobile), a colocação numérica geral precede o selo de Top Cut (ex: `1º TOP`, `2º TOP`).
- **Compartilhamento Genérico Nativo (`Web Share API Level 2`)**:
  - Tanto o **Card Oficial do Duelista** quanto o **Ranking Oficial da Liga** utilizam compartilhamento nativo com **anexo do arquivo PNG gerado** via `navigator.share({ files: [file] })`, permitindo enviar a imagem diretamente para WhatsApp, Instagram, Telegram, Twitter/X, Discord, salvar em arquivos, etc.
  - **Legenda limpa no Ranking**: O texto que acompanha a imagem do ranking inclui exclusivamente a chamada e o link da aplicação (`Confira o ranking completo em: ...`), evitando repetição textual de dados já presentes no cartão.
  - **Fallback gracioso**: Em dispositivos sem suporte ao anexo de arquivos via Web Share (ex.: desktops), o sistema faz o download automático do PNG, copia a imagem para a área de transferência (`ClipboardItem`) e abre o WhatsApp Web com o texto e o link.

### Grid e Centralização Mobile

- Cards mobile de ranking (`dashboard_estatisticas.html`) centralizam harmoniosamente todos os dados e métricas das 3 colunas (`V / D`, `Win Rate`, `Partic.`, `Top Cut`, `Títulos`, `Conv. Top`) através de `.mobile-stat-item.text-center` com `align-items: center; text-align: center;`.
- Cards mobile de torneios utilizam `.mobile-stats-grid.mobile-stats-grid-2` (duas colunas simétricas) com itens centralizados (`align-items: center; text-align: center;`) para **Vitórias** e **Derrotas**.
- No perfil individual do duelista (`dashboard_duelista.html`), o histórico mobile centraliza harmonicamente as métricas de **Placar**, **Rodadas** e **Posição** (`.mobile-stat-item.text-center`).
- A tela de busca/gerenciamento de duelistas no mobile utiliza o mesmo grid de 2 colunas (`.mobile-stats-grid-2`), distribuindo em 2x2 com conteúdo centralizado:
  - Linha 1: Vitórias (50%) e Derrotas (50%)
  - Linha 2: Participações (50%) e Status (50%)

### Terminologia Padrão

- **Torneio / Torneios**: Utilizado de forma unificada para identificar os eventos competitivos da liga (evitar "etapas").
- **Participações**: Utilizado exclusivamente para identificar assiduidade/frequência de duelistas (evitar "torneios disputados" ou "assiduidade" em cards e métricas).

---

## Fórmula de Pontuação & Regra de Double Loss

Em conformidade com o regulamento oficial de torneios de Yu-Gi-Oh! (Konami Tournament Policy), empates não existem no formato competitivo moderno; partidas não resolvidas ou penalidades resultam em **Double Loss** (derrota mútua, 0 pontos para ambos e +1 derrota):

```
Pontos por torneio = (Vitórias × 3) + 1 (participação)
Pontos globais     = soma dos pontos de todos os torneios
Win Rate           = Vitórias / (Vitórias + Derrotas) × 100
Conversão Top Cut  = Títulos / Top Cuts × 100  (renderiza '—' se Top Cuts == 0)
```

> **Nota de Retrocompatibilidade**: O campo `empates` permanece no banco de dados com valor padrão `0`, garantindo suporte a registros legados sem quebrar o esquema da base.

### Critério de desempate no ranking

```python
key=lambda d: (-d.pontos, d.derrotas, d.nome.casefold())
```

---

## Conquistas Contextuais

Exibidas apenas no perfil individual (`dashboard_duelista.html`).
São calculadas comparando o duelista com todos os outros ativos na liga.

| Conquista | Condição |
|---|---|
| 🥇 Líder do Ranking | `posicao_ranking == 1` |
| 🏆 Maior Campeão | `campeonatos == max_campeonatos` e `campeonatos > 0` |
| 🎯 Rei do Top Cut | `tops == max_tops` e `tops > 0` |
| ⚡ Elite Win Rate | `win_rate_geral == max_win_rate` (mín. 2 participações) |

---

## Regras para Dados do Perfil Individual

O `dados.historico` já carrega `win_rate_evento` para cada torneio — **usar esse campo**
ao exibir performance por torneio (não recalcular no template).

Campos disponíveis por evento no histórico:

```python
{
    'torneio_id', 'torneio_nome', 'torneio_data', 'rodadas',
    'vitorias', 'derrotas', 'empates', 'pontos_obtidos',
    'topou_torneio', 'colocacao_top',
    'partidas',         # calculado
    'win_rate_evento',  # calculado
    'posicao_geral',    # calculado via listar_participantes_torneio
}
```

---

## Segurança

- CSRF token obrigatório em **todos** os formulários mutáveis (`POST`).
- Área `/admin/*` protegida por sessão + guard em `auth.py`.
- `FLASK_SECRET_KEY` é obrigatória — a app falha no boot sem ela.
- `ADMIN_ALLOWED_IPS` restringe acesso ao painel admin por IP (opcional).

---

## Convenções de Commit

Seguir Conventional Commits:

```
feat(escopo): descrição curta
fix(escopo): descrição curta
refactor(escopo): descrição curta
style: descrição de mudança visual
docs: descrição de atualização de documentação
```
