import pandas as pd

from src.core import Table
from . import domain


class SheetService(pd.DataFrame):
    def __init__(self, data=None, index=None, columns=None, dtype=None, copy=None):
        super().__init__(data, index, columns, dtype, copy)

    @classmethod
    def from_table(cls, table: Table[domain.CellValue], rows=None, cols=None):
        if rows is None:
            rows = [domain.RowSindex(position=i) for i in range(0, len(table))]
        else:
            rows = [x.model_copy() for x in rows]
        if cols is None:
            cols = [domain.ColSindex(position=j) for j in range(0, len(table[0]))]
        else:
            cols = [x.model_copy() for x in cols]
        values = []
        for i, row in enumerate(table):
            if len(row) != len(cols):
                raise Exception
            cells = [domain.Cell(value=value, row=rows[i], col=cols[j]) for j, value in enumerate(row)]
            values.append(cells)
        return cls(data=values, index=rows, columns=cols)

    def to_simple_frame(self) -> pd.DataFrame:
        rows = [x.position for x in self.index]
        cols = [x.position for x in self.index]
        data = self.apply(lambda x: x.apply(lambda y: y.value)).values
        return pd.DataFrame(data, index=rows, columns=cols)

    def __add__(self, other):
        frame = super().__add__(other)
        return self.__class__(
            data=frame.values,
            index=frame.index,
            columns=frame.columns,
        )
