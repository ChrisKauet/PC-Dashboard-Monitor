@echo off
:: Script para instalar o coletor como serviço Windows usando NSSM
:: Pré-requisito: Baixar nssm.exe de https://nssm.cc/download e colocar no PATH ou mesmo diretório

set SERVICE_NAME=PCSensorDash
set SERVICE_DISPLAY_NAME=PC Sensor Dashboard Collector
set SERVICE_DESCRIPTION=Coletor de métricas do PC para o Dashboard de Monitoramento
set APP_PATH=%~dp0server.py
set PYTHON_PATH=pythonw.exe  :: Usa pythonw para não mostrar janela de console

:: Verificar se o NSSM está disponível
where nssm >nul 2>&1
if errorlevel 1 (
    echo ERRO: NSSM não encontrado. Baixe de https://nssm.cc/download e adicione ao PATH.
    pause
    exit /b 1
)

:: Verificar se o arquivo server.py existe
if not exist "%APP_PATH%" (
    echo ERRO: Arquivo server.py não encontrado em %APP_PATH%
    pause
    exit /b 1
)

:: Instalar o serviço
nssm install %SERVICE_NAME% "%PYTHON_PATH%" "%APP_PATH%"

:: Configurar descrição
nssm set %SERVICE_NAME% DisplayName "%SERVICE_DISPLAY_NAME%"
nssm set %SERVICE_NAME% Description "%SERVICE_DESCRIPTION%"

:: Configurar para reiniciar em caso de falha
nssm set %SERVICE_NAME% AppRestartDelay 5000
nssm set %SERVICE_NAME% AppExit Default Exit:0 Restart:1

:: Definir diretório de trabalho
nssm set %SERVICE_NAME% AppDirectory "%~dp0"

:: Iniciar o serviço
nssm start %SERVICE_NAME%

echo.
echo Servico %SERVICE_NAME% instalado e iniciado com sucesso!
echo.
echo Para ver o status: nssm status %SERVICE_NAME%
echo Para parar: nssm stop %SERVICE_NAME%
echo Para remover: nssm remove %SERVICE_NAME% confirm
pause