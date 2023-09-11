from flask import render_template, request, url_for
from markupsafe import Markup
from .markup import element
from .component import Component, InteractiveComponent, StateSlot, IntStateSlot

DEFAULT_CONTENT_MAP = {
}

class Column(object):
    def __init__(self, 
                 name, 
                 options={},
                 convert=None,
                 data_proc=None,
                 content_map=DEFAULT_CONTENT_MAP,
                 td_attrs={},
                 **kwargs):
        self.name = name
        self.id = name
        if convert:
            self.convert = convert

        self.td_attrs = td_attrs
            
        self.content_map = content_map
            
        if data_proc:
            self.get_cell_data = data_proc

    def get_cell_html(self, row):
        return element("td", self.td_attrs, self.get_cell_inner_html(row))

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

    def get_header_html(self):
        return Markup('<th scope="col">{0}</th>').format(
            self.get_header_inner_html()
        )

    def get_header_inner_html(self):
        return self.name
    
    @property
    def header(self):
        return self.get_header_html()

    
class ColumnProxy(Column):
    def __init__(self, impl):
        self.impl = impl

    @property
    def name(self):
        return self.impl.name
    
    @property
    def id(self):
        return self.impl.id
    
    @property
    def td_attrs(self):
        return self.impl.td_attrs

    def get_cell_data(self, row):
        return self.impl.get_cell_data(row)

    def get_cell_html(self, row):
        return self.impl.get_cell_html(row)

    def get_header_html(self):
        return self.impl.get_header_html()

    def get_cell_inner_html(self, row):
        return self.impl.get_cell_html(row)

    def get_header_inner_html(self):
        return self.impl.get_header_html()

    
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

class FixedColumn(Column):
    def __init__(self, name, value, **kwargs):
        super().__init__(name, value=value, **kwargs)
        self.value = value
        self.id = name

    def get_cell_data(self, row):
        return self.value


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

class ObjectLinkColumnMixin(LinkColumnMixin):
    def __init__(self, name, endpoint,
                 id_attr='id', id_arg='id', additional_args={}, **kwargs):
        super().__init__(name,
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
    
        
class ObjectLinkColumn(ObjectLinkColumnMixin, ObjectColumn):
    def __init__(self, name, attr, **kwargs):
        super().__init__(name, attr=attr, **kwargs)

class FixedLinkColumn(ObjectLinkColumnMixin, FixedColumn):
    def __init__(self, name, value, **kwargs):
        super().__init__(name, value=value, **kwargs)

        
        
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

class BaseTable(ColumnsMixin, Component):
    def __init__(self, 
                 columns=None, 
                 data=None,
                 classes=["table-striped"],
                 responsive=True,
                 **kwargs):

        super().__init__(columns=columns,
                         data=data,
                         classes=classes,
                         responsive=responsive,
                         **kwargs)

        if columns is not None:
            self.set_columns(columns)
        else:
            self.columns = None

        if data is not None:
            self.set_data(data)
        else:
            self.data = None
            
        self.classes = classes
        self.responsive = responsive

    @property
    def extend_classes(self):
        if not self.classes:
            return ""
        else:
            return " "+" ".join(self.classes)

    def set_data(self, data):
        self.data = self.transform_data(data)        

    def set_columns(self, columns):
        self.columns = self.transform_columns(columns)        
        
    def __html__(self):
        if self.data is None:
            raise ValueError("No data set for table")
        if self.columns is None:
            raise ValueError("Table does not have column configuration")
        
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
    def __init__(self,
                 row_factory=None,
                 row_kwargs={},
                 **kwargs):
        if row_factory:
            self.row_factory = row_factory
        else:
            self.row_factory = TableRow
        self.row_kwargs = row_kwargs
        
        super().__init__(row_factory=row_factory,
                         row_kwargs=row_kwargs,
                         **kwargs)

    def transform_data(self, data):
        return [self.row_factory(i, self.columns,
                                 **self.row_kwargs)
                for i in data]

    @property
    def column_headers(self):
        return self.columns

class PlainTable(SequenceColumnMixin, IterableDataTable):
    # XXX: this thing is necessary to preserve backward compatibility with code
    # that expects SomethingTable constructor to take two positional arguments
    def __init__(self, 
                 columns=None, 
                 data=None,
                 **kwargs):
        super().__init__(columns=columns,
                         data=data,
                         **kwargs)
        
class ObjectTable(ObjectColumnMixin, IterableDataTable):
    # XXX: this thing is necessary to preserve backward compatibility with code
    # that expects SomethingTable constructor to take two positional arguments
    def __init__(self, 
                 columns=None, 
                 data=None,
                 **kwargs):
        super().__init__(columns=columns,
                         data=data,
                         **kwargs)

class GroupHeaderRow(TableRow):
    def __init__(self, data, columns, content_accessor):
        self.data = data
        self.columns = columns
        self.content_accessor = content_accessor

    def get_content_html(self):
        return self.content_accessor(self.data)
        
    def __html__(self):
        header = super().__html__()
        return (
            Markup('{}<tr><td colspan="{}">{}</td></tr>')
            .format(header, len(self.columns),
                    self.get_content_html())
        )

class GroupHeaderTable(PlainTable):
    def __init__(self, columns, data, content_accessor,
                 row_factory=None, **kwargs):
        if row_factory is None:
            row_factory = GroupHeaderRow
        super().__init__(columns, data, row_factory=row_factory,
                         row_kwargs={"content_accessor": content_accessor},
                         **kwargs)

class PagedTable(PlainTable, InteractiveComponent):

    per_page = IntStateSlot(100)
    cur_page = IntStateSlot(0)
    
    def __init__(self,
                 columns=None,
                 data=None,
                 per_page_options=[10, 50, 100],
                 anchor=None, # For backward compatibility
                 name=None,
                 **kwargs):
        
        if anchor is not None: 
            name = anchor

        self.per_page_options = per_page_options
            
        super().__init__(columns=columns,
                         data=None,
                         per_page_options=per_page_options,
                         name=name,
                         state_defaults=self.defaults_from_kwargs(**kwargs),
                         **kwargs)

        if data is not None:
            self.set_data(data)

    def set_data(self, data):
        data = data[self.cur_page*self.per_page
                    : (self.cur_page+1)*self.per_page]
        self.has_next = len(data) == self.per_page
        super().set_data(data)
        
    def __html__(self):
        return Markup(render_template('flask_bootstrap_components/internal/paged_table.html',
                                      table=self))
        
    def page_url(self, page):
        return self.build_url(cur_page=page)

    def per_page_url(self, per_page):
        page = int(self.cur_page * self.per_page / per_page)
        return self.build_url(cur_page=page,
                              per_page=per_page)
    
