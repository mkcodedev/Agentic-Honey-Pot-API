Write-Host "Starting Agentic Honey-Pot Backend..."
Start-Process uvicorn -ArgumentList "main:app --host 0.0.0.0 --port 8000 --reload"

Write-Host "Waiting for backend to initialize..."
Start-Sleep -Seconds 5

Write-Host "Starting Agentic Honey-Pot Frontend..."
Start-Process streamlit -ArgumentList "run app.py"

Write-Host "Application started! Check the new windows."
