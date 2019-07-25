from flask import current_app, Blueprint, url_for

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

