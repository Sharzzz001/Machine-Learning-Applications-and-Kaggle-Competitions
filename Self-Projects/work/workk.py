# Get-DirStats.ps1
# Modified to output sizes in GB

param(
    [parameter(Position=0,Mandatory=$false,ParameterSetName="Path",ValueFromPipeline=$true)]
    $Path = (Get-Location).Path,

    [parameter(Position=0,Mandatory=$true,ParameterSetName="LiteralPath")]
    [String[]] $LiteralPath,

    [Switch] $Only,
    [Switch] $Every,
    [Switch] $FormatNumbers,
    [Switch] $Total
)

begin {
    $ParamSetName = $PSCmdlet.ParameterSetName
    if ( $ParamSetName -eq "Path" ) {
        $PipelineInput = (-not $PSBoundParameters.ContainsKey("Path")) -and (-not $Path)
    }
    elseif ( $ParamSetName -eq "LiteralPath" ) {
        $PipelineInput = $false
    }

    [UInt64] $script:totalcount = 0
    [UInt64] $script:totalbytes = 0

    function Get-Directory {
        param( $item )
        if ( $ParamSetName -eq "Path" ) {
            if ( Test-Path -Path $item -PathType Container ) {
                $item = Get-Item -Path $item -Force
            }
        }
        elseif ( $ParamSetName -eq "LiteralPath" ) {
            if ( Test-Path -LiteralPath $item -PathType Container ) {
                $item = Get-Item -LiteralPath $item -Force
            }
        }
        if ( $item -and ($item -is [System.IO.DirectoryInfo]) ) {
            return $item
        }
    }

    function Format-Output {
        process {
            $_ | Select-Object Path,
                @{Name="Files"; Expression={"{0:N0}" -f $_.Files}},
                @{Name="Size (Bytes)"; Expression={"{0:N0}" -f $_.Size}},
                @{Name="Size (GB)"; Expression={"{0:N2}" -f ($_.Size / 1GB)}}
        }
    }

    function Get-DirectoryStats {
        param( $directory, $recurse, $format )

        Write-Progress -Activity "Get-DirStats.ps1" -Status "Reading '$($directory.FullName)'"

        $files = $directory | Get-ChildItem -Force -Recurse:$recurse | Where-Object { -not $_.PSIsContainer }

        if ( $files ) {
            Write-Progress -Activity "Get-DirStats.ps1" -Status "Calculating '$($directory.FullName)'"

            $measure = $files | Measure-Object -Sum -Property Length

            $output = [PSCustomObject]@{
                Path   = $directory.FullName
                Files  = $measure.Count
                Size   = $measure.Sum
                SizeGB = [math]::Round($measure.Sum / 1GB, 2)
            }

            $script:totalcount += $measure.Count
            $script:totalbytes += $measure.Sum
        }
        else {
            $output = [PSCustomObject]@{
                Path   = $directory.FullName
                Files  = 0
                Size   = 0
                SizeGB = 0
            }
        }

        if (-not $format) { $output }
        else { $output | Format-Output }
    }
}

process {
    if ( $PipelineInput ) {
        $item = $_
    }
    else {
        if ( $ParamSetName -eq "Path" ) {
            $item = $Path
        }
        elseif ( $ParamSetName -eq "LiteralPath" ) {
            $item = $LiteralPath
        }
    }

    $directory = Get-Directory -item $item

    if ( -not $directory ) {
        Write-Error -Message "Path '$item' is not a directory in the file system." -Category InvalidType
        return
    }

    # First-level directory stats
    Get-DirectoryStats -directory $directory -recurse:$false -format:$FormatNumbers

    if ( $Only ) { return }

    # Subdirectories
    $directory | Get-ChildItem -Force -Recurse:$Every |
        Where-Object { $_.PSIsContainer } | ForEach-Object {
            Get-DirectoryStats -directory $_ -recurse:(-not $Every) -format:$FormatNumbers
        }
}

end {
    if ( $Total ) {
        $totalGB = [math]::Round($script:totalbytes / 1GB, 2)
        $output = [PSCustomObject]@{
            Path   = "<Total>"
            Files  = $script:totalcount
            Size   = $script:totalbytes
            SizeGB = $totalGB
        }
        if ( -not $FormatNumbers ) { $output }
        else { $output | Format-Output }
    }
}