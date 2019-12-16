from datetime import datetime
from flask import render_template, redirect, url_for, request, g, jsonify, current_app, send_file
from app import db
from app.models import User, Post
from app.main import bp
from sqlalchemy import desc
import json


@bp.route('/index')
def index():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(desc('timestamp')).paginate(
        page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.index', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('main.index', page=posts.prev_num) \
        if posts.has_prev else None
    return render_template('index.html', title='Home', posts=posts.items, next_url=next_url, prev_url=prev_url)


@bp.route('/')
@bp.route('/about')
def about():
    return render_template('about.html')


@bp.route('/user/<username>')
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    posts = user.posts.order_by(Post.timestamp.desc()).paginate(
        page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.user', username=user.username,
                       page=posts.next_num) if posts.has_next else None
    prev_url = url_for('main.user', username=user.username,
                       page=posts.prev_num) if posts.has_prev else None
    return render_template('user.html', user=user, posts=posts.items,
                           next_url=next_url, prev_url=prev_url)


@bp.route('/user/<username>/popup')
def user_popup(username):
    user = User.query.filter_by(username=username).first_or_404()
    return render_template('user_popup.html', user=user)


@bp.route('/export/<filename>', methods=['GET'])
def export(filename):
    return send_file('static/outputs/' + filename, attachment_filename=filename, as_attachment=True)
    



@bp.route('/download', methods=['GET', 'POST'])
def download():
    if request.method == 'POST':
        data = json.loads(request.get_data())
        start = int(data['from'].split('T')[0].replace('-', ''))
        end = int(data['to'].split('T')[0].replace('-', ''))
        user_types = [int(user_type) for user_type in data['type']]
        
        posts = Post.query.filter(Post.user_id.in_(user_types)).all()
        return_posts = []
        for post in posts:
            post_point = int(post.timestamp.strftime("%Y-%m-%d").replace('-', ''))
            if start <= post_point and post_point <= end:
                return_posts.append(post.to_dict())
        
        if data['action'] == 'preview':
            if len(return_posts) <= 5:
                return jsonify(return_posts)
            else:
                return jsonify(return_posts[:5])
        else:
            type_map = ['APP', 'HOST', 'PARTITION']
            file_name = datetime.utcnow().strftime("%Y-%m-%dat%H-%M-%S") + '-output.xls'
            wbk = xlwt.Workbook()
            sheet = wbk.add_sheet('Sheet1', cell_overwrite_ok=True)
            sheet.write(0, 0, 'UTC DateTime')
            sheet.write(0, 1, 'Type')
            sheet.write(0, 2, 'Alert Info')
            for i in range(len(return_posts)):
                sheet.write(i + 1, 0, return_posts[i]['timestamp'].strftime("%Y-%m-%d"))                
                sheet.write(i + 1, 1, type_map[return_posts[i]['user_id'] - 1])
                sheet.write(i + 1, 2, return_posts[i]['body'])
            wbk.save('app/static/outputs/' + file_name)
            
            return 'export/' + file_name
    return render_template('download.html')