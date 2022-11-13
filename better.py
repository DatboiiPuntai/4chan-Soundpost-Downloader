import requests
import json
import os
from urllib.parse import urlparse
from moviepy.editor import *
import re


def main():
    inputLink = input('Input your link')
    parsedUrl = urlparse(inputLink)
    board = parsedUrl.path.split('/')[1]

    json = get_json(parsedUrl)
    pair_dict = download_file(
        json['tim'], json['ext'], json['filename'], board)
    create_video(pair_dict)
    cleanup(pair_dict)


def get_json(url):
    '''
    Input: urlparse of soundpost link
    Ourput: JSON of the post
    '''
    postNo = int(url.fragment[1:])

    thread_json_raw = requests.get(f'https://a.4cdn.org/{url.path}.json')
    thread_json_object = json.loads(thread_json_raw.text)

    for post in thread_json_object['posts']:
        if post['no'] == postNo:
            return post


def download_file(image_id, extension, filename, board):
    image_link = f"https://i.4cdn.org/{board}/{image_id}{extension}"
    try:
        print('Downloading from: ' + image_link)
        response = requests.get(image_link)
    except:
        print('Error downloading')

    image_filename = filename + extension
    video_name = image_filename.split('[')[0].replace(' ', '')
    video_name = re.sub('[^A-Za-z0-9]+', '', video_name)
    open(f"{filename}{extension}", "wb").write(response.content)

    sound_file_link = (filename.split('sound=')
                       [-1][:-1]).replace('%2F', '/').replace('%3A', ':')
    if ('http') not in sound_file_link:
        sound_file_link = 'http://' + sound_file_link
    try:
        print('Downloading from: ' + sound_file_link)
        response = requests.get(sound_file_link)
    except:
        print('Error downloading audio')

    audio_filename = sound_file_link.split('/')[-1]
    open(sound_file_link.split('/')[-1], "wb").write(response.content)

    return {'image': image_filename, 'audio': audio_filename, 'video_name': video_name}

# combine all pairs into mp4 vids


def create_video(pair_dict):
    video_filetype = {'webm', 'mp4', 'gif'}

    filetype = pair_dict['image'].split('.')[-1]
    print(filetype)
    output_path = pair_dict['video_name'].split('.')[0]
    if filetype in video_filetype:
        # if video
        audio_clip = AudioFileClip(pair_dict['audio'])
        video_clip = VideoFileClip(
            pair_dict['image']).set_duration(audio_clip.duration)
        final_clip = video_clip.set_audio(audio_clip)
        final_clip.write_videofile(output_path+'.mp4')
    else:
        # if image
        audio_clip = AudioFileClip(pair_dict['audio'])
        image_clip = ImageClip(pair_dict['image']).set_duration(
            audio_clip.duration)
        final_clip = image_clip.set_audio(audio_clip)
        final_clip.fps = 1
        final_clip.write_videofile(output_path+'.mp4')

# delete the files


def cleanup(pair_dict):
    if os.path.exists(pair_dict['audio']):
        os.remove(pair_dict['audio'])
    if os.path.exists(pair_dict['image']):
        os.remove(pair_dict['image'])


if __name__ == '__main__':
    main()
