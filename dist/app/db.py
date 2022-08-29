import databases
import ormar
import sqlalchemy
import datetime

from .config import settings

database = databases.Database(settings.db_url)
metadata = sqlalchemy.MetaData()


class BaseMeta(ormar.ModelMeta):
    metadata = metadata
    database = database

class Content(ormar.Model):
    class Meta(BaseMeta):
        tablename = "content"

    id: int = ormar.Integer(primary_key=True)
    filename: str = ormar.String(max_length=128, nullable=False)
    size: int = ormar.Integer(default=0)
    uri: str = ormar.String(max_length=128, nullable=False)
    created_date: datetime.datetime = ormar.DateTime(timezone=True, default=datetime.datetime.now())

    #active: bool = ormar.Boolean(default=True, nullable=False)

# class User(ormar.Model):
#     class Meta(BaseMeta):
#         tablename = "users"

#     id: int = ormar.Integer(primary_key=True)
#     email: str = ormar.String(max_length=128, unique=True, nullable=False)
#     active: bool = ormar.Boolean(default=True, nullable=False)


engine = sqlalchemy.create_engine(settings.db_url)
metadata.create_all(engine)
