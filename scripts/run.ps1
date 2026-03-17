# Liga YGO Marabá - Script de Inicialização
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Liga YGO Marabá - Sistema Web Flask" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Verificando dependências..." -ForegroundColor Green
$flaskInstalled = Get-Command python -ErrorAction SilentlyContinue

if ($flaskInstalled) {
    $pipList = python -m pip list
    if ($pipList -match "Flask") {
        Write-Host "✓ Dependências OK!" -ForegroundColor Green
    } else {
        Write-Host "⚠ Flask não encontrado. Instalando dependências..." -ForegroundColor Yellow
        python -m pip install -r requirements.txt
    }
} else {
    Write-Host "❌ Python não encontrado. Certifique-se de que o Python está instalado." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "🚀 Iniciando aplicação Flask..." -ForegroundColor Green
Write-Host "🌐 Acesse: http://localhost:5000" -ForegroundColor Cyan
Write-Host ""
Write-Host "Pressione Ctrl+C para parar o servidor" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan

# Definir variáveis de ambiente
$env:FLASK_APP = "app.py"
$env:FLASK_ENV = "development"

# Executar a aplicação
try {
    python app.py
} catch {
    Write-Host "❌ Erro ao iniciar a aplicação: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "Pressione qualquer tecla para fechar..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")