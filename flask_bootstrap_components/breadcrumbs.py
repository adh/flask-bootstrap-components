from .utils import url_or_url_for
from .markup import element
from markupsafe import Markup

class Breadcrumb:
    __slots__ = ["name", "url", "kwargs"]

    def __init__(self, name, url=None, **kwargs):
        self.name = name
        self.url = url
        self.kwargs = kwargs

    @property
    def href(self):
        if self.url is None:
            return None
        
        return url_or_url_for(self.url, **self.kwargs)        
            
    def __html__(self, title=None):
        name = self.name
        if name is None:
            name = title

        href = self.href
            
        if href:
            return element("li",
                           {"class": "breadcrumb-item"},
                           element("a",
                                   {"href": href},
                                   name))
        else:
            return element("li",
                           {"class": "breadcrumb-item active"},
                           name)
    
class Breadcrumbs:
    def __init__(self, extend=None):
        self.items = []
        if extend:
            self.items += extend.items

    def extend(self):
        return type(self)(extend=self)
            
    def add(self, name, url=None, **kwargs):
        self.items.append(Breadcrumb(name, url, **kwargs))

    def __html__(self, title):
        ol = element("ol",
                     {"class": "breadcrumb py-0"},
                     Markup("").join(i.__html__(title)
                                     for i in self.items))
        return element("nav", {}, ol)
