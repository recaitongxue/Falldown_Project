import re

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 修复 get_daily_statistics 函数
old_daily_stats = '''@app.route('/api/statistics/daily', methods=['GET'])
def get_daily_statistics():
    """获取每日统计数据"""
    import random
    range_days = request.args.get('range', '7d')
    days = int(range_days.replace('d', ''))

    statistics = []
    today = datetime.date.today()
    for i in range(days):
        date = today - datetime.timedelta(days=i)
        statistics.append({
            'date': date.isoformat(),
            'detections': random.randint(50, 200),
            'falls': random.randint(0, 15),
            'users': random.randint(10, 50)
        })

    statistics.reverse()

    return jsonify({
        'success': True,
        'data': statistics,
        'range': range_days
    }), 200'''

new_daily_stats = '''@app.route('/api/statistics/daily', methods=['GET'])
def get_daily_statistics():
    """获取每日统计数据"""
    range_days = request.args.get('range', '7d')
    days = int(range_days.replace('d', ''))

    statistics = []
    today = datetime.date.today()
    for i in range(days):
        date = today - datetime.timedelta(days=i)
        start_of_day = datetime.datetime.combine(date, datetime.datetime.min.time())
        end_of_day = datetime.datetime.combine(date, datetime.datetime.max.time())

        detections = DetectionRecord.query.filter(
            DetectionRecord.created_at >= start_of_day,
            DetectionRecord.created_at <= end_of_day
        ).count()

        falls = DetectionRecord.query.filter(
            DetectionRecord.created_at >= start_of_day,
            DetectionRecord.created_at <= end_of_day,
            DetectionRecord.fall_detected == True
        ).count()

        users = db.session.query(db.func.count(db.func.distinct(DetectionRecord.user_id))).filter(
            DetectionRecord.created_at >= start_of_day,
            DetectionRecord.created_at <= end_of_day
        ).scalar() or 0

        statistics.append({
            'date': date.isoformat(),
            'detections': detections,
            'falls': falls,
            'users': users
        })

    statistics.reverse()

    return jsonify({
        'success': True,
        'data': statistics,
        'range': range_days
    }), 200'''

content = content.replace(old_daily_stats, new_daily_stats)

# 修复 get_top_users 函数
old_top_users = '''@app.route('/api/statistics/top-users', methods=['GET'])
def get_top_users():
    """获取活跃用户排名"""
    import random
    users = User.query.all()[:10]
    top_users = []

    for user in users:
        top_users.append({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'detections': random.randint(100, 1000),
            'fall_events': random.randint(0, 50),
            'risk_level': 'low' if random.random() > 0.3 else 'medium'
        })

    top_users.sort(key=lambda x: x['detections'], reverse=True)

    return jsonify({
        'success': True,
        'data': top_users
    }), 200'''

new_top_users = '''@app.route('/api/statistics/top-users', methods=['GET'])
def get_top_users():
    """获取活跃用户排名"""
    users = User.query.all()
    top_users = []

    for user in users:
        detections = DetectionRecord.query.filter_by(user_id=user.id).count()
        fall_events = DetectionRecord.query.filter_by(user_id=user.id, fall_detected=True).count()

        risk_level = 'low'
        if fall_events > 20:
            risk_level = 'high'
        elif fall_events > 10:
            risk_level = 'medium'

        top_users.append({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'detections': detections,
            'fall_events': fall_events,
            'risk_level': risk_level
        })

    top_users.sort(key=lambda x: x['detections'], reverse=True)
    top_users = top_users[:10]

    return jsonify({
        'success': True,
        'data': top_users
    }), 200'''

content = content.replace(old_top_users, new_top_users)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Statistics APIs fixed successfully!')