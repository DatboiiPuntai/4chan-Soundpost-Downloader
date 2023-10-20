import requests
import os
import sys
from urllib.parse import urlparse
from moviepy.editor import VideoFileClip, AudioFileClip, ImageClip
import re
from tqdm import tqdm

# Constants for file extensions
VIDEO_EXTENSIONS = ('.webm', '.mp4', '.gif')

def main():
    # Parse the 4chan post URL either from the command line or user input.
    input_link = sys.argv[1] if len(sys.argv) > 1 else input('Input your link: ')
    parsed_url = urlparse(input_link)
    board = parsed_url.path.split('/')[1]

    # Get the JSON data for the 4chan post.
    post = get_json(parsed_url)

    # Download image and audio files, create a video, and perform cleanup.
    file_info = download_files(post, board)
    create_video(file_info)
    cleanup(file_info)

def get_json(url):
    """
    Retrieve JSON data of a 4chan post from the specified URL.

    Args:
        url (str): Parsed URL of the 4chan post.

    Returns:
        dict: JSON data of the 4chan post or None in case of an error.
    """
    post_number = int(url.fragment[1:])
    print(f'https://a.4cdn.org/{url.path}.json')
    response = requests.get(f'https://a.4cdn.org/{url.path}.json')


    if response.status_code == 200:
        thread_json = response.json()
        # Find and return the post with the specified post number.
        return next((post for post in thread_json['posts'] if post['no'] == post_number), None)
    else:
        print(f"Failed to retrieve JSON data from {url}. HTTP Status Code: {response.status_code}")
        return None


def download_files(post, board):
    """
    Download image and audio files associated with a 4chan post.

    Args:
        post (dict): JSON data of the 4chan post.
        board (str): The name of the 4chan board.

    Returns:
        dict: Dictionary containing the image, audio, and video names.
    """
    image_url = f"https://i.4cdn.org/{board}/{post['tim']}{post['ext']}"
    audio_filename_match = re.search(r'sound=([^&]+)', post['filename'])
    audio_filename = audio_filename_match.group(1).replace('%2F', '/').replace('%3A', ':').rstrip(']')
    audio_url = f"http://{audio_filename}" if 'http' not in audio_filename else audio_filename

    try:
        download_file(image_url, post['filename'] + post['ext'])
        download_file(audio_url, os.path.basename(audio_filename))
    except Exception as e:
        print(f"An error occurred while downloading files: {e}")

    return {
        'image_file': post['filename'] + post['ext'],
        'audio_file': os.path.basename(audio_filename),
        'video_name': re.sub(r'[^\w]+', '', post['filename'].split('[')[0].replace(' ', ''))
    }

def download_file(url, filename):
    """
    Download a file from the specified URL and save it with the given filename.

    Args:
        url (str): URL of the file to download.
        filename (str): Name for the downloaded file.

    Returns:
        None
    """
    print(f'Downloading from: {url}')

    try:
        # Send a GET request to the URL and stream the response
        response = requests.get(url, stream=True)

        # Check if the request was successful
        if response.status_code == 200:
            total_size = int(response.headers.get('content-length', 0))
            block_size = 1024  # 1 KB

            with open(filename, 'wb') as file, tqdm(
                desc=filename, total=total_size, unit='B', unit_scale=True, unit_divisor=1024
            ) as bar:
                for data in response.iter_content(block_size):
                    file.write(data)
                    bar.update(len(data))
        else:
            print(f"Failed to download from {url}. HTTP Status Code: {response.status_code}")
    except Exception as e:
        print(f"An error occurred while downloading the file {filename}: {e}")

def create_video(file_info):
    """
    Create a video by combining the downloaded image and audio files.

    Args:
        file_info (dict): Dictionary containing file names.

    Returns:
        None
    """
    image_file = file_info['image_file']
    audio_file = file_info['audio_file']
    audio_clip = AudioFileClip(audio_file)
    video_name = file_info['video_name'].split('.')[0]

    if image_file.split('.')[-1] in VIDEO_EXTENSIONS:
        video_clip = VideoFileClip(image_file).set_duration(audio_clip.duration)
        final_clip = video_clip.set_audio(audio_clip)
    else:
        image_clip = ImageClip(image_file).set_duration(audio_clip.duration)
        final_clip = image_clip.set_audio(audio_clip)
        final_clip.fps = 1

    final_clip.write_videofile(video_name + '.mp4')

def cleanup(file_info):
    """
    Remove the downloaded temporary files.

    Args:
        file_info (dict): Dictionary containing file names.

    Returns:
        None
    """
    for filename in file_info.values():
        if os.path.exists(filename):
            try:
                os.remove(filename)
                print(f"File {filename} removed successfully.")
            except OSError as e:
                print(f"Error deleting {filename}: {e}")
        else:
            print(f"File {filename} not found. Skipping deletion.")

if __name__ == '__main__':
    main()
