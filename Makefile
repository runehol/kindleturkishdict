
.PHONY: all mini clean install

all: turkishdict/morphological_turkish_english_dict.mobi
mini: minidict/minidict.mobi


turkishdict/morphological_turkish_english_dict.mobi: turkishdict/morphological_turkish_english_dict.opf
	cd turkishdict &&  /usr/bin/time kindlegen -c2 -verbose -dont_append_source morphological_turkish_english_dict.opf; true

turkishdict/morphological_turkish_english_dict.opf: $(wildcard *.py) $(wildcard *.txt) inflection-list.txt
	./kindleturkishdict.py --dest-file=$@  --inflection-list inflection-list.txt --dictionary turkish-definitions.db

install: turkishdict/morphological_turkish_english_dict.mobi
	rm -r /Volumes/Kindle/documents/morphological_turkish_english_dict.*; cp turkishdict/morphological_turkish_english_dict.mobi /Volumes/Kindle/documents/morphological_turkish_english_dict.mobi


master-list.txt: freqlist-ebooks.txt  freqlist-subtitles-2012.txt
	./create_master_word_list.py --dest-file=$@ --frequency-list $^  --min-word-frequency=1

inflection-list.txt: master-list.txt
	flookup TRmorph/stem.fst < $^ > $@

minidict/minidict.mobi: minidict/minidict.opf
	cd minidict &&  /usr/bin/time kindlegen -c2 -verbose -dont_append_source minidict.opf; true

minidict/minidict.opf: $(wildcard *.py) $(wildcard *.txt) inflection-list.txt
	./kindleturkishdict.py --mini --dest-file=$@ --inflection-list inflection-list.txt --dictionary turkish-definitions.db

installmini: minidict/minidict.mobi
	rm -r /Volumes/Kindle/documents/morphological_turkish_english_dict.*; cp minidict/minidict.mobi /Volumes/Kindle/documents/morphological_turkish_english_dict.mobi





clean:
	rm -r turkishdict minidict

