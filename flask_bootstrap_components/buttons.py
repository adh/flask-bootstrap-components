from .markup import element

def button(text, classes="", context_class="default", size=None, attrs={}, type="button"):
    cls = "btn btn-"+context_class
    if size:
        cls += " btn-" + size
    a = {"class": cls + " " + classes, 
         "type": type}
    a.update(attrs)
    return element("button", 
                   a,
                   text)

def link_button(url, text, context_class="default", size=None, hint=None, link_target=None):
    cls = "btn btn-"+context_class
    if size:
        cls += " btn-" + size
    return element("a", 
                   {"class": cls, "role": "button", "href": url, "title": hint, "target": link_target},
                   text)

def form_button(url, text, classes="", context_class="default", size=None, attrs={}):
    return element("form",
                   {"method": "POST",
                    "action": url},
                   button(text, classes=classes, context_class=context_class,
                          size=size, attrs=attrs, type="submit"))
