foreach ($nodePid in @(3736, 3956, 6920, 20872)) {
    Write-Output "==== Details for Node process ID $nodePid ===="
    Get-Process -Id $nodePid | Format-List *
    
    # Try to get module information
    Write-Output "==== Modules for Node process ID $nodePid ===="
    try {
        Get-Process -Id $nodePid -Module -ErrorAction SilentlyContinue | Select-Object -First 10
    } catch {
        Write-Output "Could not get modules: $_"
    }
    
    Write-Output "`n`n"
}

# Output to file
Out-File -FilePath C:\Users\Man\AppData\Local\Temp\node_processes_details.txt -Encoding utf8 -Force 