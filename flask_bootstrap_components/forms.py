from flask import (
    render_template,
    request,
    url_for,
    abort,
    redirect,
    current_app,
    _app_ctx_stack,
)
from markupsafe import Markup
from .markup import element
from .csrf import get_scoped_auth_key
from .base import get_extension_object
from .component import InteractiveComponent

class FormComponent(InteractiveComponent):
    def process(self):
        pass
    
class Form(FormComponent):
    def __init__(self, **kwargs):
        self.process_on_submit_called = False
        super().__init__(**kwargs)
    
    def process_on_submit(self):
        if self.process_on_submit_called:
            return
        
        self.process_on_submit_called = True

        if request.method != 'POST':
            return

        if self.trigger_field_name not in request.form:
            return

        if not self.validate_trigger_field():
            self.handle_invalid_csrf_token()

            
        self.process()
        self.commit()

    def handle_invalid_csrf_token(self):
        abort(400)

    def process(self):
        pass
        
    @property
    def trigger_field_name(self):
        return '__{}__'.format(self.name_prefix)

    @property
    def trigger_field_value(self):
        return get_scoped_auth_key(self.name_prefix)
    
    @property
    def hidden_trigger_field(self):
        return Markup('<input type="hidden" name="{}" value="{}">').format(
            self.trigger_field_name,
            self.trigger_field_value
        )

    def validate_trigger_field(self):
        return request.form[self.trigger_field_name] == self.trigger_field_value
    
    def commit(self, **kwargs):
        abort(redirect(self.build_url(**kwargs)))

    def __html__(self):
        self.process_on_submit()
        return element("form",
                       {"method": "post"},
                       Markup("{}{}").format(self.hidden_trigger_field,
                                             self.form_body()))
