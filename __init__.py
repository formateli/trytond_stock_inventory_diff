# This file is part of trytond-stock_inventory_diff module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.

from trytond.pool import Pool
from .inventory import *

def register():
    Pool.register(
        InventoryLine,
        module='stock_inventory_diff', type_='model')
