import sys
import pysrt
import os
import argparse

import subprocess
import json

import numpy as np

import threading
import re
import time

from keys import *

def is_common_word(word):
    return word in ('i','you','are','is','the','a','%HESITATION')

def fix_srt(srt_path,start_t,end_t):

    srt = pysrt.open(srt_path)
    for i in range(0,len(srt)):
        #print srt[i].start
        seconds_to_srt_time(srt[i].start,start_t[i])
        seconds_to_srt_time(srt[i].end,end_t[i])

    #srt.save(srt_path+".fixed.srt", encoding='utf-8')
    srt.save("test.srt", encoding='utf-8')

def calculate_subtitle_shift(
    sample_times,
    sample_duration,
    min_words,
    shift_wanted,
    diff_segments,
    start_t,
    end_t,
    first_sentance_words
):

    diff_mean_vec = []
    diff_time_vec = []
    num_segments = len(sample_times)

    for seg_idx in range(0,num_segments):
        if not diff_segments[seg_idx].size <  min_words:
            diff_mean_vec.append(np.mean(diff_segments[seg_idx]))
            diff_time_vec.append(sample_times[seg_idx] + sample_duration/2.)
        else:
            print "diff_segments[seg_idx].size <  min_words"

    for i in range (0,len(start_t)):
        ts = start_t[i]
        te = end_t[i]
        if ts < diff_time_vec[0]:
            shift = diff_mean_vec[0] - shift_wanted
        elif ts > diff_time_vec[-1]:
            shift = diff_mean_vec[-1] - shift_wanted
        else:
            shift = np.interp(ts,diff_time_vec,diff_mean_vec) - shift_wanted

        start_t[i] += shift
        end_t[i] += shift


def compare_words(
    sample_times,
    sample_duration,
    video_path,
    output_template,
    search_win,
    start_t,
    first_sentance_words,
    min_words,
    max_dist
):

    video_name = get_video_name_from_path(video_path)
    num_segments = len(sample_times)
    diff_segments = []

    for seg_idx in range(0,num_segments):
        start_time = sample_times[seg_idx]

        extracted_text_output_json_filename = output_template.format(
                video_name,sample_duration,seg_idx,num_segments)

        result = json.loads(open(extracted_text_output_json_filename,'r').read())
        if 'results' not in result.keys():
            #TODO should be NaN
            print("Should be NaN :: 'results' not in result.keys():")
            diff_segments.append(np.array(0))
            continue

        t_ws_vid_vec = []
        t_ws_srt_vec = []
        match_words = []

        for res in result['results']:
            for sample in res['alternatives'][0]['timestamps']:
                word,word_start_sample,word_end_sample = sample
                word = word.strip().lower()

                if is_common_word(word):
                    continue

                if len(word) == 0:
                    continue

                time_word_start = start_time + word_start_sample
                time_min = time_word_start - search_win
                time_max = time_word_start + search_win
                #print time_min,time_max
                min_idx = np.where(start_t > time_min)
                max_idx = np.where(start_t < time_max)
                intersection = np.intersect1d(min_idx,max_idx)
                #print intersection

                for word_idx in intersection:
                    word_srt = first_sentance_words[word_idx]
                    #print word_srt,word,word_srt == word
                    if word_srt == word:
                        t_ws_vid_vec.append(time_word_start)
                        t_ws_srt_vec.append(start_t[word_idx])
                        match_words.append(word)

        if len(match_words) == 0:
            #TODO should be NaN
            print("Should be NaN :: len(match_words) == 0")
            diff_segments.append(np.array(0))
        elif len(match_words) < min_words:
            #TODO should be NaN
            print("Should be NaN :: len(match_words) < min_words")
            diff_segments.append(np.array(0))
        else:
            diff_temp = np.array(t_ws_vid_vec).astype('float') - np.array(t_ws_srt_vec).astype('float')
            diff_m = np.median(diff_temp)
            dist = diff_temp - diff_m
            i_ok = np.where(np.abs(dist) < max_dist)
            diff_temp = diff_temp[i_ok]
            if diff_temp.size  < min_words :
                #TODO should be NaN
                print("Should be NaN :: i_ok[0].size  < min_words")
                diff_segments.append(np.array(0))
            else :
                diff_segments.append(diff_temp)

    return diff_segments



