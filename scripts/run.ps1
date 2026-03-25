# Liga YGO Maraba - Script de Inicializacao
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Liga YGO Maraba - Sistema Web Flask" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Verificando dependencias..." -ForegroundColor Green
$pythonInstalled = Get-Command python -ErrorAction SilentlyContinue

if ($pythonInstalled) {
    $pipList = python -m pip list
    if ($pipList -match "Flask") {
        Write-Host "Dependencias OK!" -ForegroundColor Green
    } else {
        Write-Host "Flask nao encontrado. Instalando dependencias..." -ForegroundColor Yellow
        python -m pip install -r requirements.txt
    }
} else {
    Write-Host "Python nao encontrado. Certifique-se de que o Python esta instalado." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Iniciando aplicacao Flask..." -ForegroundColor Green
Write-Host "Acesse: http://localhost:5000" -ForegroundColor Cyan
Write-Host ""
Write-Host "Pressione Ctrl+C para parar o servidor" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan

# Garante execucao a partir da raiz do projeto
Set-Location (Join-Path $PSScriptRoot "..")

try {
    python -m web.app
} catch {
    Write-Host "Erro ao iniciar a aplicacao: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "Pressione qualquer tecla para fechar..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")