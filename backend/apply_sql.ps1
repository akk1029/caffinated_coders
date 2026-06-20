# Apply SQL files in the correct order against the local database.
# Run from the backend/ directory:
#   .\apply_sql.ps1

$env:PGPASSWORD = "pantrypet123"
$psql = "psql"
$args_common = @("-U", "pantrypet", "-h", "localhost", "-d", "pantrypet")

Write-Host "1/3 Applying schema..." -ForegroundColor Cyan
& $psql @args_common -f "postgresql_schema.sql"
if (-not $?) { Write-Host "Schema failed — stopping." -ForegroundColor Red; exit 1 }

Write-Host "2/3 Applying shelf life seed..." -ForegroundColor Cyan
& $psql @args_common -f "sample_shelf_life_seed.sql"
if (-not $?) { Write-Host "Shelf life seed failed — stopping." -ForegroundColor Red; exit 1 }

Write-Host "3/3 Applying dummy data..." -ForegroundColor Cyan
& $psql @args_common -f "dummy_data.sql"
if (-not $?) { Write-Host "Dummy data failed — stopping." -ForegroundColor Red; exit 1 }

Write-Host "Done." -ForegroundColor Green