@echo off
echo ========================================
echo Liberando porta 5000 no Windows Firewall
echo ========================================

:: Verifica se está executando como administrador
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo ERRO: Este script precisa ser executado como Administrador!
    echo.
    echo Clique com botao direito no arquivo e selecione:
    echo "Executar como administrador"
    echo.
    pause
    exit /b 1
)

echo.
echo Criando regra no firewall para porta 5000...

:: Remove regra existente (se houver)
netsh advfirewall firewall delete rule name="Liga YGO - Flask App" >nul 2>&1

:: Adiciona nova regra
netsh advfirewall firewall add rule name="Liga YGO - Flask App" dir=in action=allow protocol=TCP localport=5000

if %errorlevel% equ 0 (
    echo ✓ Regra de firewall criada com sucesso!
    echo.
    echo Agora você pode acessar pelo celular em:
    echo http://192.168.0.8:5000
    echo.
    echo Certifique-se de que:
    echo - O celular está na mesma rede WiFi
    echo - A aplicação Flask está rodando
) else (
    echo ✗ Erro ao criar regra no firewall
    echo Tente executar manualmente:
    echo netsh advfirewall firewall add rule name="Liga YGO - Flask App" dir=in action=allow protocol=TCP localport=5000
)

echo.
pause