def migrate(cr, version):
    cr.execute("UPDATE loyalty_card SET points = 0")
