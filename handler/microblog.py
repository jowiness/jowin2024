from flask import Blueprint, render_template, redirect, request, jsonify, session, make_response
from config import db
from bson import ObjectId
import datetime, os, random

bp = Blueprint('microblog', __name__)


def microblog_find(page, count=5, type='paging'):
    '''
    :param page: 页数
    :param count: 每页显示数量
    :param type: 类型，paging表示分页，init表示从下标0开始
    :return: 根据 page 返回列表 microblogs 中的对象
    '''
    if type == 'paging':
        data = list(db.microblog.find().skip((page - 1) * count).limit(count).sort('create_time', -1))
    elif type == 'init':
        data = list(db.microblog.find().limit(page * count).sort('create_time', -1))

    return data


@bp.route('/')
def index():
    # 若没有则重定向到登录页
    if session.get('user') is None:
        return redirect('/user/login')
    user = session['user']

    # 获取Cookie中保存的用户名
    # username = request.cookies.get('username', '')

    page = request.cookies.get('page')
    if page is None:
        page = 1
    microblog_data = microblog_find(int(page), type='init')

    return render_template('index.html', microblogs=microblog_data, user=user)


@bp.route('/microblog/load', methods=['GET'])
def microblog_load():
    # 从 cookie 中获取当前页数
    page = request.cookies.get('page')
    # page是None，默认加载第2页，否则加载当前页的下一页
    if page is None:
        page = 2
    else:
        page = int(page) + 1
    microblog_data = microblog_find(page)
    # 打印取到的数据
    print(microblog_data)

    # 将 ObjectId 类型值转成字符串
    for blog in microblog_data:
        blog['_id'] = str(blog['_id'])
        blog['author']['_id'] = str(blog['author']['_id'])
        if 'liker_id' in blog:
            for liker_id in blog['liker_id']:
                blog['liker_id'] = str(liker_id)
    print(microblog_data)
    response = make_response(jsonify({'data': microblog_data}))

    if len(microblog_data) > 0:
        # 将当前页数 page 保存到 cookie 中
        response.set_cookie("page", str(page))

    return response


@bp.route('/microblog/detail', methods=['GET'])
def detail():
    if not session.get('user'):
        return redirect('/user/login')
    blog_id = ObjectId(request.args.get('id'))
    blog = db.microblog.find_one({'_id': blog_id})

    # 是否已经点赞
    user = session['user']
    print('user:', user)
    user_id = ObjectId(user['_id'])
    if 'liker_id' in blog and user_id in blog['liker_id']:
        is_liked = True
    else:
        is_liked = False
    blog['is_liked'] = is_liked
    # 点赞数
    if 'liker_id' in blog:
        blog['likes'] = len(blog['liker_id'])
    else:
        blog['likes'] = 0

    # 评论
    com_list = list(db.comment.find({'blog_id': blog_id}))
    blog['comments'] = len(com_list)
    blog['com_list'] = com_list

    return render_template('detail.html', blog=blog)


# 点赞
@bp.route('/like/create', methods=['GET'])
def like_on():
    # 因为访问该路由的是ajax请求，所以重定向是无效的,故返回json数据让浏览器端完成访问登录页面的操作
    if not session.get('user'):
        return jsonify({'status': 'failure', 'data': '请先登录'})
    user = session['user']
    user_id = ObjectId(user['_id'])
    blog_id = ObjectId(request.args.get('blog_id'))
    db.microblog.update({'_id': blog_id}, {'$push': {'liker_id': user_id}})
    return jsonify({'status': 'success', 'data': '点赞成功'})


# 取消点赞
@bp.route('/like/delete', methods=['GET'])
def like_cancle():
    if not session.get('user'):
        return jsonify({'status': 'failure', 'data': '请先登录'})
    user = session['user']
    user_id = ObjectId(user['_id'])
    blog_id = ObjectId(request.args.get('blog_id'))
    db.microblog.update({'_id': blog_id}, {'$pull': {'liker_id': user_id}})
    return jsonify({'status': 'success', 'data': '取消点赞成功'})


@bp.route('/comments/create', methods=['POST'])
def comment():
    if not session.get('user'):
        return jsonify({'status': 'failure', 'data': '请先登录'})
    user = session['user']
    user_id = ObjectId(user['_id'])
    blog_id = ObjectId(request.form.get('blog_id'))
    content = request.form.get('content')

    user = db.user.find_one({'_id': user_id})
    comment = {
        'author': user,
        'blog_id': blog_id,
        'content': content,
        'create_time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    db.comment.insert_one(comment)
    return jsonify({'status': 'success', 'data': '评论成功'})


@bp.route('/comments/list', methods=['GET'])
def comment_list():
    blog_id = ObjectId(request.args.get('blog_id'))
    com_list = list(db.comment.find({'blog_id': blog_id}))
    # 将ObjectId类型转成str
    for comment in com_list:
        comment['_id'] = str(comment['_id'])
        comment['blog_id'] = str(comment['blog_id'])
        comment['author']['_id'] = str(comment['author']['_id'])
    return jsonify({'status': 'success', 'data': com_list})


@bp.route('/microblog/pub', methods=['GET'])
def publish():
    if not session.get('user'):
        return redirect('/user/login')
    user = session['user']
    return render_template('pub.html', user=user)


@bp.route('/microblog/create', methods=['POST'])
def create():
    if not session.get('user'):
        return redirect('/user/login')
    user = session['user']
    user['_id'] = ObjectId(user['_id'])
    # 接收发布微博的文本内容
    content = request.form.get('text')
    # 定义空列表，后期存储文件名
    file_list = []
    # 接收多个文件
    files = request.files.getlist('filelist')
    # 遍历 FileStorage 文件对象列表
    for file in files:
        # 调用预留的函数实现在服务器保存文件，并返回新的文件名
        file_name = img_upload(file)
        # 把新的文件名添加到文件列表中
        file_list.append(file_name)
    # 构建字典，保存微博作者信息author，微博内容content，微博图片photos，微博发布时间create_time
    blog = {'author': user,
            'content': content,
            'photos': file_list,
            'create_time': datetime.datetime.now()}
    # 添加一条微博文档
    db.microblog.insert_one(blog)
    # 重定向到首页
    return redirect('/')


# 存储图片到服务器
def img_upload(file):
    # 在下方写你的代码：定义文件存储目录
    pass
    # 如果目录不存在，则创建目录

    # 获取文件名的扩展名
   
    # 用时间戳的总微秒数和 10000-99999 之间的随机数生成文件名
    
    # 创建该文件名的文件
   
    # 在新文件中写入原文件内容
   
    # 关闭文件

    # 返回新的文件名
   

