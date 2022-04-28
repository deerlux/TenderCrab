# -*- coding: utf-8 -*-
from sqlalchemy.ext.declarative import declarative_base
import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker
import TenderCrab.settings as settings

engine = sa.create_engine(settings.DBURL)
Session = sessionmaker(bind=engine)

Base = declarative_base()


class TenderItem(Base):
    __tablename__ = 'tender_item'
    id = sa.Column(sa.Integer, primary_key=True,
        auto_increment=True)
    name = sa.Column(sa.String)
    title = sa.Column(sa.String)
    url = sa.Column(sa.String)
    seller = sa.Column(sa.String)
    seller_address = sa.Column(sa.String)
    price = sa.Column(sa.String)
    publish_date = sa.Column(sa.DateTime)
    body = sa.Column(sa.String)


def get_url_hashset() -> set:
    result = set()
    with Session() as session:
        stmt = sa.select(TenderItem.url)
        url_result = session.execute(stmt)
        for url in url_result:
            result.add(hash(url[0]))
    return result

if __name__ == "__main__":
    engine = sa.create_engine("sqlite:///test.db")
    Base.metadata.create_all(bind=engine)
