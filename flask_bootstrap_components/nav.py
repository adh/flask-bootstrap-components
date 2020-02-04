from markupsafe import Markup
from fnmatch import fnmatchcase
from flask import request
from .markup import *
from .utils import url_or_url_for

class NavItem:
    __slots__ = ["label", "target", "args", "preserve_args",
                 "subendpoint_pattern"]

    def __init__(self, label, target,
                 args={},
                 preserve_args=[],
                 subendpoints=False,
                 subendpoint_pattern=None):
        self.label = label
        self.target = target
        self.args = args
        self.preserve_args = preserve_args
        if subendpoints:
            subendpoint_pattern = target + "*"
        self.subendpoint_pattern = subendpoint_pattern
        
    @property
    def is_active(self):
        if request.endpoint == self.target:
            return True

        if self.subendpoint_pattern:
            return fnmatchcase(request.endpoint, self.subendpoint_pattern)

        return False

    @property
    def url(self):
        params = self.args.copy()
        for i in self.preserve_args:
            params[i] = request.view_args[i]
        
        return url_or_url_for(self.target, **params)
    
    @property
    def a_attrs(self):
        klasses = ["nav-link"]

        if self.is_active:
            klasses.append("active")

        return {'href': self.url, "class": " ".join(klasses)}

    @property
    def li_attrs(self):
        return {"class": "nav-item"}
    
    def __html__(self):
        link = element('a',
                       self.a_attrs,
                       self.label)
        return element('li', self.li_attrs, link)
        
class Nav:
    item_class = NavItem
    
    def __init__(self, preserve_args=[]):
        self.items = []
        self.preserve_args = preserve_args
        
    def add_item(self, item):
        self.items.append(item)
        
    def add(self, label, target, preserve_args=None, **kwargs):
        if preserve_args is None:
            preserve_args = self.preserve_args
            
        self.add_item(self.item_class(label,
                                      target,
                                      preserve_args=preserve_args,
                                      **kwargs))

    @property
    def ul_attrs(self):
        return {"class": "nav"}
        
    def __html__(self):
        return element('ul', self.ul_attrs,
                       Markup("").join(self.items))

class NavTabs(Nav):
    @property
    def ul_attrs(self):
        return {"class": "nav nav-tabs"}

class NavPills(Nav):
    @property
    def ul_attrs(self):
        return {"class": "nav nav-pills"}
    
