#!/bin/bash
cd $HOME/TenderCrab
source venv/bin/activate
scrapy crawl TenderSD 
count=`sqlite3 test.db "select count(*) from tender_item;"`
echo "$(date '+%Y-%m-%d %H:%M:%S'), $count" >> count.csv
