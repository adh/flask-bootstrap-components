import base64
from hashlib import sha256
import hmac
import time
import os
from flask import current_app, session, request
import json

def get_session_id():
    if "__fbc_csrf" not in session:
        session["__fbc_csrf"] = os.urandom(16)

    return session["__fbc_csrf"]

def get_scoped_auth_key(scope, include_request_endpoint=True):
    if include_request_endpoint:
        scope += "\n" + request.endpoint

    scope += "\n" + current_app.secret_key
        
    d = hmac.new(get_session_id(), scope.encode("utf-8"), sha256).digest()
    
    return base64.b64encode(d[:18]).decode('ascii')
