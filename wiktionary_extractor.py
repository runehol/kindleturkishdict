#!/usr/bin/env python3

import xml.etree.ElementTree
import re
import io
import sqlite3
from xml.sax.saxutils import escape, quoteattr

section_regex = re.compile(r"(==+)([^=]+)")
metadata_regex = re.compile(r"\[\[.*\]\]")


parts_of_speech = ["Noun", "Verb", "Adjective", "Adverb", "Pronoun", "Preposition", "Article", "Conjunction", "Determiner", "Interjection", "Symbol", "Proper noun", "Initialism", "Particle", "Abbreviation", "Numeral", "Postposition", "Acronym"]
parts_of_speech += ["Letter", "Suffix", "Prefix", "Phrase", "Idiom", "Diacritical mark", "Proverb", "Prepositional phrase"]


def mediawiki_to_html(text):
    return text


def parse_mediawiki(title, text, language):
    
    if ":" in title: return None

    seen_interesting_lang = False
    lang_interesting = False
    in_definition = False
    last_section_name = ""
    output = []
    pronunciation_lines = []
    etymology_lines = []
    definition_lines = []
    stri = io.StringIO(text)
    for line in stri:
        m = section_regex.match(line)
        if m:
            indent = len(m.group(1))
            section_name = m.group(2).strip()


            if in_definition:
                # just finished up a definition. wrap it and output it
                output += definition_lines + pronunciation_lines + etymology_lines
                definition_lines = []
                pronunciation_lines = []
                etymology_lines = []

            if indent == 2:
                lang_interesting = section_name == language
                if lang_interesting: seen_interesting_lang = True
                in_definition = False
            elif indent >= 3:
                in_definition = section_name in parts_of_speech
            else:
                in_definition = False
            last_section_name = section_name

        if lang_interesting:
            if not metadata_regex.match(line):
                if in_definition:
                    definition_lines.append(line)
                # elif last_section_name == "Pronunciation":
                #     pronunciation_lines.append(line)
                # elif last_section_name.startswith("Etymology"):
                #     etymology_lines.append(line)

    # get the last definition, and possibly straggler pronuncation or etymology parts
    output += definition_lines + pronunciation_lines + etymology_lines
    definition_lines = []
    pronunciation_lines = []
    etymology_lines = []

    if seen_interesting_lang and output == []:
        if title == "-tan":
            pass #the -tan article is a suffix article that's marked up wrong. We don't care
        else:
            print("Article %s has Turkish content but no interesting part" % (title,))
            #raise Exception("Article %s has Turkish content but no interesting part" % (title,))
        
    if output != []:
        result = "==%s==\n" % (title,) + "".join(output)
        return result
    else:
        return None







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
        



def process(filename, language, dbfile):
    last_title = ""
    n_articles = 0
    n_useful_articles = 0
    conn = sqlite3.connect(dbfile)
    c = conn.cursor()
    conn.commit()
    for event, elem in xml.etree.ElementTree.iterparse(filename):
        if elem.tag == "{http://www.mediawiki.org/xml/export-0.10/}title":
            last_title = elem.text
            n_articles += 1
        elif elem.tag == "{http://www.mediawiki.org/xml/export-0.10/}text":
            if elem.text != None:
                c.execute("SELECT definition from definitions WHERE word=?", (last_title,))
                if not c.fetchone():
                    data = parse_mediawiki(last_title, elem.text, language)
                    if data != None:
                        n_useful_articles += 1
                        c.execute("INSERT INTO definitions VALUES (?,?)", (last_title, escape(data)))
                        conn.commit()
        elem.clear()

    print("Parsed %d articles, %d useful" % (n_articles, n_useful_articles))
    conn.commit()
    create_lookup_index(conn)
    conn.close()



if __name__ == "__main__":
    process("enwiktionary-latest-pages-articles.xml", "Turkish", "turkish-definitions.db")