def remove_non_ascii(text):
    return "".join(i for i in text if ord(i)<128)

def decode_utf8_bom(srt_fname):
    fp = open(srt_fname,'rw')
    content_raw = remove_non_ascii(fp.read())
    fp.close()

    content_utf8bom = content_raw.decode('utf-8')
    content_ascii = content_utf8bom.encode('ascii')

    fp = open(srt_fname,'w')
    fp.write(content_ascii)
    fp.close()


def srt_time_to_seconds(srt_time):
    return srt_time.hours*3600 + srt_time.minutes*60 + srt_time.seconds + srt_time.milliseconds/1000.0

def seconds_to_srt_time(srt_time,sec):

    hours = int(sec/3600.)
    minutes = int((sec%3600)/60.)
    seconds = int(sec%60)
    milliseconds = int(sec%1*1000)
    #print sec,hours,minutes,seconds,milliseconds

    srt_time.hours = hours
    srt_time.minutes = minutes
    srt_time.seconds = seconds
    srt_time.milliseconds = milliseconds

def read_srt(srt_fname):
    start_t = []
    end_t = []
    first_sentance_words = []

    decode_utf8_bom(srt_fname)

    srt = pysrt.open(srt_fname)
    for line in srt:
        start_t.append(srt_time_to_seconds(line.start))
        end_t.append(srt_time_to_seconds(line.end))
        word = line.text.split()[0].lower()
        word = re.sub('[,\.><!\?]','',word)
        #TODO check if common word and take the other one?
        first_sentance_words.append(word)

    return start_t,end_t,first_sentance_words

def extract_text_from_video_segment(start_time,sample_duration,video_path,extracted_text_output_json_filename):

    audio_sample_filename = "seg_{}_of_{}.ogg".format(int(start_time),int(start_time+sample_duration))

    temp_script_name = '/tmp/{}_{}.sh'.format(start_time,(start_time+sample_duration))
    temp_script = open(temp_script_name,'w')
    sample_audio_cmd = '/usr/local/bin/ffmpeg -i "{}" -ss {} -t {} -vn -acodec libvorbis -y {}'.format(video_path,start_time,sample_duration,audio_sample_filename)
    #os.system(sample_audio_cmd)
    tts_cmd = '/usr/bin/curl -X POST -u {}:{} --header "Content-Type: audio/ogg;codecs=vorbis" --header "Transfer-Encoding: chunked" --data-binary @{} "https://stream.watsonplatform.net/speech-to-text/api/v1/recognize?continuous=true&timestamps=true&max_alternatives=1"  > "{}_temp" '.format(IBM_USER,IBM_PASSWORD,audio_sample_filename,extracted_text_output_json_filename)
    #os.system(tts_cmd)

    print sample_audio_cmd
    print tts_cmd

    print >> temp_script , sample_audio_cmd
    print >> temp_script , tts_cmd
    print >> temp_script , 'mv "{}_temp" "{}"'.format(extracted_text_output_json_filename,extracted_text_output_json_filename)
    temp_script.close()
    os.system('bash {} &'.format(temp_script_name))

