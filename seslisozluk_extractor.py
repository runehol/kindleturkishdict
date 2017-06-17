#!/usr/bin/env python3

import re
import sqlite3
from xml.sax.saxutils import escape, quoteattr
import bs4
import locale
import urllib.request
import urllib.parse
import time
import random
import sys
locale.setlocale(locale.LC_ALL, 'tr_TR') #make sure string lowercase are turkish aware



def create_lookup_index(conn):
    c = conn.cursor()
    c.execute('''DROP TABLE IF EXISTS indirectlookups''')
    c.execute('''DROP INDEX IF EXISTS IDlookupkey''')
    c.execute('''CREATE TABLE indirectlookups 
             (key text, lookupkey text)''')
    c.execute('''CREATE INDEX IDlookupkey ON indirectlookups (key)''')

    c.execute("SELECT word from definitions")
    all_keys = [v[0] for v in c.fetchall()]
    for orig_key in all_keys:
        keys = set(orig_key.split(" "))
        keys.add(orig_key)
        for k in keys:
            c.execute("INSERT INTO indirectlookups VALUES (?,?)", (k, orig_key))

    conn.commit()
        

def process_dict_html(c, word, html_doc):
    soup = bs4.BeautifulSoup(html_doc, 'html.parser')
    found_something = False
    bodydiv = soup.find(class_="panel-body sozluk")
    if bodydiv:
        orig_key = word
        for node in bodydiv.find_all(['dt', 'dd']):
            keynode = node.find(class_="word-link")
            valuenode = node.find(class_="definition-link")
            if keynode:
                orig_key = keynode.text.strip()
                
            if valuenode:
                definition = valuenode.string
                wordform = ""
                found_something = True

                data = """<li> %s <i>%s</i> %s</li>\n""" % (escape(orig_key), wordform, definition)
                processed_key = orig_key.lower()

                #c.execute("SELECT definition from definitions WHERE word=?", (processed_key,))
                #d = c.fetchone()
                #if d:
                #    data = d[0] + data
                #    c.execute("UPDATE definitions SET definition=? WHERE word=?", (data, processed_key))
                #else:
                #    c.execute("INSERT INTO definitions VALUES (?,?)", (processed_key, data))
                orig_key = word

    if not found_something:
        print("no definitions found for", word)


def process(words, dbfile, recreate_db=False):
    conn = sqlite3.connect(dbfile)
    if recreate_db:
        c = conn.cursor()
        c.execute('''DROP TABLE IF EXISTS definitions''')
        c.execute('''DROP INDEX IF EXISTS WDefinitions''')
        c.execute('''DROP TABLE IF EXISTS alreadylookedup''')
        c.execute('''DROP INDEX IF EXISTS Walreadylookedup''')
        c.execute('''CREATE TABLE definitions 
             (word text, definition text)''')
        c.execute('''CREATE UNIQUE INDEX WDefinitions ON definitions (word)''')
        c.execute('''CREATE TABLE alreadylookedup 
             (word text)''')
        c.execute('''CREATE UNIQUE INDEX Walreadylookedup ON alreadylookedup (word)''')
        conn.commit()

    for word in words:
        url = "https://www.seslisozluk.net/en/what-is-the-meaning-of-%s/" % (urllib.parse.quote_plus(word),)
        try:
            c = conn.cursor()
            c.execute("SELECT word from alreadylookedup WHERE word=?", (word,))
            res = c.fetchone()
            if not res:
                print("fetching", word)
                time.sleep(random.uniform(0.2, 0.4))
                req = urllib.request.Request(
                    url, 
                    data=None, 
                    headers={
                        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36'
                    }
                )

                f = urllib.request.urlopen(req)
                html_doc = f.read()

                process_dict_html(c, word, html_doc)
                c.execute("INSERT INTO alreadylookedup VALUES (?)", (word,))
                conn.commit()
        except urllib.error.URLError as e:
            print("got url error for url", url, e)

    create_lookup_index(conn)
    conn.close()


def get_word_list_from_inflection_file(inflection_list):
    inflection_re = re.compile("([^\s]+)\s+([^<]+)<.+>")

    res = set()

    with open(inflection_list, "r", encoding="utf-8") as f:
        for line in f:
            m = inflection_re.match(line)
            if m:
                inflection, base_form = m.group(1), m.group(2)
                res.add(base_form)
    return res





if __name__ == "__main__":
    dictlist = get_word_list_from_inflection_file("inflection-list.txt")
    #dictlist = sorted(dictlist)
    #dictlist = list(sorted([d for d in dictlist if d.startswith("a")]))[:50]
    print(len(dictlist))
    
    process(dictlist, "seslisozluk-definitions.db", False)

