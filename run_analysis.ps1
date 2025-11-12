# Script de Análisis Automatizado del Proyecto
# Ejecuta múltiples herramientas de análisis de código

Write-Host "=== Análisis de Código - Agente Búsqueda ===" -ForegroundColor Green
Write-Host "Fecha: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Cyan
Write-Host ""

# Crear directorio de reportes
$reportsDir = "reports"
if (-not (Test-Path $reportsDir)) {
    New-Item -ItemType Directory -Force -Path $reportsDir | Out-Null
    Write-Host "Directorio de reportes creado: $reportsDir" -ForegroundColor Yellow
}

# Activar entorno virtual
$venvPath = ".\venv310\Scripts\Activate.ps1"
if (Test-Path $venvPath) {
    Write-Host "Activando entorno virtual..." -ForegroundColor Yellow
    & $venvPath
} else {
    Write-Host "ADVERTENCIA: No se encontró entorno virtual en $venvPath" -ForegroundColor Red
}

# 1. Estadísticas básicas del código
Write-Host "`n[1/7] Recopilando estadísticas del código..." -ForegroundColor Yellow
$pythonFiles = Get-ChildItem -Path agents,app,services,utils -Include *.py -Recurse
$totalFiles = $pythonFiles.Count
$totalLines = ($pythonFiles | Get-Content | Measure-Object -Line).Lines

Write-Host "  - Archivos Python: $totalFiles" -ForegroundColor Cyan
Write-Host "  - Líneas totales: $totalLines" -ForegroundColor Cyan

# Guardar estadísticas
@"
=== Estadísticas del Código ===
Fecha: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
Archivos Python: $totalFiles
Líneas totales: $totalLines
"@ | Out-File -FilePath "$reportsDir\stats.txt"

# 2. Ejecutar tests con pytest
Write-Host "`n[2/7] Ejecutando tests con pytest..." -ForegroundColor Yellow
try {
    python -m pytest tests/ --tb=short --maxfail=10 -v 2>&1 | Tee-Object -FilePath "$reportsDir\pytest.txt"
} catch {
    Write-Host "  ADVERTENCIA: Algunos tests fallaron. Ver $reportsDir\pytest.txt" -ForegroundColor Red
}

# 3. Cobertura de código
Write-Host "`n[3/7] Generando reporte de cobertura..." -ForegroundColor Yellow
try {
    python -m pytest tests/ --cov=agents --cov=app --cov=services --cov=utils `
           --cov-report=html:$reportsDir\coverage `
           --cov-report=term 2>&1 | Tee-Object -FilePath "$reportsDir\coverage.txt"
    Write-Host "  Reporte HTML generado en: $reportsDir\coverage\index.html" -ForegroundColor Green
} catch {
    Write-Host "  ERROR: No se pudo generar reporte de cobertura" -ForegroundColor Red
}

# 4. Instalar y ejecutar flake8 (si no está instalado)
Write-Host "`n[4/7] Análisis de estilo con flake8..." -ForegroundColor Yellow
try {
    python -m pip install flake8 -q
    python -m flake8 agents/ app/ services/ utils/ `
           --max-line-length=120 `
           --statistics `
           --output-file="$reportsDir\flake8.txt"
    Write-Host "  Reporte guardado en: $reportsDir\flake8.txt" -ForegroundColor Green
} catch {
    Write-Host "  ERROR: No se pudo ejecutar flake8" -ForegroundColor Red
}

# 5. Análisis de complejidad con radon
Write-Host "`n[5/7] Análisis de complejidad con radon..." -ForegroundColor Yellow
try {
    python -m pip install radon -q
    
    # Complejidad ciclomática
    python -m radon cc agents/ app/ services/ utils/ -a -s | Out-File -FilePath "$reportsDir\complexity.txt"
    
    # Índice de mantenibilidad
    python -m radon mi agents/ app/ services/ utils/ -s | Out-File -FilePath "$reportsDir\maintainability.txt"
    
    Write-Host "  Reportes guardados en: $reportsDir\complexity.txt y maintainability.txt" -ForegroundColor Green
} catch {
    Write-Host "  ERROR: No se pudo ejecutar radon" -ForegroundColor Red
}

# 6. Análisis de seguridad con bandit
Write-Host "`n[6/7] Análisis de seguridad con bandit..." -ForegroundColor Yellow
try {
    python -m pip install bandit -q
    python -m bandit -r agents/ app/ services/ utils/ `
           -f json -o "$reportsDir\bandit.json" 2>&1 | Out-Null
    python -m bandit -r agents/ app/ services/ utils/ -ll | Out-File -FilePath "$reportsDir\bandit.txt"
    Write-Host "  Reporte guardado en: $reportsDir\bandit.json" -ForegroundColor Green
} catch {
    Write-Host "  ERROR: No se pudo ejecutar bandit" -ForegroundColor Red
}

# 7. Verificar dependencias con safety
Write-Host "`n[7/7] Verificando vulnerabilidades en dependencias..." -ForegroundColor Yellow
try {
    python -m pip install safety -q
    python -m safety check --json --output "$reportsDir\safety.json" 2>&1 | Out-Null
    python -m safety check | Out-File -FilePath "$reportsDir\safety.txt"
    Write-Host "  Reporte guardado en: $reportsDir\safety.json" -ForegroundColor Green
} catch {
    Write-Host "  ADVERTENCIA: No se pudo ejecutar safety" -ForegroundColor Red
}

# Resumen final
Write-Host "`n=== Análisis Completado ===" -ForegroundColor Green
Write-Host "Todos los reportes están disponibles en: $reportsDir\" -ForegroundColor Cyan
Write-Host ""
Write-Host "Reportes generados:" -ForegroundColor Yellow
Write-Host "  - stats.txt          : Estadísticas del código" -ForegroundColor White
Write-Host "  - pytest.txt         : Resultados de tests" -ForegroundColor White
Write-Host "  - coverage/          : Cobertura de código (HTML)" -ForegroundColor White
Write-Host "  - flake8.txt         : Análisis de estilo" -ForegroundColor White
Write-Host "  - complexity.txt     : Complejidad ciclomática" -ForegroundColor White
Write-Host "  - maintainability.txt: Índice de mantenibilidad" -ForegroundColor White
Write-Host "  - bandit.json        : Análisis de seguridad" -ForegroundColor White
Write-Host "  - safety.json        : Vulnerabilidades en dependencias" -ForegroundColor White
Write-Host ""
Write-Host "Para ver el reporte de cobertura:" -ForegroundColor Cyan
Write-Host "  start $reportsDir\coverage\index.html" -ForegroundColor White
