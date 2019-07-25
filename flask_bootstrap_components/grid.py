from .markup import element

class GridColumn:
    __slots__ = ["widths"]
    def __init__(self, width=3, **widths):
        if not widths:
            widths = {"md": width}
            
        self.widths = widths

    def get_class(self):
        return " ".join(["col-{}-{}".format(k, v)
                         for k, v in self.widths.items()])
        
    def render(self, content):
        return element("div", {"class": self.get_class()}, content)
