from flask import render_template, request, url_for
from markupsafe import Markup
from .markup import element

DEFAULT_CONTENT_MAP = {
}

class Column(object):
    def __init__(self, 
                 name, 
                 options={},
                 convert=None,
                 data_proc=None,
                 content_map=DEFAULT_CONTENT_MAP,
                 **kwargs):
        self.name = name
        self.id = name
        self.header = Markup('<th scope="col">{0}</th>').format(name)
        self.filter = filter
        self._options = options
        if convert:
            self.convert = convert
        
        self.content_map = content_map
            
        if data_proc:
            self.get_cell_data = data_proc

    def get_cell_html(self, row):
        return element("td", {}, self.get_cell_inner_html(row))

    def convert(self, data):
        if data is True:
            return "\u2713"
        if data is False:
            return "\u2715"
        if data is None:
            return "\U0001f6ab"
        
        return data
    
    def get_cell_inner_html(self, row):
        res = self.get_cell_data(row)
        res = self.convert(res)

        if res in self.content_map:
            return self.content_map[res]
        
        return res

class CustomDataColumn(Column):
    def __init__(self, name, key, **kwargs):
        super().__init__(name, key=key, **kwargs)
        self.key = key
        self.id = str(id(key))

    def get_cell_data(self, row):
        return self.key(row)
    
class SequenceColumn(Column):
    def __init__(self, name, index, **kwargs):
        super(SequenceColumn, self).__init__(name, index=index, **kwargs)
        self.index = index
        self.id = str(index)
    def get_cell_data(self, row):
        return row[self.index]

def recursive_getattr(r, attr):
    for i in attr.split('.'):
        r = getattr(r, i)
        if r is None:
            return None
    return r
    
class ObjectColumn(Column): 
    def __init__(self, name, attr, **kwargs):
        super(ObjectColumn, self).__init__(name, attr=attr, **kwargs)
        self.attr = attr
        self.id = attr
    def get_cell_data(self, row):
        return recursive_getattr(row, self.attr)

class ObjectOrNoneColumn(ObjectColumn):
    def get_cell_data(self, row):
        try:
            return super(self, ObjectColumn).get_cell_data(row)
        except:
            return None

class LinkColumnMixin:
    def get_cell_inner_html(self, row):
        return Markup('<a href="{}">{}</a>').format(self.href(row),
                                                    super().get_cell_inner_html(row))
    
        
class ObjectLinkColumn(LinkColumnMixin, ObjectColumn):
    def __init__(self, name, attr, endpoint,
                 id_attr='id', id_arg='id', additional_args={}, **kwargs):
        super().__init__(name,
                         attr=attr,
                         id_attr=id_attr,
                         id_arg=id_arg,
                         **kwargs)
        self.id_attr = id_attr
        self.id_arg = id_arg
        self.endpoint = endpoint
        self.additional_args = additional_args

    def href(self, row):
        args = dict(self.additional_args)
        args[self.id_arg] = recursive_getattr(row, self.id_attr)
        return url_for(self.endpoint, **args)
    
        
class DescriptorColumn(Column):
    def __init__(self, name, descriptor, **kwargs):
        super(ObjectColumn, self).__init__(name, attr=attr, **kwargs)
        self.descriptor = descriptor
    def get_cell_data(self, row):
        return self.descriptor.fget(row)

class ColumnsMixin(object):
    def transform_columns(self, columns):
        return [i if isinstance(i, Column) else self.column_factory(i, 
                                                                    index=idx) 
                for idx, i in enumerate(columns)]

    def column_factory(self, i, index):
        return i

class BaseTable(ColumnsMixin):
    def __init__(self, 
                 columns, 
                 data,
                 classes=["table-striped"],
                 responsive=True,
                 **kwargs):

        self.columns = self.transform_columns(columns)
        self.data = self.transform_data(data)
        self.classes = classes
        self.responsive = responsive

    @property
    def extend_classes(self):
        if not self.classes:
            return ""
        else:
            return " "+" ".join(self.classes)
        
    def __html__(self):
        return Markup(render_template('flask_bootstrap_components/internal/table.html',
                                      table=self))
    
class TableRow(object):
    def __init__(self, data, columns):
        self.data = data
        self.columns = columns
    
    def get_row_contents(self):
        cols = []
        for i in self.columns:
            cols.append(i.get_cell_html(self.data))
        return Markup("").join(cols)

    def __html__(self):
        return element("tr", 
                       self.get_element_attrs(), 
                       self.get_row_contents())

    def get_element_attrs(self):
        classes = " ".join(self.get_element_classes())
        if classes:
            return {"class": classes}
        else:
            return {}

    def get_element_classes(self):
        return []


class SequenceColumnMixin(object):
    column_factory=SequenceColumn

class ObjectColumnMixin(object):
    column_factory=ObjectColumn

class IterableDataTable(BaseTable):
    def __init__(self, columns, data, row_factory=None,
                 **kwargs):
        if row_factory:
            self.row_factory = row_factory
        else:
            self.row_factory = TableRow
        super().__init__(columns, data, 
                         **kwargs)

    def transform_data(self, data):
        return [self.row_factory(i, self.columns) for i in data]

    @property
    def column_headers(self):
        return self.columns

class PlainTable(SequenceColumnMixin, IterableDataTable):
    pass
class ObjectTable(ObjectColumnMixin, IterableDataTable):
    pass

class PagedTable(PlainTable):
    def __init__(self, columns, data,
                 per_page=None,
                 cur_page=None,
                 per_page_options=[10, 50, 100],
                 anchor=None,
                 **kwargs):
        if not cur_page:
            cur_page = int(request.args.get("cur_page", "0"))
        if not per_page:
            per_page = int(request.args.get("per_page", per_page_options[0]))
        else:
            per_page_options = []

        self.anchor = anchor
        self.per_page = per_page
        self.cur_page = cur_page
        self.per_page_options = per_page_options

        data = data[self.cur_page*self.per_page:(self.cur_page+1)*self.per_page]

        self.has_next = len(data) == self.per_page
        
        super().__init__(columns, data, 
                         **kwargs)
    
    def __html__(self):
        return Markup(render_template('flask_bootstrap_components/internal/paged_table.html',
                                      table=self))

    def with_anchor(self, url):
        if self.anchor:
            return url + "#" + self.anchor
        else:
            return url
    
    def page_url(self, page):
        args = dict(request.args, **request.view_args)
        args["cur_page"] = page
        args["per_page"] = self.per_page
        return self.with_anchor(url_for(request.endpoint, **args))

    def per_page_url(self, per_page):
        args = dict(request.args, **request.view_args)
        page = int(self.cur_page / self.per_page * per_page)
        args["cur_page"] = page
        args["per_page"] = per_page
        return self.with_anchor(url_for(request.endpoint, **args))
    
