
#################################################
### THIS FILE WAS AUTOGENERATED! DO NOT EDIT! ###
#################################################
# file to edit: ./nb/main.ipynb

import sys
if __name__ == '__main__': sys.path.append('..')
import download_youtube_subtitle.common as common
from pprint import pprint
def pj(*args, **kargs):
    if common.IN_JUPYTER:
        pprint(*args, **kargs)

from functools import partial
import sys

perr = partial(print, "ERR: ")

import requests
import socket
socket.setdefaulttimeout(5.)

# dealing with xml.dom
import re
def getVal(dom, key):
    att = dom.attributes[key]
    return att.value

def eachTxt(txt, remove_font_tag):
    start = getVal(txt, 'start')
    dur = getVal(txt, 'dur')
    if txt.firstChild is None:
        # fix dl-youtube-cc.exe Zd14s2WW-Tc --caption_num=1
        txt = ""
    else :
        txt = html.unescape((txt.firstChild.data))
        if remove_font_tag:
            txt =   re.sub(r'</?font[^>]*>','', txt)
    return {
        "start":start,
        "dur": dur,
        "text": txt
    }

# todo
# add tlang=zh-Hans to baseUrl
# will get translation

# getting track info

def get_data(link):
    data = requests.get(link)
    data = data.text
    return data

import re
import json
import urllib
def get_tracks_title(data):
    decodedData = urllib.parse.unquote(data)
    if 'captionTracks' not in decodedData:
        perr("no caption available. ;(")
        exit(1)
    match = re.search(r'({"captionTracks":.*isTranslatable":(true|false)}])', decodedData)
    match = match.group(1)
    match = f"{match}}}"
    captionTracks =  json.loads(match)['captionTracks']
    match = re.search(r'title":"(.*?)","lengthSeconds":', decodedData)
    title = match.group(1)
    return captionTracks, title

# dealing with transcript
import math
from functools import partial
import sys
from xml.dom.minidom import parseString
import html
def parseTranscript(transcript, remove_font_tag=True):
    try:
        dom = parseString(transcript.text)
    except :
        perr("check your lang code")
        perr("server response")
        perr(transcript.text)
        exit(1)
    texts = dom.getElementsByTagName('text')

    _eachTxt = partial(eachTxt, remove_font_tag=remove_font_tag)
    texts = list(map( _eachTxt, texts,))
    return texts

def each_sent(o, file=sys.stdout):
    start = o['start']
    start = float(start)
    minute = math.floor(start/60)
    second = math.floor(start%60)
    p = partial(print, file=file)
    p(f"---------{minute:02d}:{second:02d}----------")
    p(o['text'])
    translate_text = o.get('translate_text', None)
    if translate_text:
        p(translate_text)


# dealing with valid filename
# https://github.com/django/django/blob/master/django/utils/text.py
import re
def get_valid_filename(s):
    """
    Return the given string converted to a string that can be used for a clean
    filename. Remove leading and trailing spaces; convert other spaces to
    underscores; and remove anything that is not an alphanumeric, dash,
    underscore, or dot.
    >>> get_valid_filename("john's portrait in 2004.jpg")
    'johns_portrait_in_2004.jpg'
    """
    s = str(s).strip().replace(' ', '_')
    return re.sub(r'(?u)[^-\w.]', '', s)

