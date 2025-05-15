# PowerShell Script to push ONLY the Excel progress report to the main branch

# ---- CONFIG ----
$repoUrl = "https://github.com/Jayshil-Singh/CS415_A3.git"
$tempDir = "$env:TEMP\cs415-report-temp"
$excelFilePath = "C:\Users\avichal avneel nath\Documents\Semester 7\CS415\A3\CS415_A3\PR&IR.xlsx"
$excelFileName = "PR&IR.xlsx"
# ----------------

# Step 1: Remove temp directory if it exists
if (Test-Path $tempDir) {
    Remove-Item -Recurse -Force $tempDir
}

# Step 2: Clone only the main branch into the temp directory
git clone -b main $repoUrl $tempDir

# Step 3: Copy the Excel file into the new clone
Copy-Item -Path $excelFilePath -Destination "$tempDir\$excelFileName"

# Step 4: Change to temp repo directory
Set-Location $tempDir

# Step 5: Git add, commit, and push just the Excel file
git add "$excelFileName"
git commit -m "Updated progress report for May 14 Wed by Avichal"
git push origin main

# Step 6: Done, optional cleanup message
Write-Host "`n✅ Report pushed to 'main' successfully from avichal-dev without affecting current branch."

#.\push-excel-report.ps1 