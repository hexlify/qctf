from functools import wraps
from html import escape

from flask import g, redirect, url_for, render_template_string, flash

from db import db, Note


def authorized(handler):
    @wraps(handler)
    def wrapper(*args, **kwargs):
        if 'user' not in g:
            return redirect(url_for('.login'))
        return handler(*args, **kwargs)

    return wrapper


def load_note(handler):
    @wraps(handler)
    def wrapper(note_id, **kwargs):
        note = db.query(Note).filter(id=int(note_id)).first()
        if not note:
            return 'Запись не найдена', 404
        g.note = note
        return handler(note_id, **kwargs)

    return wrapper


def render_title(note):
    template = escape(note.title) + '''
    {% for tag in note.tags %}
        <span class="tag is-light">{{tag}}</span>
    {% endfor %}
    '''
    return render_template_string(template, note=note)


def flash_error(message):
    flash(message, 'danger')


def flash_info(message):
    flash(message, 'info')


def flash_success(message):
    flash(message, 'success')
