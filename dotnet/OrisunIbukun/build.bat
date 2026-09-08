@echo off
echo ============================================
echo   ORISUN IBUKUN - Build Script
echo   C# / .NET WinForms Version
echo ============================================
echo.

where dotnet >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: .NET SDK not found.
    echo.
    echo Please install .NET 8.0 SDK from:
    echo https://dotnet.microsoft.com/download/dotnet/8.0
    echo.
    echo After installation, run this script again.
    pause
    exit /b 1
)

echo Restoring packages...
dotnet restore
if %errorlevel% neq 0 (
    echo.
    echo Restore failed.
    pause
    exit /b 1
)

echo.
echo Building application...
dotnet publish -c Release -r win-x64 --self-contained true -p:PublishSingleFile=true -p:IncludeNativeLibrariesForSelfExtract=true
if %errorlevel% neq 0 (
    echo.
    echo Build failed.
    pause
    exit /b 1
)

echo.
echo ============================================
echo   Build successful!
echo.
echo   Executable: bin\Release\net8.0-windows\win-x64\publish\OrisunIbukun.exe
echo ============================================
echo.
pause
