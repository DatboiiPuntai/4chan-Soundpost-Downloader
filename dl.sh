#!/bin/bash

# Default values for parameters
output_dir="./"
output_filename=""

# Function to display usage information
show_help() {
    echo "Usage: $0 [OPTIONS] <4chan_post_url>"
    echo "OPTIONS:"
    echo "  -o, --output-dir DIR    Specify the output directory (default: current directory)"
    echo "  -n, --output-filename    Specify the output filename (default: auto-generated)"
    echo "  -h, --help               Show this help message and exit"
    exit 1
}

# Function to parse command line arguments
parse_args() {
    while [ $# -gt 0 ]; do
        case "$1" in
        -o | --output-dir)
            output_dir="$2"
            shift 2
            ;;
        -n | --output-filename)
            output_filename="$2"
            shift 2
            ;;
        -h | --help)
            show_help
            ;;
        *)
            url="$1"
            shift
            ;;
        esac
    done
}

get_data() {
    local url="$1"
    thread_number=$(echo "$url" | sed -n 's/.*\/\([0-9]\+\)#[pP]\([0-9]\+\)/\1/p')
    post_number=$(echo "$url" | sed -n 's/.*\/\([0-9]\+\)#[pP]\([0-9]\+\)/\2/p')
    board=$(echo "$url" | sed -E 's|https://(boards\.)?4chan(nel)?\.org/([^/]+)/.*|\3|')

    local response=$(curl -s "https://a.4cdn.org/$board/thread/$thread_number.json")
    post_json=$(echo "$response" | jq ".posts[] | select(.no == $post_number)")
}

# Function to extract values from post_json
extract_post_data() {
    post_json="$1"

    tim=$(echo "$post_json" | jq -r '.tim')
    image_ext=$(echo "$post_json" | jq -r '.ext')
    image_url="https://i.4cdn.org/$board/$tim$image_ext"

    audio_ext=".$(echo "$post_json" | jq -r '.filename' | sed -n 's/.*\.\([^.]\+\)]/\1/p')"
    audio_url=$(
        echo "$post_json" | jq -r '.filename' |
            sed 's|%2F|/|g; s|%3A|:|g; s|%2E|.|g; s|%3F|?|g; s|%3D|=|g; s|%26|&|g; s|%25|%|g' |
            sed -n 's/.*\[sound=\(https:\/\/\)\{0,1\}\([^]]*\)\].*/\1\2/p' |
            sed -E 's|^https?://||; t; s|^http://||' |
            sed 's|^|https://|'
    )

    filename=$(echo "$post_json" | jq -r '.filename' | sed 's/\[sound=[^]]*\]//;s/[^[:alnum:]]/_/g;s/_\{2,\}/_/g')

    echo "post_filename: $(echo "$post_json" | jq -r '.filename')"
    echo "image_url: $image_url"
    echo "audio_url: $audio_url"
    echo "filename: $filename"
}

# Function to clean up temp dir
cleanup() {
    rm -rf "$temp_dir"
}
trap cleanup EXIT SIGINT

# Main function
main() {
    if [ $# -ge 1 ]; then
        url="$1"
        get_data $url

        extract_post_data "$post_json"

        temp_dir=$(mktemp -d)
        curl -# -o "$temp_dir/$filename$image_ext" "$image_url"
        curl -# -o "$temp_dir/$filename$audio_ext" "$audio_url"

        output_file="${2:-$filename.mp4}"
        output_path="$output_dir/$output_file"
        ffmpeg -loglevel warning -y -i "$temp_dir/$filename$image_ext" -i "$temp_dir/$filename$audio_ext" "$output_path"

    else
        show_help
        exit 1
    fi
}

# Call parse_args to process command line arguments
parse_args "$@"
# Call the main function with command line arguments
main "$@"