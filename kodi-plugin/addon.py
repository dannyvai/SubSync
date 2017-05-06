import xbmcaddon
import xbmcgui
import xbmc
import time
import os

finished = False

def pause_stream_if_not_finished():
    global finished
    if finished:
        pass
    else:
        xbmc.Player().pause()


addon       = xbmcaddon.Addon()
addonname   = addon.getAddonInfo('name')


xbmc.Player().onPlayBackResumed(pause_stream_if_not_finished)

isPlayingVideo  = xbmc.Player().isPlayingVideo()
if isPlayingVideo:

    #Pause the current playing file
    xbmc.Player().pause()
    for sub_stream in xbmc.Player().getAvailableSubtitleStreams():
        #xbmc.log(msg=sub_stream, level=xbmc.LOGINFO)
        os.system('echo "{}" >> /Users/dwainshtein/workspace/SubSync_git/output.txt'.format(sub_stream))
    playing_file = xbmc.Player().getPlayingFile()
    video_tag = xbmc.Player().getVideoInfoTag()
    title = video_tag.getTitle()
    episode = video_tag.getEpisode()
    is_movie = False
    if episode == -1:
        is_movie = True

    #get the name of the file
    if len(title) == 0:
        title = playing_file.split(os.sep)[-1].split('.')[0]

    pDialog = xbmcgui.DialogProgressBG()
    pDialog.create('SubSync', 'Finding the best subtitles, just chill')

    os.system('pwd >> /Users/dwainshtein/workspace/SubSync_git/output.txt'.format(sub_stream))
    cwd = os.getcwd()
    os.system('echo "{}" >> /Users/dwainshtein/workspace/SubSync_git/output.txt'.format(cwd))


    os.system('cd /Users/dwainshtein/workspace/SubSync_git/;/usr/local/bin/python2.7 parse_srt.py -f "{}" -d'.format(playing_file))
    #os.system('ping 8.8.8.8 -n 10')
    #print "Test"
    xbmc.Player().setSubtitles('/Users/dwainshtein/workspace/SubSync_git/test.srt')
    xbmcgui.Dialog().ok('SubSync',str(title),"Is movie ? : {}".format(is_movie),playing_file)
    pDialog.update(100,message="Found")
    xbmc.Player().pause()
