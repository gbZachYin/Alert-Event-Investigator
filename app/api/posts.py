from app.api import bp
from flask import jsonify, request, url_for
from app.models import Post
from app import db
from app.api.errors import bad_request

@bp.route('/posts/<int:id>', methods=['GET'])
def get_post(id):
    return jsonify(Post.query.get_or_404(id).to_dict())

@bp.route('/posts', methods=['GET'])
def get_posts():
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 100)
    data = Post.to_collection_dict(Post.query, page, per_page, 'api.get_posts')
    return jsonify(data)


@bp.route('/posts/<int:id>', methods=['PUT'])
def update_post(id):
    post = Post.query.get_or_404(id)
    data = request.get_json() or {}
    if 'user_id' not in data:
        return bad_request('must include user id')
    post.from_dict(data)
    db.session.commit()
    return jsonify(post.to_dict())

@bp.route('/posts', methods=['POST'])
def create_post():
    data = request.get_json() or {}
    if 'user_id' not in data:
        return bad_request('must include user id')
    post = Post()
    post.from_dict(data)
    db.session.add(post)
    db.session.commit()
    response = jsonify(post.to_dict())
    response.status_code = 201
    response.headers['Location'] = url_for('api.get_post', id=post.id)
    return response