from datetime import datetime


def _get_field(model_cls, name):
    return model_cls.model_fields[name]


def test_reservation_starts_at_is_datetime():
    from models.reservation import Reservation
    field = _get_field(Reservation, "starts_at")
    assert field.annotation is datetime, (
        f"Reservation.starts_at must be datetime, got {field.annotation}"
    )


def test_reservation_ends_at_is_datetime():
    from models.reservation import Reservation
    field = _get_field(Reservation, "ends_at")
    assert field.annotation is datetime


def test_table_type_capacity_is_int():
    from models.table_type import TableType
    field = _get_field(TableType, "capacity")
    assert field.annotation is int, (
        f"TableType.capacity must be int, got {field.annotation}"
    )


def test_menu_item_foreign_key_points_to_menu_table():
    from models.menu_item import MenuItem
    table = MenuItem.__table__
    fk = next(iter(table.c.menu_id.foreign_keys))
    assert fk.target_fullname == "content.menu.id", (
        f"MenuItem.menu_id must reference content.menu.id, got {fk.target_fullname}"
    )


def test_reservation_foreign_keys_resolve():
    from models.reservation import Reservation
    table = Reservation.__table__
    rest_fk = next(iter(table.c.restaurant_id.foreign_keys))
    tt_fk = next(iter(table.c.table_type_id.foreign_keys))
    assert rest_fk.target_fullname == "content.restaurant.id"
    assert tt_fk.target_fullname == "content.table_type.id"
