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
from werkzeug.local import LocalProxy

class Component:
    def __init__(self, name=None, parent=None, **kwargs):
        self.children = []
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
            self.parent.add_child(self)
        else:
            self.name_prefix = name

    def add_child(self, child):
        self.children.append(child)

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

class BooleanStateSlot(StateSlot):
    def load_value(self, value):
        return value == "1"
    def dump_value(self, value):
        return "1" if value else "0"
    
class RequestStateTracker:
    def __init__(self):
        self.dirty_set = set()

    @classmethod
    def get_instance(cls):
        ctx = _app_ctx_stack.top
        if ctx is not None:
            if not hasattr(ctx, 'fbc_request_state_tracker'):
                ctx.fbc_request_state_tracker = cls()
            return ctx.fbc_request_state_tracker

    def mark_changed(self, state):
        self.dirty_set.add(state)

request_state_tracker = LocalProxy(RequestStateTracker.get_instance)
        
class InteractiveComponentState:
    def __init__(self, component, slots, name_prefix, defaults={}):
        self.component = component
        self.name_prefix = name_prefix
        self.state = {}
        self.changed = set()
        for i in slots:
            arg = self.get_argument(i.name, None)
            if arg is not None:
                self.set_value(i, i.load_value(arg))
                
            elif i.name in defaults:
                # When setting from defaults we dont want to mark slot/state
                # as changed
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

        if not self.changed:
            request_state_tracker.mark_changed(self)
    
        self.changed.add(slot)

    def update_slot_values(self, args, overide=set()):
        for slot, value in self.state.items():
            if slot.name in overide:
                value = overide[slot.name]
            elif slot not in self.changed:
                continue

            name = self.convert_argument_name(slot.name)
            args[name] = slot.dump_value(value)
            print(name, value)

        for i in self.component.interactive_children:
            i.state.update_slot_values(args)


    def build_url(self, **kwargs):
        args = dict(request.args, **request.view_args)

        self.update_slot_values(args, overide=kwargs)
            
        print(args)

        return url_for(request.endpoint, **args)
            
class InteractiveComponentMetaClass(type):
    def __init__(cls, name, bases, attrs):
        super().__init__(name, bases, attrs)
        
        if not hasattr(cls, "_state_slots"):
            cls._state_slots = []
        else:
            cls._state_slots = list(cls._state_slots)
            
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

    @property
    def interactive_children(self):
        return [
            i for i in self.children if isinstance(i, InteractiveComponent)
        ]

    def init_state(self, defaults={}):
        self.state = InteractiveComponentState(
            self,
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
    

