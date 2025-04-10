@echo off
set PYTHON_EXE=py

:: Verifica se o Python está instalado
%PYTHON_EXE% --version >nul 2>&1
IF ERRORLEVEL 1 (
    echo Python não encontrado. Instalando...
    start /wait python-3.13.1-amd64.exe /quiet InstallAllUsers=1 PrependPath=1
)

:: Garante que PATH foi atualizado
where %PYTHON_EXE% >nul 2>&1
IF ERRORLEVEL 1 (
    echo Erro: Python ainda não está disponível no PATH.
    pause
    exit /b
)

:: Cria ambiente virtual se não existir
if not exist "venv" (
    echo Criando ambiente virtual...
    %PYTHON_EXE% -m venv venv
)

:: Verifica se a ativação é possível
if exist "venv\Scripts\activate.bat" (
    echo Ativando ambiente virtual...
    call venv\Scripts\activate
) else (
    echo Erro: Ambiente virtual não foi criado corretamente.
    pause
    exit /b
)

:: Define caminhos do venv
set PYTHON_EXE=venv\Scripts\python
set PIP_EXE=venv\Scripts\pip

:: Instala bibliotecas
echo Instalando bibliotecas...
%PIP_EXE% --version | findstr "24.3.1"
IF ERRORLEVEL 1 (
    echo Atualizando pip...
    %PIP_EXE% install --upgrade pip
)

%PIP_EXE% install -r requirements.txt

:: Roda seu script
echo Iniciando script...
start chrome http://localhost:5000
%PYTHON_EXE% app.py

:: Mantém terminal aberto
pause
