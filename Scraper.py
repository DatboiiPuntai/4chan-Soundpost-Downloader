import requests
import json
import shutil
import os
from IPython.display import clear_output
from moviepy.editor import *

def main():
    folder_path = r"C:\Users\panta\Downloads"

    board = input("What is the board you would like to search? ")
                
    thread_dict_list = get_threads(board)
    for thread_dict in thread_dict_list:
        print(thread_dict['subject'])
        
    search_query = input("Which thread would you like to search? ")
    clear_output()

    thread_json_object = find_thread(search_query,thread_dict_list)

    soundpost_dict_list = find_soundposts_in_thread(thread_json_object)

    if len(soundpost_dict_list) != 0:
        print('Here are all the soundposts')
        for soundpost_dict in soundpost_dict_list:
            print(soundpost_dict['filename'])

        if input('Would you like to download them all? (y/n) ').lower() == 'y':
            for soundpost_dict in soundpost_dict_list:
                download_file(soundpost_dict['image_id'], soundpost_dict['extension'], soundpost_dict['filename'])
        else:
            print('ogey buddy')

        if input('Would you like to merge files? (y/n) ').lower() == 'y':
            pair_dict_list = match_files(folder_path)
            create_video(folder_path, pair_dict_list)
        else:
            print('ogey buddy')

        if input('Would you like to delete original files? (y/n) ').lower() == 'y':
            cleanup(pair_dict_list)
        else:
            print('ogey buddy')
    else:
        print('There are no soundposts in this thread.')

def get_threads(board):
    json_raw = requests.get(f'https://a.4cdn.org/{board}/catalog.json')
    json_object = json.loads(json_raw.text) 

    thread_dict_list = []
    for page in json_object:
        for thread in page['threads']:
            if 'sub' in thread:
                thread_dict_list.append({'subject': thread['sub'], 'number': thread['no']})
    return thread_dict_list

def find_thread(search_query, thread_dict_list):
    for thread_dict in thread_dict_list:
        if search_query.lower() in thread_dict['subject'].lower():
            matched_thread_number = thread_dict['number']
            break
    thread_json_raw = requests.get(f'https://a.4cdn.org/{board}/thread/{matched_thread_number}.json')
    thread_json_object = json.loads(thread_json_raw.text)
    return thread_json_object

def find_soundposts_in_thread(thread_json_object):
    soundpost_dict_list = []
    for post in thread_json_object['posts']:
        if 'filename' in post:
            if '[sound=' in post["filename"]:
                soundpost_dict_list.append({'filename': post['filename'], 
                                            'image_id': post['tim'], 'extension': post['ext']})
    return soundpost_dict_list

def download_file(image_id,extension,filename):
    image_link = f"https://i.4cdn.org/{board}/{image_id}{extension}"
    try:
        print('Downloading from: ' + image_link)
        response = requests.get(image_link)
    except:
        print('Error downloading')

    open(f"{filename}{extension}", "wb").write(response.content)
    shutil.move(f"D://Programming//My Scripts//Scraper//{filename}{extension}", 
                f"C://Users//panta//Downloads//{filename}{extension}")

    
    sound_file_link = (filename.split('sound=')[-1][:-1]).replace('%2F','/').replace('%3A',':')
    if('http') not in sound_file_link:
        sound_file_link = 'http://'+ sound_file_link
    try:
        print('Downloading from: ' + sound_file_link)
        response = requests.get(sound_file_link)
    except:
        print('Error downloading audio')

    open(sound_file_link.split('/')[-1], "wb").write(response.content)
    shutil.move(f"D://Programming//My Scripts//Scraper//{sound_file_link.split('/')[-1]}", 
                f"C://Users//panta//Downloads//{sound_file_link.split('/')[-1]}")



# find matching audio and visual file in folder
def match_files(folder_path):
    file_list = os.listdir(folder_path)
    pair_dict_list = []

    for file in file_list:
        if 'sound=' in os.path.basename(file) and os.path.splitext(file)[-1] in video_file_types.union(image_file_types):
            visual_clip = os.path.basename(file)
            visual_clip_path = os.path.join(folder_path,visual_clip)

            # finds matching audio
            audio_clip = visual_clip.split(']')[0].split('%2F')[-1]
            audio_clip_path = os.path.join(folder_path,audio_clip)

            video_name = visual_clip.split('[')[0].replace(' ','')

            isVideo = visual_clip.split('.')[-1] in video_file_types
            pair_dict_list.append({'audio_clip':audio_clip_path, 'visual_clip':visual_clip_path, 
                                   'video_name':video_name, 'isVideo':isVideo})
            visual_clip = None

    return pair_dict_list

# combine all pairs into mp4 vids
def create_video(folder_path, pair_dict_list):
    for pair in pair_dict_list:
        try:
            output_path = os.path.join(folder_path,pair['video_name'].split('.')[0])
            if pair['isVideo']:
                # if video
                audio = AudioFileClip(pair['audio_clip'])
                clip = VideoFileClip(pair['visual_clip'])
                clip = clip.set_audio(audio)
                clip.write_videofile(output_path+'.mp4')
                clip.close()
            else:
                # if image
                audio = AudioFileClip(pair['audio_clip'])
                clip = ImageClip(pair['visual_clip']).set_duration(audio.duration)
                clip = clip.set_audio(audio)
                clip.write_videofile(output_path+'.mp4', fps=1)
                clip.close()
        except:
            print('Error merging ' + pair['video_name'])
            del pair
            clip.close()

# delete the files
def cleanup(pair_dict_list):
    for pair in pair_dict_list:
        if os.path.exists(pair['audio_clip']):
            os.remove(pair['audio_clip'])
        if os.path.exists(pair['visual_clip']):
            os.remove(pair['visual_clip'])

if __name__ == '__main__':
    main()