#!/usr/bin/env python

"""
Using csv file, `locate` filename and determine wether to download file from
forvo.
Build separate csv file if filename missing and unavailable on forvo.
"""

import sys
reload(sys)
sys.setdefaultencoding('utf-8')

import csv
import subprocess as sp
import requests as rq
import os.path
from itertools import islice
import time

api_key = sys.argv[1]
audio_path = sys.argv[2]
loc_db = audio_path + '.locate.db'

def build_db():
    """Use updatedb to create a locally stored copy of %audio_path for
    searching"""
    
    l_run = ['updatedb', '-l', '0', '-o', loc_db, '-U', audio_path]

    l_result = sp.Popen(l_run, stdout=sp.PIPE).communicate()[0] 
    
    return

def build_wiki():
    
    csv_head = ['**Word**', '**Accent (BR)**', '**Accent (PT)**', '**Link**']
    csv_form = ['---', ':---:', ':---:', '---']

    with open('csv/wiki.csv', 'wb') as wiki_head:
        csv_wr = csv.writer(wiki_head, delimiter='|')
        csv_wr.writerow(csv_head)
        csv_wr.writerow(csv_form)

    return;

def wiki_table( wiki_word, acc_br, acc_pt ):
    """wiki table"""

    csv_w = []
    csv_w.append(wiki_word)

    if acc_br == False:
        csv_w.append('&#10006;')
    else:
        csv_w.append('&#10004;')

    if acc_pt == False:
        csv_w.append('&#10006;')
    else:
        csv_w.append('&#10004;')

    csv_w.append('https://forvo.com/word-record/' + wiki_word + '/pt/')
    
    if acc_br == False or acc_pt == False:
        with open('csv/wiki.csv', 'ab') as wiki_file:
            csv_wr = csv.writer(wiki_file, delimiter='|')
            csv_wr.writerow(csv_w)

    return;

def loc_audio( aud_name, accent ):
    """Using `locate` list aud_name, use any() to return True/False for accent
    
    @param aud_name: audio file to `locate`
    @param accent: (br)azil, (p)or(t)ugal
    @type aud_name: str
    @type accent: str
    """

    l_aud_name = '/' + aud_name + '.(mp3|ogg)'
    l_loc = ['locate', '-d', loc_db, '--regex', l_aud_name]

    l_result =\
    sp.Popen(l_loc, stdout=sp.PIPE).communicate()[0].rsplit('\n')[:2]

    if accent == 'pt':
        l_acc = 'Portugal'
    elif accent == 'br':
        l_acc = 'Brazil'

    dled = any(l_acc in cntry for cntry in l_result)

    return dled;
     
def forvo_api( fetch_word, fetch_br, fetch_pt ):
    """Check against forvo api for audio clips of %fetch_word, if available
    download. If not mark as unavailable and log in csv
    
    @param fetch_word: word to search
    @param fetch_br: True/False. Logic is odd: False = search for and download
    @param fetch_pt: True/False. As above.
    @type fetch_word: str
    @type fetch_br: bool
    @type fetch_pt: bool    
    """
    
    api_url =\
    'https://apicommercial.forvo.com/key/' + api_key +\
    '/format/json/action/word-pronunciations/word/' + fetch_word +\
    '/language/pt/'

    api_data = rq.get(api_url).json()
    api_cnt = int(api_data['attributes']['total'])
    
    if api_cnt > 0:
        items = api_data['items']
        for item in items:
            if fetch_br == False and item['country'] == 'Brazil':
                api_ogg = rq.get(item['pathogg'], stream=True)
                with open(os.path.join(audio_path + item['country'] 
                + '/', fetch_word + '.ogg'), 'wb') as api_file:
                    api_file.write(api_ogg.content)
                    csv_br = '&#10004;'
                    fetch_br = True
            elif fetch_pt == False and item['country'] == 'Portugal':
                api_ogg = rq.get(item['pathogg'], stream=True)
                with open(os.path.join(audio_path + item['country']
                + '/', fetch_word + '.ogg'), 'wb') as api_file:
                    api_file.write(api_ogg.content) 
                    csv_pt = '&#10004;'
                    fetch_pt = True
    
    wiki_table( fetch_word, fetch_br, fetch_pt )

    return;

def main():
    build_db()
    
    build_wiki()

    with open('csv/current.csv') as csv_file:
        rows = csv.DictReader(csv_file, delimiter=',',
        fieldnames=['card','word','te','ep','ee','audio','tag'])
        for row in islice(rows,1000):
            accent_br = loc_audio( row['word'], 'br' )
            accent_pt = loc_audio( row['word'], 'pt' )
        
            forvo_api( row['word'], accent_br, accent_pt )
    
    return;

if __name__ == "__main__":
    main()
