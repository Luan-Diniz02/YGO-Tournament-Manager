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
| `/visualizar_torneios` | `visualizar_torneios.html` | Lista de todas as etapas cadastradas (com coluna de temporada) |
| `/torneio/<id>` | `painel_torneio.html` | Resultados de uma etapa específica |

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
  informações exclusivas do contexto individual: histórico etapa a etapa, conquistas
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

---

## Fórmula de Pontuação

```
Pontos por torneio = (Vitórias × 3) + Empates + 1 (participação)
Pontos globais     = soma dos pontos de todos os torneios
Win Rate           = Vitórias / (Vitórias + Derrotas + Empates) × 100
Conversão          = Títulos / Top Cuts × 100
```

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
ao exibir performance por etapa (não recalcular no template).

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
