# Context — Liga YGO Marabá

Regras, decisões de arquitetura e padrões visuais estabelecidos para o projeto.
Este documento deve ser consultado antes de qualquer nova implementação.

---

## Arquitetura de Páginas

### Mapa de rotas

| Rota | Template | Propósito |
|---|---|---|
| `/` | `index.html` | Landing page com acesso rápido às seções |
| `/dashboard` | `dashboard_estatisticas.html` | Ranking unificado + estatísticas comparativas |
| `/ranking` | — | **Redireciona para `/dashboard`** (não tem template próprio) |
| `/dashboard/duelista/<nome>` | `dashboard_duelista.html` | Perfil individual — drill-down exclusivo |
| `/visualizar_torneios` | `visualizar_torneios.html` | Lista de todas as etapas cadastradas |
| `/torneio/<id>` | `painel_torneio.html` | Resultados de uma etapa específica |
| `/admin/cadastrar_torneio` | `cadastrar_torneio.html` | Formulário de criação de torneio (admin) |
| `/admin/buscar_duelista` | `buscar_duelista.html` | Busca + edição/reativação de duelistas (admin) |
| `/admin/alterar/<nome>` | `alterar_duelista.html` | Formulário de edição de duelista (admin) |

### Regra de responsabilidade das páginas

- **`/dashboard`** é a única lista comparativa pública. Mostra todos os duelistas com:
  posição no ranking, pontos, V/D, Win Rate, Top Cut, Títulos e Conversão Top→Título.
- **`/ranking`** não tem template — existe apenas para compatibilidade de links externos,
  redirecionando imediatamente para `/dashboard`.
- **`/dashboard/duelista/<nome>`** é o destino de drill-down. Deve conter **apenas**
  informações exclusivas do contexto individual: histórico etapa a etapa, conquistas
  contextuais, win rate por torneio. Não duplicar dados já visíveis no ranking.

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
