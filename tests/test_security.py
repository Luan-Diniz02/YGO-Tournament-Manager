from flask import Flask

from web.security import is_safe_redirect_target, validate_csrf_token


def test_validate_csrf_token_com_tokens_iguais_retorna_true():
    assert validate_csrf_token('abc123', 'abc123') is True


def test_validate_csrf_token_com_tokens_diferentes_retorna_false():
    assert validate_csrf_token('abc123', 'xyz999') is False


def test_validate_csrf_token_sem_tokens_retorna_false():
    assert validate_csrf_token('', 'abc123') is False
    assert validate_csrf_token('abc123', '') is False


def test_is_safe_redirect_target_permite_path_relativo():
    app = Flask(__name__)
    with app.test_request_context('/', base_url='https://liga-ygo.com'):
        assert is_safe_redirect_target('/dashboard') is True


def test_is_safe_redirect_target_bloqueia_dominio_externo():
    app = Flask(__name__)
    with app.test_request_context('/', base_url='https://liga-ygo.com'):
        assert is_safe_redirect_target('https://evil.example/phishing') is False
