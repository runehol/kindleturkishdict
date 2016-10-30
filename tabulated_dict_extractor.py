#!/usr/bin/env python3

import re
import sqlite3
from xml.sax.saxutils import escape, quoteattr



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
        






def process(filenames, language, dbfile):
    conn = sqlite3.connect(dbfile)
    c = conn.cursor()
    c.execute('''DROP TABLE IF EXISTS definitions''')
    c.execute('''DROP INDEX IF EXISTS WDefinitions''')
    c.execute('''CREATE TABLE definitions 
             (word text, definition text)''')
    c.execute('''CREATE UNIQUE INDEX WDefinitions ON definitions (word)''')
    conn.commit()

    for filename in filenames:
        for line in open(filename):
            line = line.strip()
            if not line or line[0] == "#": continue
            items = line.split("\t")
            orig_key = items[0]
            definition = items[1]
            wordform = ""
            if len(items) >= 3: wordform = items[2]

        

            data = """<li> %s <i>%s</i> %s</li>\n""" % (escape(orig_key), wordform, definition)

            c.execute("SELECT definition from definitions WHERE word=?", (orig_key,))
            d = c.fetchone()
            if d:
                data = d[0] + data
                c.execute("UPDATE definitions SET definition=? WHERE word=?", (data, orig_key))
            else:
                c.execute("INSERT INTO definitions VALUES (?,?)", (orig_key, data))


            conn.commit()

    create_lookup_index(conn)
    conn.close()



if __name__ == "__main__":
    process(["dictcc-tr-en.txt", "turkish-english-2016-10-30.txt", "wiktionary-tr-en.txt", "omegawiki-tr-en.txt", "wikipedia-interlanguage-tr-en.txt"], "Turkish", "turkish-definitions.db")
