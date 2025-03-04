import pymongo


def data_init():
    client = pymongo.MongoClient('mongodb://localhost:27017/')
    db = client.database76
    db.photos.delete_many({})
    return db


db = data_init()
