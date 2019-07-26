from .utils import url_or_url_for
from .buttons import link_button
from .markup import element
from markupsafe import Markup

class ToolbarButton(object):
    __slots__ = ["text", "endpoint", "context_class", "hint", "args",
                 "pass_args"]
    def __init__(self, text, endpoint, context_class="light", hint='',
                 args={}, pass_args=[]):
        self.text = text
        self.endpoint = endpoint
        self.context_class = context_class
        self.hint = hint
        self.args = args
        self.pass_args = pass_args 

    def render(self, toolbar, size, args={}):
        a = dict(self.args)
        for i in self.pass_args:
            a[i] = args[i]
            
        return link_button(url_or_url_for(self.endpoint,
                                          **a),
                           self.text,
                           self.context_class,
                           size,
                           self.hint)

class ToolbarSplitter(object):
    def render(self, toolbar, size, args={}):
        return Markup('</div><div class="btn-group" role="group">')
    
class Toolbar(object):
    def __init__(self, grouped=True, size=None, context_class="light"):
        self.buttons = []
        self.grouped = grouped
        self.size = size
        self.context_class = context_class

    def add_button(self, text, endpoint,
                   context_class=None, hint='', args={}):
        if context_class is None:
            context_class = self.context_class
        self.buttons.append(ToolbarButton(text, endpoint, context_class,
                                          hint=hint, args=args))

    def add_splitter(self):
        self.buttons.append(ToolbarSplitter())
        self.grouped = True

    def render(self, size, in_group=False, **kwargs):
        res = Markup("").join((i.render(self, size, **kwargs)
                               for i in self.buttons))

        if not in_group:
            if self.grouped:
                res = element("div", {"class": "btn-group"}, res)
                res = element("div", {"class": "btn-toolbar"}, res)
            else:
                res = element("div", {}, res)
            
        return res
        
    def __html__(self):
        return self.render(self.size)
        
    def prepend(self, content):
        return Markup("{}{}").format(self, content)