import copy
def merge_subtitle(subtitle, subtitle_cn):
    """
    merge subtitle_cn(traslation) to subtitle(origin).
    cc and translated cc aren't always align,
    I found at least in cn and ja, translated cc are less than cc
    see  videoID='HSz7Q4YnQ_M'
    cc and translated cc aren't always equal in time see 5tKOV0KqPlg for translation ja
    """
    subtitle = copy.deepcopy(subtitle) # original transcript
    subtitle_cn = copy.deepcopy(subtitle_cn) # translation script

    TRANSLATE_TEXT="translate_text"
    TEXT="text"
    START="start"

    # NOTE not sure how to merge them properly

    # indexer for subtitle
    sub_p = 0
    sub_p_cn = 0

    while sub_p < len(subtitle) and sub_p_cn < len(subtitle_cn):

        sub = subtitle[sub_p]
        sub_cn = subtitle_cn[sub_p_cn]

        if TRANSLATE_TEXT not in sub: sub[TRANSLATE_TEXT] = ""

        if float(sub[START]) >= float(sub_cn[START]) :
        # sub goes first, being chased by sub_cn

            # for separating the sentence
            if len(sub[TRANSLATE_TEXT]) != 0: sub[TRANSLATE_TEXT] += "\n"

            sub[TRANSLATE_TEXT] +=  sub_cn[TEXT]

            sub_p_cn += 1

        else :
            sub_p += 1

    # add empty field for subitle
    while sub_p < len(subtitle):
        assert sub_p_cn == len(subtitle_cn)

        sub = subtitle[sub_p]
        if TRANSLATE_TEXT not in sub: sub[TRANSLATE_TEXT] = ""
        sub_p += 1

    # add the rest of subtitle_cn to the last one of subtitle
    while sub_p_cn < len(subtitle_cn):
        assert sub_p == len(subtitle)

        sub = subtitle[-1]

        if TRANSLATE_TEXT not in sub: sub[TRANSLATE_TEXT] = ""

        if len(sub[TRANSLATE_TEXT]) != 0: sub[TRANSLATE_TEXT] += "\n"

        sub[TRANSLATE_TEXT] += sub_cn[TEXT]
        sub_p_cn += 1

    assert sub_p == len(subtitle)
    assert sub_p_cn == len(subtitle_cn)

    return subtitle

#here to break up the procss
# videoID="Zd14s2WW-Tc"
videoID="5tKOV0KqPlg"
data_link=f"https://youtube.com/get_video_info?video_id={videoID}"
data=get_data(data_link)
captionTracks, title = get_tracks_title(data)
baseUrl = captionTracks[0]['baseUrl']
transcript = requests.get(baseUrl)
subtitle = parseTranscript(transcript)
# baseUrl = captionTracks[0]['baseUrl'] + '&tlang=zh-Hans'
baseUrl = captionTracks[0]['baseUrl'] + '&tlang=ja'
transcript = requests.get(baseUrl)
subtitle_cn = parseTranscript(transcript)
merged_subtitle = merge_subtitle(subtitle, subtitle_cn)

def format_caption(caption):
    ret = f"{caption['vssId']:8s} {caption['name']['simpleText']}"
    if 'a.' in caption['vssId']:
        ret += ' automatically generated by youtube'
    return ret

output_file = get_valid_filename(f'{title}.txt')
with open(output_file , 'w', encoding='UTF-8') as f:
    print("save to ", output_file)
    for sent in subtitle:
        each_sent(sent, file=f)

def parseVideoID(videoID):
    if 'youtu' in videoID:
        videoID = re.search('v=([^&]+)', videoID).group(1)

    video_link = f'https://www.youtube.com/watch?v={videoID}'
    data_link=f"https://youtube.com/get_video_info?video_id={videoID}"
    return videoID, video_link, data_link

videoID = 'https://www.youtube.com/watch?v=5tKOV0KqPlg'
videoID, video_link, data_link = parseVideoID(videoID)
videoID = '5tKOV0KqPlg'
assert (videoID, video_link, data_link) == parseVideoID(videoID)