def extract_text_from_video(sample_times,sample_duration,video_path,output_template):

    threads = []
    video_name = get_video_name_from_path(video_path)
    output_names = []
    for seg_idx in range(0,len(sample_times)):

        start_time = sample_times[seg_idx]

        extracted_text_output_json_filename = output_template.format(
                video_name,sample_duration,seg_idx,len(sample_times))

        if not os.path.exists(extracted_text_output_json_filename):
            #t = threading.Thread(target=extract_text_from_video_segment,args=(start_time,sample_duration,video_path,extracted_text_output_json_filename,))
            #threads.append(t)
            #t.start()
            extract_text_from_video_segment(start_time,sample_duration,video_path,extracted_text_output_json_filename)
            output_names.append(extracted_text_output_json_filename)
    #for thread in threads:
    #   threads.join()
    all_outputs_exist = False
    while not all_outputs_exist:
        all_outputs_exist = True
        for name in output_names:
            if not os.path.exists(name):
                all_outputs_exist = False
                break
        time.sleep(5)

    print "All threads finished"


def get_video_duration(video_path):

    command = [
        "/usr/local/bin/ffprobe",
        "-loglevel",  "quiet",
        "-print_format", "json",
        "-show_format",
        video_path
     ]

    pipe = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out, err = pipe.communicate()
    output = json.loads(out)
    return float(output['format']['duration'])

def find_srt_file(video_name,where='.'):

    files = os.listdir(where)

    srt_fname = None
    for fname in files:
        not_my_file = False
        if ".srt" in fname:
            for word in video_name.lower().split():
                if word not in fname.lower():
                    not_my_file = True
                    break
            if not not_my_file:
                srt_fname = fname
                break
    if srt_fname is None:
        return None
    return os.path.join(where,srt_fname)

def download_subtitles(video_name,where='.'):
    os.system('python SubsceneDL.py -d {} -m {}'.format(where,video_name))

def get_video_name_from_path(video_path):
    return video_path.split(os.path.sep)[-1].split('.')[0]

def main():

    credits_length = 30; #Seconds
    intro_length = 30; #Seconds
    sample_duration = 60; #Seconds
    win = 5;  #Seconds
    num_of_seg = 15;
    max_dist = 0.3; #Seconds
    min_words = 4;
    shift_wanted = 0.1; #Seconds


    parser = argparse.ArgumentParser(description='SubSync')

    parser.add_argument('-f','--filename',help='filename path',default='')
    parser.add_argument('-od','--dir',help='output dir',default='.')
    parser.add_argument('-d','--download',dest='download',help='download subtitles',action='store_true')
    parser.add_argument('-nd','--no-download',dest='download',help='Dont download subtitles',action='store_false')
    parser.add_argument('-s','--subtitle',help='subtitle file',default='')
    args = parser.parse_args()



    video_path = args.filename

    video_name = get_video_name_from_path(args.filename)
    print ("Video name is : {} ".format(video_name))
    output_dir = args.dir


    if args.download or args.subtitle == '':
        srt_file = find_srt_file(video_name,output_dir)
        if srt_file is None:
            download_subtitles(video_name,output_dir)
            srt_file = find_srt_file(video_name,output_dir)
    else:
        srt_file = args.subtitle

    if srt_file is not None:
        print("Found srt:",srt_file)
    else:
        print("no subtitles where found :{")
        sys.exit(-1)

    video_duration = get_video_duration(video_path)
    print("Video duration : {}".format(video_duration))

    sampled_duration = video_duration - credits_length - intro_length
    sample_times = np.floor(np.linspace(intro_length,video_duration-sample_duration,num_of_seg))
    print("Time samples:",sample_times)

    start_t,end_t,first_sentance_words = read_srt(srt_file)

    tts_output_template = '{}_dur_{}_seg_{}_of_{}.json'
    extract_text_from_video(sample_times,sample_duration,video_path,tts_output_template)

    diff_segments = compare_words(sample_times,sample_duration,video_path,tts_output_template,win,start_t,first_sentance_words,min_words,max_dist)

    #rint start_t
    #print end_t
    calculate_subtitle_shift(sample_times,sample_duration,min_words,shift_wanted,diff_segments,start_t,end_t,first_sentance_words)
    #print start_t
    #print end_t

    fix_srt(srt_file,start_t,end_t)

if __name__ == "__main__":
    main()
