#!/bin/sh
wget http://www.nationstates.net/pages/nations.xml.gz &
wget http://www.nationstates.net/pages/regions.xml.gz &
wait
gunzip nations.xml.gz &
gunzip regions.xml.gz &
wait
grep "^<NATIONS>.\+<" regions.xml | sed "s/^<NATIONS>\(.\+\)<\/NATIONS>/\1/" > region_nations.txt
sed "s/:/\n/g" < region_nations.txt > rnations.txt
sort -u < rnations.txt > sr_nations.txt
grep "^<NAME>" nations.xml | sed "s/^<NAME>\(.\+\)<\/NAME>$/\1/" | tr "[:upper:] " "[:lower:]_" > nations.txt
sort < nations.txt > s_nations.txt
diff s_nations.txt sr_nations.txt

