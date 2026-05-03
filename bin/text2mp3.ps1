param($v, $i, $o, $d, [switch]$l)

if ($l) {
    podman run --rm -it sabotagecla6/text2mp3 /bin/bash /usr/local/text2mp3/text2mp3.sh edge-tts --list-voices
    exit 0
}

# 
$infile = $((Get-Item $i).BaseName)
$outfile = $o

# 作業用フォルダの作成
$chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
$randomString = -join ((1..12) | ForEach-Object { $chars[(Get-Random -Maximum $chars.Length)] })
$tempdir="$($PSScriptRoot)\..\tmp\${randomString}"
mkdir $tempdir
$tempdir = Resolve-Path $tempdir

if ($null -eq $volumn -or $volumn -eq "") {
    $volumn = Resolve-Path "./"
}

Copy-Item -Path $i -Destination "${tempdir}\infile.yaml"
if($null -ne $d -and $d -ne ""){
    Copy-Item -Path $d -Destination "${tempdir}\dictfile.yaml"
}
if (Test-Path "$($PSScriptRoot)\..\config\global-dict.yaml"){
    Copy-Item -Path "$($PSScriptRoot)\..\config\global-dict.yaml" -Destination "${tempdir}\global-dict.yaml"
}
if ( $null -eq "$outfile" -or "$outfile" -eq ""){
    $outfile="/tmp/volumn/${infile}.mp3"
}

$args_str=""
if ( $null -ne "$outfile" -and "$outfile" -ne ""){
    $args_str="${args_str} -o /tmp/volumn/${infile}.mp3"
}
if($null -ne $d -and $d -ne ""){
    $args_str="${args_str} -d /tmp/data/dictfile.yaml"
}
if (Test-Path "${tempdir}\global-dict.yaml"){
    $args_str="${args_str} -g /tmp/data/global-dict.yaml"
}

podman run --rm -it `
    -v "${volumn}:/tmp/volumn:Z" `
    -v "${tempdir}:/tmp/data/" `
    sabotagecla6/text2mp3 `
    /bin/bash /usr/local/text2mp3/text2mp3.sh python3 main.py `
    -i "/tmp/data/infile.yaml" ${args_str}

Remove-Item -Force -Recurse $tempdir
