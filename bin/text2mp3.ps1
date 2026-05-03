param($volumn, $i, $o, $d, $s, $showvoices)

$inputfile = $i
$output = $o
$dict = $d
$srtfile = $s

if ($null -ne $showvoices -and $showvoices -ne "") {
    podman run `
        --rm -it `
        -v ${volumn}:/tmp/volumn:Z `
        sabotagecla6/text2mp3 `
        /bin/bash /usr/local/text2mp3/bin/edge-tts --list-voices | grep "${showvoices}"
    exit 0
}
else{
if ($null -eq $volumn -or $volumn -eq "") {
    $volumn = ".\"
}

if ($null -eq $srtfile -or $srtfile -eq "") {
    $srtfile = $output -replace "\.mp3$", ".srt"
}
if($null -ne $dict -or $dict -ne "") {
    $dict = "dict.yaml"
}

podman run `
    --rm -it `
    -v ${volumn}:/tmp/volumn:Z `
    sabotagecla6/text2mp3 `
    /bin/bash /usr/local/text2mp3/text2mp3.sh `
    -i "/tmp/volumn/${inputfile}" `
    -o "/tmp/volumn/${output}" `
    -d "/tmp/volumn/${dict}" `
    -s "/tmp/volumn/${srtfile}"
}
