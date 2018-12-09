import os
import logging
import sys
import traceback
from pathlib import Path

from flask import Flask, request, session, redirect, url_for, render_template, \
    g, Blueprint

from convert import convert_file, ConversionError
from db import db, User, Note
from server_helpers import authorized, render_title, flash_error, load_note, \
    flash_info
from users import register_user, auth_user, find_user

app = Flask(__name__)
prefix = Blueprint(
    'prefix', __name__, static_folder='static', template_folder='templates')


@prefix.before_request
def before_request():
    if 'uid' in session:
        g.user = db.query(User).filter(id=session['uid']).first()


@prefix.route('/')
def index():
    if 'user' in g:
        return redirect(url_for('.notes'))
    else:
        return render_template('index.html')


@prefix.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login = request.form.get('login')
        password = request.form.get('password')

        if login and password:
            user = find_user(login)
            if not user:
                user = register_user(login, password)

            if user and auth_user(user, password):
                session['uid'] = user.id
                return redirect(url_for('.notes'))

            flash_error('Неверный логин или пароль')

    return render_template('login.html')


@prefix.route('/logout')
def logout():
    del session['uid']
    return redirect(url_for('.index'))


@prefix.route('/notes')
@authorized
def notes():
    notes = db.query(Note).filter(owner_id=g.user.id).all()
    if not notes:
        flash_info('У вас ещё нет записей')
    return render_template('notes.html', notes=notes, render_title=render_title)


@prefix.route('/notes/<note_id>')
@load_note
@authorized
def note_view(note_id):
    if g.note.owner_id != g.user.id:
         return 'Доступ запрещён', 403
    return render_template('note.html', note=g.note, render_title=render_title)


@prefix.route('/notes/add', methods=['GET', 'POST'])
@authorized
def note_add():
    note = create_note()
    if request.method == 'GET' or not try_update_note(note):
        return render_template('edit.html', note=note, create_mode=True)
    db.add(note)
    note.save()
    return redirect(url_for('.note_view', note_id=note.id))


@prefix.route('/notes/import', methods=['POST'])
@authorized
def note_import():
    file = request.files.get('file')
    if not file or not file.filename:
        flash_error('Файл не найден')
        return redirect(url_for('.notes'))
    try:
        text = convert_file(file)
    except ConversionError as e:
        traceback.print_exception(*sys.exc_info())
        flash_error(str(e))
        return redirect(url_for('.notes'))
    note = create_note(title=os.path.splitext(file.filename)[0], text=text)
    return render_template('edit.html', note=note, create_mode=True)


@prefix.route('/notes/<note_id>/edit', methods=['GET', 'POST'])
@load_note
@authorized
def note_edit(note_id):
    if g.note.owner_id != g.user.id:
        return 'Доступ запрещён', 403
    if request.method == 'GET' or not try_update_note(g.note):
        return render_template('edit.html', note=g.note)
    g.note.save()
    return redirect(url_for('.note_view', note_id=g.note.id))


@prefix.route('/notes/<note_id>/remove', methods=['POST'])
@load_note
@authorized
def note_remove(note_id):
    if g.note.owner_id != g.user.id:
        return 'Доступ запрещён', 403
    db.remove(g.note)
    return redirect(url_for('.notes'))


def create_note(**fields):
    return Note(owner_id=g.user.id, **fields)


def try_update_note(note):
    title = request.form.get('title')
    text = request.form.get('text') or ''
    tags = [tag.strip() for tag in request.form.get('tags', "").split(",")]
    tags = [tag for tag in tags if tag]
    if not title:
        flash_error('Заголовок не должен быть пустым')
        return False
    note.title = title
    note.text = text
    note.tags = tags
    return True


def main():
    logging.basicConfig(filename='app.log', level=logging.DEBUG)
    secret_path = Path('./.flask_secret')
    try:
        secret_key = secret_path.read_bytes()
    except FileNotFoundError:
        secret_key = os.urandom(16)
        secret_path.write_bytes(secret_key)
    app.secret_key = secret_key

    app_prefix = Path('./.flask_prefix').read_text().strip()
    app.register_blueprint(prefix, url_prefix=app_prefix)

    db.load()
    app.run()


if __name__ == '__main__':
    main()
