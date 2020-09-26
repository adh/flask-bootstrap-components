from flask import (
    render_template,
    request,
    url_for,
    abort,
    redirect,
    current_app,
)
from markupsafe import Markup
from .markup import element
from .csrf import get_scoped_auth_key
from .base import get_extension_object

class Component:
    def __init__(self, name=None, parent=None, **kwargs):
        if name is None:
            name = get_extension_object().generate_default_name(
                self.__class__.__name__
            )
            
        self.name = name
        self.parent = parent
        self.name_prefix = None
        if self.parent:
            self.name_prefix = "{}__{}".format(self.parent.name_prefix,
                                               self.name)
        else:
            self.name_prefix = name

    def render_template(self, name, **kwargs):
        return Markup(render_template(name, **kwargs))

    def field_name(self, name):
        return "{}__{}".format(self.name_prefix, name)
        
class SlotDescriptor:
    __slots__ = ["slot"]

    def __init__(self, slot):
        self.slot = slot

    def __get__(self, obj, owner=None):
        return self.slot.get_value(obj)

    def __set__(self, obj, value):
        self.slot.set_value(obj, value)
        
class StateSlot:
    def __init__(self, default=None, name=None):
        self.name = name
        self.default = default
        
    def get_value(self, obj):
        if obj is None:
            return self.default

        return obj.state.get_value(self)
        
    def set_value(self, obj, value):
        return obj.state.set_value(self, value)

    def set_name(self, name):
        if self.name is None:
            self.name = name

    def load_value(self, value):
        return value

    def dump_value(self, value):
        return str(value)

    def get_descriptor(self):
        return SlotDescriptor(self)
    
class IntStateSlot(StateSlot):
    def load_value(self, value):
        return int(value)
    
class InteractiveComponentState:
    def __init__(self, slots, name_prefix, defaults={}):
        self.name_prefix = name_prefix
        self.state = {}
        self.changed = set()
        for i in slots:
            arg = self.get_argument(i.name, None)
            if arg is not None:
                self.state[i] = i.load_value(arg)
                self.changed.add(i)
            elif i.name in defaults:
                self.state[i] = defaults[i.name]
            else:
                self.state[i] = i.default
                    
                
    def convert_argument_name(self, name):
        return "{}__{}".format(self.name_prefix, name)

    def get_argument(self, name, default=None):
        return request.args.get(self.convert_argument_name(name),
                                default)

    def get_value(self, slot):
        return self.state[slot]
    
    def set_value(self, slot, value):
        self.state[slot] = value
        self.changed.add(slot)
        
    def build_url(self, **kwargs):
        args = dict(request.args, **request.view_args)

        for slot, value in self.state.items():
            if slot.name in kwargs:
                value = kwargs[slot.name]
            elif slot not in self.changed:
                continue
            
            name = self.convert_argument_name(slot.name)
            args[name] = slot.dump_value(value)
            
        return url_for(request.endpoint, **args)
            
class InteractiveComponentMetaClass(type):
    def __init__(cls, name, bases, attrs):
        super().__init__(name, bases, attrs)
        cls._state_slots = []
        for name in dir(cls):
            if name.startswith('_'):
                continue

            value = getattr(cls, name)
            if not isinstance(value, StateSlot):
                continue
            
            value.set_name(name)
                
            cls._state_slots.append(value)
            setattr(cls, name, value.get_descriptor())
            
            
class InteractiveComponent(Component, metaclass=InteractiveComponentMetaClass):
    def __init__(self,
                 state_defaults={},
                 **kwargs):
        super().__init__(**kwargs)
        self.init_state(defaults=state_defaults)

    @classmethod
    def defaults_from_kwargs(cls, **kwargs):
        res = {}
        
        for i in cls._state_slots:
            v = kwargs.get(i.name)
            if v is not None:
                res[i.name] = v

        return res
        
    def init_state(self, defaults={}):
        self.state = InteractiveComponentState(
            self._state_slots,
            self.name_prefix,
            defaults=defaults
        )
        
    def url_with_anchor(self, url):
        if self.name_prefix:
            return url + "#" + self.name_prefix
        else:
            return url

    def build_url(self, **kwargs):
        return self.url_with_anchor(self.state.build_url(**kwargs))
    

class FormProcessingComponent(InteractiveComponent):
    def process(self):
        pass
    
class FormComponent(InteractiveComponent):
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
