import pymongo, os, json, datetime, random
from bson import ObjectId
from flask.json import JSONEncoder
from datetime import date
import chardet

ip = '127.0.0.1'
port = 27017
database = 'blog'

client = pymongo.MongoClient(ip, port)
db = None


def get_db():
    global db
    if not db:
        db = client[database]
    return db


db = get_db()

data_path = './data'


# 导入原始数据的方法
def data_import():
    coll_list = db.list_collection_names()
    for collection in coll_list:
        # 删除集合
        db[collection].drop()

    for maindir, subdir, file_list in os.walk(data_path):
        for file_name in file_list:
            if file_name[file_name.rindex('.'):] == '.json':
                coll = file_name[:file_name.rindex('.')]

                with open(data_path + '/' + file_name, encoding='utf-8') as file:
                    str = file.read()
                    if str is '' or str is None:
                        continue
                    else:
                        data = []
                        data.extend(json.loads(str))
                        if coll == 'user':
                            for d in data:
                                d['_id'] = ObjectId(d['_id'])
                        if coll == 'microblog':
                            for d in data:
                                d['_id'] = ObjectId(d['_id'])
                                d['author']['_id'] = ObjectId(d['author']['_id'])
                                d['photos'] = d['photos'].split(',')
                                d['create_time'] = randomtimes('2020-01-01', '2020-06-30', 1)
                        if coll == 'game':
                            for d in data:
                                d['_id'] = ObjectId(d['_id'])
                        if coll == 'props':
                            for d in data:
                                d['game_id'] = ObjectId(d['game_id'])
                        db[coll].insert_many(data)


def randomtimes(start, end, n, frmt="%Y-%m-%d"):
    stime = datetime.datetime.strptime(start, frmt)
    etime = datetime.datetime.strptime(end, frmt)
    return [random.random() * (etime - stime) + stime for _ in range(n)][0].strftime('%Y-%m-%d %H:%M:%S')


class CustomJSONEncoder(JSONEncoder):

    def default(self, obj):
        try:
            if isinstance(obj, date):
                return obj.isoformat(sep=' ')
            iterable = iter(obj)
        except TypeError:
            pass
        else:
            return list(iterable)
        return JSONEncoder.default(self, obj)


def decode_data(c):
    """
    把bytes类型的文本文件根据对应编码进行解码
    :param c:
    :return: 解码后的数据
    """
    coding = chardet.detect(c)['encoding']
    data = c.decode(coding)
    return data
