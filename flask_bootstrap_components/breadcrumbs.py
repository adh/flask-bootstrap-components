from .utils import url_or_url_for
from .markup import element
from markupsafe import Markup

class Breadcrumb:
    __slots__ = ["name", "url"]

    def __init__(self, name, url=None, **kwargs):
        self.name = name
        if url is not None:
            self.url = url_or_url_for(url, **kwargs)
        else:
            self.url = None
            
    def __html__(self, title=None):
        name = self.name
        if name is None:
            name = title
        
        if self.url:
            return element("li",
                           {"class": "breadcrumb-item"},
                           element("a",
                                   {"href": self.url},
                                   name))
        else:
            return element("li",
                           {"class": "breadcrumb-item active"},
                           name)
    
class Breadcrumbs:
    def __init__(self):
        self.items = []

    def add(self, name, url=None, **kwargs):
        self.items.append(Breadcrumb(name, url, **kwargs))

    def __html__(self, title):
        ol = element("ol",
                     {"class": "breadcrumb py-0"},
                     Markup("").join(i.__html__(title)
                                     for i in self.items))
        return element("nav", {}, ol)