import fire
import sys
from functools import partial
import json
import re
def main(videoID, output_file=None, save_to_file=True, translation='zh-Hans', to_json=False, caption_num=0, remove_font_tag=True):
    """
    download youtube closed caption(subtitles) by videoID

    Examples:
    dl-youtube-cc -h # to see this helpful infomation
    dl-youtube-cc 5tKOV0KqPlg --save_to_file=False # print stuff in console
    dl-youtube-cc 5tKOV0KqPlg --output_file='test.txt' # print stuff in named file
    dl-youtube-cc 5tKOV0KqPlg --to_json=True # print stuff in json
    dl-youtube-cc 5tKOV0KqPlg --translation 'ja' # use japanese translation, see ./lang_code for full list
    dl-youtube-cc 5tKOV0KqPlg --translation False # without translation
    dl-youtube-cc 5tKOV0KqPlg --caption_num=1 # choose the caption num

    Argument:
    videoID: string, the video link or the id of youtube video, the string after 'v=' in a youtube video link
    output_file: string, default to video title
    save_to_file: bool, default to True, True or False
    translation: bool or string, which will be displayed as original transcript, default to 'zh-Hans' for simplified Chinese, False or lang code, see ./lang_code.json for full list
    to_json: bool, default to False, export caption to json
    caption_num: number, default to 0, choose the caption which will be displayed as original transcript
    remove_font_tag: bool, default to True, remove font tag in txt transcript, but not in json's merged

    """

    videoID, video_link, data_link = parseVideoID(videoID)
    data=get_data(data_link)
    captionTracks, title = get_tracks_title(data)

    info = partial(print, "INFO: ")

    info("available caption(s) will be displayed as original text:")

    for i, caption in enumerate(captionTracks):
        mark = '✔' if caption_num == i else '⭕'
        notice = f"{mark}"
        info(notice, f"#{i}.", format_caption(caption))

    info("✔ marks chosen one,  given by --caption_num in 0-index, default to 0")

    caption = captionTracks[caption_num]
#     info('using',f"{caption_num}.", format_caption(caption))

    baseUrl = caption['baseUrl']
    transcript = requests.get(baseUrl)

    _parseTranscript = partial(parseTranscript, remove_font_tag=remove_font_tag)

    subtitle = _parseTranscript(transcript, )

    output_json = { "original": subtitle }

    if translation:
        baseUrl = caption['baseUrl'] + '&tlang=' + translation
        transcript = requests.get(baseUrl)
        subtitle_cn = _parseTranscript(transcript)
        merged_subtitle = merge_subtitle(subtitle, subtitle_cn)
        output_json = {
                 "original": subtitle,
                 "translation":subtitle_cn,
                # note that it's not guaranteed to be aligned.
                "merged": merged_subtitle,
            }

    ######################## save to file

    f = sys.stdout
    if save_to_file :
        if output_file is None:
            if to_json:
                output_file = get_valid_filename(f'{title}.json')
            else:
                output_file = get_valid_filename(f'{title}.txt')
        f = open(output_file , 'w', encoding='UTF-8')
        info("Save to ", output_file )

    if to_json:
        json.dump(
            output_json
             , f, indent=4, ensure_ascii=False)
        return

    pfile = partial(print, file=f)
    pfile(video_link, file=f)
    for sent in merged_subtitle:
        each_sent(sent, file=f)
        pfile()



from functools import partial
def set_fire(fn):
    if common.IN_TRAVIS or common.IN_JUPYTER:
        return
    fire.Fire(fn)
if __name__ == '__main__':
    if common.IN_TRAVIS or common.IN_JUPYTER:
        pass
    else :
        set_fire(main)
fire_main = partial(set_fire, main)

#fix eachTxt, allow txt.firstChild = None
main('https://www.youtube.com/watch?v=Zd14s2WW-Tc', caption_num=1)

main('https://www.youtube.com/watch?v=EozTm6ZVf1U', caption_num=1)

main('MhCEdIqFCck') # fix title with quotes "

main('HSz7Q4YnQ_M') # fix when cc's length and translated cc's don't match

def read_all_content(f):
    with open(f, 'r', encoding='UTF-8') as f:
        ret = ''.join(f.readlines())
    return ret

f = 'no_font_tag.txt'
main('tktbVrTFUkc', output_file=f) # remove font tag
assert '<font' not in read_all_content(f)
assert '</font>' not in read_all_content(f)
del f

f = 'save_font_tag.txt'
main('tktbVrTFUkc', remove_font_tag=False, output_file=f) # remove font tag
assert '<font' in read_all_content(f)
assert '</font>' in read_all_content(f)
del f