param($volumn, $inputfile, $output, $dict, $srtfile)

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
