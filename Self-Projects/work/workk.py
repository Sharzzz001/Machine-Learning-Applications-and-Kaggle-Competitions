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
    [double] $script:totaltime = 0

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

    function Output-Stats {
        param($path, $files, $bytes, $seconds)

        $gb = [math]::Round($bytes / 1GB, 2)

        if ($FormatNumbers) {
            "{0,-60} {1,12:N0} files   {2,15:N0} bytes   {3,10:N2} GB   {4,10:N2} sec" -f $path, $files, $bytes, $gb, $seconds
        }
        else {
            "{0,-60} {1,12} files   {2,15} bytes   {3,10} GB   {4,10} sec" -f $path, $files, $bytes, $gb, $seconds
        }
    }

    function Get-DirectoryStats {
        param($directory, $recurse)

        Write-Progress -Activity "Calculating folder size" -Status $directory.FullName

        $sw = [System.Diagnostics.Stopwatch]::StartNew()

        $files = $directory | Get-ChildItem -Force -Recurse:$recurse -ErrorAction SilentlyContinue | Where-Object { -not $_.PSIsContainer }

        $sw.Stop()
        $elapsed = $sw.Elapsed.TotalSeconds
        $script:totaltime += $elapsed

        if ($files) {
            $measure = $files | Measure-Object -Sum -Property Length
            $count = $measure.Count
            $size = $measure.Sum
        }
        else {
            $count = 0
            $size = 0
        }

        $script:totalcount += $count
        $script:totalbytes += $size

        Output-Stats -path $directory.FullName -files $count -bytes $size -seconds $elapsed
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

    if (-not $directory) {
        Write-Error -Message "Path '$item' is not a directory in the file system." -Category InvalidType
        return
    }

    # First-level folder
    Get-DirectoryStats -directory $directory -recurse:$false

    if ($Only) { return }

    # Subfolders
    $directory | Get-ChildItem -Force -Recurse:$Every | Where-Object { $_.PSIsContainer } | ForEach-Object {
        Get-DirectoryStats -directory $_ -recurse:(!$Every)
    }
}

end {
    if ($Total) {
        $gb = [math]::Round($script:totalbytes / 1GB, 2)
        if ($FormatNumbers) {
            "`n{0,-60} {1,12:N0} files   {2,15:N0} bytes   {3,10:N2} GB   {4,10:N2} sec" -f "<Total>", $script:totalcount, $script:totalbytes, $gb, $script:totaltime
        }
        else {
            "`n{0,-60} {1,12} files   {2,15} bytes   {3,10} GB   {4,10} sec" -f "<Total>", $script:totalcount, $script:totalbytes, $gb, $script:totaltime
        }
    }
}
