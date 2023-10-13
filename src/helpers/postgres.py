from src.core import OrderBy


def parse_order_by(model, order_by: OrderBy):
    asc = order_by.asc
    order_by = order_by.fields
    if isinstance(order_by, str):
        order_by = [order_by]
    if asc:
        return [model.__table__.c[col].asc() for col in order_by]
    else:
        return [model.__table__.c[col].desc() for col in order_by]


def parse_filter_by(model, filter_by: dict) -> list:
    filters = []
    for key, value in filter_by.items():
        if '.__in' in key:
            filters.append(model.__table__.c[key.split('.')[0]].in_(value))
            continue
        filters.append(model.__table__.c[key] == value)
    return filters
