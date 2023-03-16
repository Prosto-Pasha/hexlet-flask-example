from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    get_flashed_messages,
    make_response,
    session,
)  # Jinja2
import json
from pathlib import Path


app = Flask(__name__)
app.config['SECRET_KEY'] = 'SECRET_KEY'


@app.route('/')
def main():
    errors = {}
    login = ''
    return render_template(
        'users/start_page.html',
        errors=errors,
        login=login
    )


@app.post('/')
def auth_post():
    args = request.form.to_dict()
    session['login'] = args['login']
    response = make_response(redirect(url_for('users_get'), code=302))
    return response


@app.route('/logout')
def logout():
    session.pop('login', None)
    return redirect(url_for('main'))


@app.route('/users/<id>')
def users(id):
    all_users = get_users()
    user = next(
        filter(
            lambda x: x['id'] == id,
            all_users
        ),
        None
    )
    if not user:
        return 'User not found', 404
    return render_template(
        'users/show.html',
        user=user,
    )


@app.get('/users')
def users_get():
    check_login()
    messages = get_flashed_messages(with_categories=True)
    term = request.args.get('term')
    if term is None:
        term = ''
    term = term.strip()
    filtered_users = get_users()
    if term:
        filtered_users = list(
            filter(
                lambda x: x['name'].find(term) != -1,
                filtered_users
            )
        )
    return render_template(
        'users/index.html',
        users=filtered_users,
        search=term,
        messages=messages,
    )


@app.post('/users')
def users_post():
    user = request.form.to_dict()
    errors = validate(user)
    if errors:
        return render_template(
            'users/new.html',
            user=user,
            errors=errors,
        )
    all_users = get_users()
    user['id'] = str(get_new_id())
    all_users.append(user)
    encoded_users = json.dumps(all_users)
    response = make_response(redirect(url_for('users_get'), code=302))
    response.set_cookie('users', encoded_users)
    flash('User was added successfully', 'success')
    return response


@app.route('/users/new')
def users_new():
    user = {'name': '', 'email': '',}
    errors = {}
    return render_template(
        'users/new.html',
        user=user,
        errors=errors
    )


@app.route('/users/<id>/edit')
def edit_user(id):
    all_users = get_users()
    user = next(filter(lambda x: x['id'] == id, all_users), None)
    errors = []
    return render_template(
           'users/edit.html',
           user=user,
           errors=errors,
    )


@app.route('/users/<id>/delete', methods=['POST'])
def delete_user(id):
    all_users = get_users()
    user = next(filter(lambda x: x['id'] == id, all_users), None)
    if user:
        all_users.remove(user)
        encoded_users = json.dumps(all_users)
        response = make_response(redirect(url_for('users_get'), code=302))
        response.set_cookie('users', encoded_users)
        flash('User was deleted successfully', 'success')
        return response
    return 'Error!', 404


@app.route('/users/<id>/patch', methods=['POST'])
def patch_user(id):
    data = request.form.to_dict()
    errors = validate(data)
    if errors:
        return render_template(
            'users/edit.html',
            user=data,
            errors=errors,
        ), 422
    all_users = get_users()
    old_user = next(filter(lambda x: x['id'] == id, all_users), None)
    user_index = all_users.index(old_user)
    if old_user:
        all_users[user_index]['id'] = id
        all_users[user_index]['name'] = data['name']
        all_users[user_index]['email'] = data['email']
        encoded_users = json.dumps(all_users)
        response = make_response(redirect(url_for('users_get'), code=302))
        response.set_cookie('users', encoded_users)
        flash('User was updated successfully', 'success')
        return response
    return 'Error!', 404


def check_login():
    if 'login' in session:
        username = session['login']
        flash(f'Logged in as {username}', 'success')
    else:
        flash('You are not logged in', 'error')


def is_double(user):
    all_users = get_users()
    f_user = list(
        filter(
            lambda x: x['name'] == user.get('name', '') and
                      x['email'] == user.get('email', ''),
            all_users
        )
    )
    return bool(f_user)


def validate(user):
    errors = {}
    double = is_double(user)
    if not user['name']:
        errors['name'] = "Nickname can't be blank"
    elif len(user['name']) < 5:
        errors['name'] = "Nickname must be grater than 4 characters"
    elif double:
        errors['name'] = "This nickname is already taken"
    if not user['email']:
        errors['email'] = "Email can't be blank"
    elif double:
        errors['email'] = "This email is already taken"
    return errors


def get_users():
    all_users = json.loads(request.cookies.get('users', json.dumps([])))
    return all_users


def get_new_id():
    all_users = get_users()
    if all_users:
        return max(map(lambda x: int(x['id']), all_users)) + 1
    return 1


if __name__ == '__main__':
    main()