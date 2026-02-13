text2mp3() {
    local opt optarg h m s

    # 引数を取る指定は - のみ
    while getopts viosd-: opt; do
        # OPTIND 番目の引数を optarg へ代入
        optarg="${!OPTIND}"
        [[ "$opt" = - ]] && opt="-$OPTARG"
        case "-$opt" in
            -v|--volumn)
                volumn="$optarg"
                shift
                ;;
            -i|--input)
                input="$optarg"
                shift
                ;;
            -o|--output)
                output="$optarg"
                shift
                ;;
            -s|--srt)
                srtfile="$optarg"
                shift
                ;;
            -d|--dict)
                dict="$optarg"
                shift
                ;;
            --)
                break
                ;;
            -\?)
                exit 1
                ;;
            --*)
                echo "$0: illegal option -- ${opt##-}" >&2
                exit 1
                ;;
        esac
    done
    shift $((OPTIND - 1))

    local message="$1"

    podman run \
        --userns=keep-id \
        --device /dev/snd \
        -e XDG_RUNTIME_DIR \
        -e PULSE_SERVER=unix:${XDG_RUNTIME_DIR}/pulse/native \
        -v ${XDG_RUNTIME_DIR}/pulse:${XDG_RUNTIME_DIR}/pulse:Z \
        -e DISPLAY --net=host -v $HOME/.Xauthority:/tmp/.Xauthority:Z \
        -v /tmp/.X11-unix/X0:/tmp/.X11-unix/X0:ro \
        -u $(id -u):$(id -u) \
        --rm -it \
        -v "$volumn":/tmp/volumn:Z \
        sabotagecla6/text2mp3 \
        /usr/local/text2mp3/text2mp3.sh \
        -i "/tmp/volumn/$input" \
        -o "/tmp/volumn/$output" \
        -d "/tmp/volumn/$dict" \
        -s "/tmp/volumn/$srtfile"
}

text2mp3 $@