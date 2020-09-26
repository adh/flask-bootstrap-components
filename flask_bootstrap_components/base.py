from flask import current_app, Blueprint, url_for, _app_ctx_stack
from collections import defaultdict

class FlaskBootstrapComponents:
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        self.app = app
        if not hasattr(app, 'extensions'):
            app.extensions = {}
        app.extensions['flask_bootstrap_components'] = self

        bp = Blueprint('flask_bootstrap_components', __name__, 
                       template_folder='templates')
        app.register_blueprint(bp)

    def generate_default_name(self, name):
        ctx = _app_ctx_stack.top
        if ctx is not None:
            if not hasattr(ctx, 'fbc_name_counter_map'):
                ctx.fbc_name_counter_map = defaultdict(lambda: 0)

            ctx.fbc_name_counter_map[name] += 1
            
            return "{}{}".format(name, ctx.fbc_name_counter_map[name])
        return name

def get_extension_object():
    return current_app.extensions['flask_bootstrap_components']
