import os
from functools import wraps

from flask import flash, redirect, request, session, url_for


def admin_esta_logado():
    return session.get('is_admin', False)


def obter_ip_cliente():
    forwarded_for = request.headers.get('X-Forwarded-For', '').strip()
    if forwarded_for:
        return forwarded_for.split(',')[0].strip()
    return (request.remote_addr or '').strip()


def ip_admin_permitido():
    ips_permitidos = os.getenv('ADMIN_ALLOWED_IPS', '').strip()
    if not ips_permitidos:
        return True

    cliente_ip = obter_ip_cliente()
    allowlist = {ip.strip() for ip in ips_permitidos.split(',') if ip.strip()}
    return cliente_ip in allowlist


def admin_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not ip_admin_permitido():
            flash('Acesso administrativo bloqueado para este IP.', 'error')
            return redirect(url_for('index'))

        if admin_esta_logado():
            return func(*args, **kwargs)

        flash('Acesso restrito ao administrador. Faça login para continuar.', 'error')
        return redirect(url_for('admin_login', next=request.path))

    return wrapper


def inject_auth_context():
    return {
        'is_admin': admin_esta_logado(),
    }
