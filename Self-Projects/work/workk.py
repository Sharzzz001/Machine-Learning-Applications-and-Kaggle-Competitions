param(
    [string]$Path = "C:\Your\Folder\Path"
)

Get-ChildItem -Path $Path -Directory -Recurse | ForEach-Object {
    $folder = $_.FullName
    $size = (Get-ChildItem -Path $folder -Recurse -File -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum
    [PSCustomObject]@{
        Folder = $folder
        SizeGB = "{0:N2}" -f ($size / 1GB)
        SizeMB = "{0:N2}" -f ($size / 1MB)
    }
} | Sort-Object -Property SizeGB -Descending | Format-Table -AutoSize