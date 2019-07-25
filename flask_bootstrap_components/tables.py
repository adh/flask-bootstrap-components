from flask import render_template
from markupsafe import Markup
from .markup import element

class Column(object):
    def __init__(self, 
                 name, 
                 options={},
                 convert=None,
                 data_proc=None,
                 content_map={},
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
        return data
    
    def get_cell_inner_html(self, row):
        res = self.get_cell_data(row)
        res = self.convert(res)

        try:
            if res in self.content_map:
                return self.content_map[res]
        except:
            pass
        
        return res

class CustomDataColumn(Column):
    def __init__(self, name, key, **kwargs):
        super(SequenceColumn, self).__init__(name, index=index, **kwargs)
        self.key = key
        self.id = str(index)

    def get_cell_data(self, row):
        return self.key(row)
    
class SequenceColumn(Column):
    def __init__(self, name, index, **kwargs):
        super(SequenceColumn, self).__init__(name, index=index, **kwargs)
        self.index = index
        self.id = str(index)
    def get_cell_data(self, row):
        return row[self.index]

class ObjectColumn(Column): 
    def __init__(self, name, attr, **kwargs):
        super(ObjectColumn, self).__init__(name, attr=attr, **kwargs)
        self.attr = attr
        self.id = attr
    def get_cell_data(self, row):
        r = row
        for i in self.attr.split('.'):
            r = getattr(r, i)
            if r is None:
                return None
        return r

class ObjectOrNoneColumn(ObjectColumn):
    def get_cell_data(self, row):
        try:
            return super(self, ObjectColumn).get_cell_data(row)
        except:
            return None
    
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
