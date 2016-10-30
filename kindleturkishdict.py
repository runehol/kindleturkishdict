#!/usr/bin/env pypy3

from collections import defaultdict
from xml.sax.saxutils import escape, quoteattr
import argparse
import os.path
import time
import re
import sqlite3
import opfgen


freqlist = defaultdict(float)



        
def gen_dict(dest_file, is_mini, inflection_list, dictionary_file):
    start_time = time.clock()

    inflection_re = re.compile("([^\s]+)\s+([^<]+)<.+>")
    lemmas_to_entry = dict()
    index_to_lemmas = defaultdict(list)

    conn = sqlite3.connect(dictionary_file)
    c = conn.cursor()
    not_found_lemmas = dict()
    with open(inflection_list, "r", encoding="utf-8") as f:
        for line in f:
            m = inflection_re.match(line)
            if m:
                inflection, base_form = m.group(1), m.group(2)
                if not is_mini or base_form[0:1] == "a":

                    c.execute("SELECT lookupkey FROM indirectlookups WHERE key=?", (base_form,))
                    defs = [row[0] for row in c.fetchall()]
                    if len(defs):
                        for form in defs:
                            if not form in lemmas_to_entry:
                                c.execute("SELECT definition from definitions where word=?", (form,))
                                definition = c.fetchone()
                                if definition is not None:
                                    formatted_head_word = "<b>%s</b>" % (escape(form))
                                    defn = definition[0]
                                    formatted_defn = defn
                                    lemmas_to_entry[form] = (formatted_head_word, formatted_defn)
                        
                        for form in defs:
                            if form not in index_to_lemmas[inflection]:
                                index_to_lemmas[inflection].append(form)
                    else:
                        not_found_lemmas[base_form] = True



    print("Dictionary health: %d found lemmas, %d not found lemmas" % (len(lemmas_to_entry), len(not_found_lemmas)))


    dirname, fname = os.path.split(dest_file)

    title = "The Morphological Turkish-English Dictionary"
    if is_mini:
        title = "Test Dictionary"

    out_dict = opfgen.KindleDictGenerator(title, "https://github.com/runehol/kindleturkishdict/", ["Rune Holm"], "tr", "en", "../datafiles/turkishdict-cover.jpg", "../datafiles/title-page.html", dirname, fname)

                


        
        
        

    print("Sorting index...")
    dict_entries = defaultdict(list)
        
    for index, lemma_list in index_to_lemmas.items():
        lemma_tuple = tuple(sorted(lemma_list, key=lambda item: (item.count(" "), item)))
        dict_entries[lemma_tuple].append(index)

    print("Generating dictionary...")
    for lemma_tuple, indices in dict_entries.items():
        formatted_head_word, formatted_desc = lemmas_to_entry[lemma_tuple[0]]
        for lemma in lemma_tuple[1:]:
            hw, desc = lemmas_to_entry[lemma]
            desc = "<ul>\n" + desc + "</ul>\n" + "<hr\>\n"
            formatted_desc += hw + desc

        out_dict.add_dict_entry(formatted_head_word, indices, formatted_desc)
        
    out_dict.finalize()

    elapsed_time = time.clock() - start_time
    print("Generated %d original entries, %d expanded entries, %d empty entries, %d index size from %d lemmas in %f seconds" % (out_dict.n_orig_entries, out_dict.n_expanded_entries, out_dict.n_empty_entries, out_dict.index_size, len(lemmas_to_entry), elapsed_time))

                
        
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate an Turkish-English Kindle dictionary')
    parser.add_argument('--dest-file',
                    help='Destination opf file')
    parser.add_argument('--mini', action='store_true',
                    help='Generate small test dictionary (only words starting with a')
    parser.add_argument('--inflection-list',
                    help='Inflection list to use')
    parser.add_argument('--dictionary',
                    help='Dictionary in sqlite3 form to use')

    arg = parser.parse_args()
    gen_dict(arg.dest_file, arg.mini, arg.inflection_list, arg.dictionary)
