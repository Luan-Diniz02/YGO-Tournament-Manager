import hmac
import os
import secrets
from urllib.parse import urljoin, urlparse

from flask import flash, redirect, request, session, url_for

_CSRF_SESSION_KEY = '_csrf_token'
_CSRF_FORM_KEY = '_csrf_token'


def _valid_session_secret(secret_key):
    return bool(secret_key and secret_key.strip())


def _generate_csrf_token():
    token = session.get(_CSRF_SESSION_KEY)
    if not token:
        token = secrets.token_urlsafe(32)
        session[_CSRF_SESSION_KEY] = token
    return token


def validate_csrf_token(session_token, request_token):
    if not session_token or not request_token:
        return False
    return hmac.compare_digest(str(session_token), str(request_token))


def is_safe_redirect_target(target):
    if not target:
        return False

    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc


def _request_csrf_token():
    return request.form.get(_CSRF_FORM_KEY) or request.headers.get('X-CSRF-Token')


def _csrf_exempt():
    endpoint = request.endpoint or ''
    return endpoint == 'static'


def _enforce_csrf():
    if request.method not in ('POST', 'PUT', 'PATCH', 'DELETE'):
        return None

    if _csrf_exempt():
        return None

    session_token = session.get(_CSRF_SESSION_KEY)
    request_token = _request_csrf_token()

    if validate_csrf_token(session_token, request_token):
        return None

    flash('Sessão inválida ou expirada. Tente novamente.', 'error')
    return redirect(request.referrer or url_for('index'))


def configure_security(app):
    secret_key = os.getenv('FLASK_SECRET_KEY', '').strip()
    if not _valid_session_secret(secret_key):
        raise RuntimeError('FLASK_SECRET_KEY nao configurada. Defina a variavel de ambiente antes de iniciar a aplicacao.')

    app.secret_key = secret_key

    @app.context_processor
    def inject_csrf_token():
        return {'csrf_token': _generate_csrf_token}

    @app.before_request
    def csrf_protect():
        return _enforce_csrf()

    return app
