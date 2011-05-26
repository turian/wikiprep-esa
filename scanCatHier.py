#!/usr/bin/python

'''
Copyright (C) 2010  Cagatay Calli <ccalli@gmail.com>

Scans XML output (gum.xml) from Wikiprep and outputs cat_hier file.
Output format: <cat id> <list of immediate descendants cat ids>

USAGE: scanCatHier.py <hgw.xml file from Wikiprep> <cat_hier output file path>

IMPORTANT: If you use XML output from a recent version of Wikiprep
(e.g. Zemanta fork), then set FORMAT to 'Zemanta-legacy' or 'Zemanta-modern'.

'''

import sys
try:
    import re2 as re
    re.set_fallback_notification(re.FALLBACK_WARNING)
    print >> sys.stderr, "Using re2 for faster regex parsing"
except:
    import re
    print >> sys.stderr, "WARNING: re2 not detected. Regex parsing will be slow. See the README for install instructions."

FORMAT = 'Gabrilovich'


# read list of stop categories from 'wiki_stop_categories.txt'
STOP_CATS = []
try:   
        f = open('wiki_stop_categories.txt','r')
        for line in f.readlines():
                ps = line.split('\t')
		strId = ps[0]
                STOP_CATS.append(int(strId))
        f.close()
except:
        print 'Stop categories cannot be read! Please put "wiki_stop_categories.txt" file containing stop categories in this folder.'
        sys.exit(1)


rePage = re.compile('<page id="(?P<id>\d+)".+?>(?P<page>.+?)</page>',re.MULTILINE | re.DOTALL)

reContent = re.compile('<title>(?P<title>.+?)</title>\n<categories>(?P<categories>.*?)</categories>',re.MULTILINE | re.DOTALL)

reCategory = re.compile("^Category:.+",re.DOTALL)

RSIZE = 10000000	# read chunk size = 10 MB

catDict = {}
catTitles = {}

# pageContent - <page>..content..</page>
# pageDict - stores page attribute dict
def recordArticle(pageDict):
   global catDict,catTitles

   mContent = reContent.search(pageDict['page'])
   if not mContent:
	return

   contentDict = mContent.groupdict()

   title = contentDict['title']
   if not reCategory.match(title):
	return

   id = pageDict['id']
   curId = int(id)

   catTitles[curId] = title

   cats = contentDict['categories']

   cs = []
   for cat in cats.split():
	c = int(cat)
	if catDict.has_key(c):
		catDict[c].add(curId)
	else:
		catDict[c] = set([curId])

   return


args = sys.argv[1:]
# scanCatHier.py <hgw_file> <RSIZE>

if len(args) < 1:
    sys.exit()

if len(args) == 2:
    RSIZE = int(args[1])

f = open(args[0],'r')
prevText = ''

firstRead = f.read(10000)

if FORMAT == 'Gabrilovich':
	documentStart = firstRead.find('</siteinfo>') + len('</siteinfo>')
else:
	documentStart = firstRead.find('<gum>') + len('<gum>')

prevText = firstRead[documentStart:10000]

while True:

    newText = f.read(RSIZE)
    if not newText:
        break
    
    text = prevText + newText

    endIndex = -1
    
    for page in rePage.finditer(text):
        recordArticle(page.groupdict())
	endIndex = page.end()

    prevText = text[endIndex:]

f.close()

print 'cat_hier output complete'
print 'traversing category tree..'

cats = set(STOP_CATS)
outcats = set(STOP_CATS)

while cats:
	parent = cats.pop()

	childs = []
	if catDict.has_key(parent):
		childs = catDict[parent]

	# avoid cycles/repeats
	for c in childs:
		if not c in outcats:
			cats.add(c)
			outcats.add(c)

# write extended stop category list
f = open('extended_stop_categories.txt','w')
for c in outcats:
	f.write(str(c) + '\t' + catTitles[c] + '\n')
f.close()
