@echo off
echo ========================================
echo Liga YGO Maraba - Sistema Web Flask
echo ========================================
echo.

echo Verificando dependencias...
pip show Flask > nul 2>&1
if errorlevel 1 (
    echo Flask nao encontrado. Instalando dependencias...
    pip install -r requirements.txt
) else (
    echo Dependencias OK!
)

echo.
echo Iniciando aplicacao Flask...
echo Acesse: http://localhost:5000
echo.
echo Pressione Ctrl+C para parar o servidor
echo ========================================

pushd "%~dp0.."
python -m web.app
popd

pause