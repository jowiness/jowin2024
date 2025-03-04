from flask import Blueprint, render_template, session, redirect, request, jsonify, abort
from config import db
from bson import ObjectId
import traceback

bp = Blueprint('game', __name__)


@bp.route('/game')
def game():
	if not session.get('user'):
		return redirect('/user/login')
	user = session['user']
	games = list(db.game.find({}))
	return render_template('game.html', user=user, games=games)


@bp.route('/game/plane_war', methods=['GET'])
def game_plane_war():
	if not session.get('user'):
		return redirect('/user/login')
	user = session['user']
	user_id = ObjectId(user['_id'])
	game_id = ObjectId(request.args.get('id'))
	# 使用一个新的集合保存用户的游戏记录
	record = db.record.find_one({'user_id': user_id, 'game_id': game_id})
	if record == None:
		record = {
			'user_id': user_id,
			'game_id': game_id,
			'power_level': 1,
			'shoot_level': 1,
			'life_level': 3
		}
		db.record.insert_one(record)
	return render_template('/game/plane.html', record=record)


@bp.route('/store', methods=['GET'])
def store_index():
	if not session.get('user'):
		return redirect('/user/login')
	user = session['user']
	props = list(db.props.find({}))
	return render_template('store.html', user=user, props=props)


@bp.route('/store/buy', methods=['GET'])
def store_buy():
	if not session.get('user'):
		return redirect('/user/login')
	try:
		user = session['user']
		prop_id = ObjectId(request.args.get('prop_id'))
		prop = db.props.find_one({'_id': prop_id})
		if user['coins'] < prop['price']:
			return jsonify({'data': '金币不足'})

		# 游戏数据更新
		record = db.record.find_one({'user_id': ObjectId(user['_id']), 'game_id': prop['game_id']})
		if record is None:
			# 如果此前没有记录，则插入游戏记录
			record = {
				'user_id': ObjectId(user['_id']),
				'game_id': prop['game_id'],
				'power_level': 1,
				'shoot_level': 1,
				'life_level': 3
			}
			db.record.insert_one(record)

		ability = prop['ability']
		# 当前级数小于最大级，级数加1
		if record[ability] < prop['max']:
			record[ability] += 1
			# 通过user_id和game_id来查找游戏记录（如果用游戏记录的_id做条件查找的话，上面需要在插入后再查找一次）
			db.record.update_one({'user_id': ObjectId(user['_id']), 'game_id': prop['game_id']}, {'$set': record})
		else:
			return jsonify({'data': '已经满级'})

		# 消耗金币
		user['coins'] -= prop['price']
		db.user.update_one({'_id': ObjectId(user['_id'])}, {'$set': {'coins': user['coins']}})
		session['user'] = user

		return jsonify({'data': '购买成功'})
	except Exception as e:
		traceback.print_exc()
		return jsonify({'data': '服务端程序出错了！'})
