#%%
import sys
sys.path.append('.')

from typer import Typer
from TenderCrab.DataModels import Session, TenderItem
from sqlalchemy import select, func
from parsel import Selector
import re
import logging
import typer

logging.basicConfig(filename='analyze.log', level=logging.INFO)

#%%
session = Session()

#%%
def get_buyer1(body: str):
    temp = re.findall(r'采购人[：:]([\u4e00-\u9fa5\w]+)', body)
    if temp:
        return temp[0]
    else:
        wrm = re.sub(r'<[^>]+>', ' ', body)
        temp = re.findall(r'采购人名?称?[：:]\s*([\u4e00-\u9fa5\w]+)', wrm)
        if temp:
            return temp[0]
        else:
            return None

def get_buyer2(body: str):
    temp = re.sub(r'<[^>]+>', '', body)
    temp1 = re.findall(r'采购人信息[\xa0\s]*名[\xa0\s]*称：([\u4e00-\u9fa5\w]+)', temp)
    if temp1: 
        return temp1[0]
    else:
        return None

def update_buyer(batch:int=100, offset:int=0, total_count:int=0):
    global session
    if total_count == 0:
        stmt = select(func.count()).select_from(TenderItem)
        result = session.execute(stmt).fetchone()
        total_count = result[0]

    count = 0
    while count < total_count:
        stmt = select(TenderItem).limit(batch).offset(count + offset)
        result = session.execute(stmt).fetchall()
        count += batch
        for k, row in enumerate(result):
            temp = get_buyer1(row[0].body)
            if temp:
                row[0].buyer = temp
                continue
            temp = get_buyer2(row[0].body)
            if temp:
                row[0].buyer = temp
            else:
                logging.info(f"Failed to find buyer {row[0].id}")
        logging.info(f'{count} of {total_count} is completed.')
        session.commit()
#%%
if __name__ == "__main__":
    typer.run(update_buyer) 


# %%
stmt = select(TenderItem).limit(20).offset(38)
result = session.execute(stmt).fetchall()

