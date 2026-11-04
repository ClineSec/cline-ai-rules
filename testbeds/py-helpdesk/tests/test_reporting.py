from helpdesk.reporting import SORT_ORDERS, strip_fences


def test_strip_fences_removes_markdown_wrapper():
    assert strip_fences("```sql\nSELECT id FROM tickets\n```") == "SELECT id FROM tickets"


def test_strip_fences_leaves_plain_sql():
    assert strip_fences("SELECT count(*) FROM queues") == "SELECT count(*) FROM queues"


def test_every_sort_order_is_a_column_list():
    assert all(order.split()[0].isidentifier() for order in SORT_ORDERS.values())
