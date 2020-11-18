# This file is part of trytond-stock_inventory_diff module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.

from trytond.pool import PoolMeta
from trytond.model import fields
from trytond.pyson import Eval
from trytond.transaction import Transaction
from trytond.pool import Pool

__all__ = ['InventoryLine']


class InventoryLine(metaclass=PoolMeta):
    __name__ = 'stock.inventory.line'

    diff_quantity = fields.Function(
        fields.Float(
            'Diff', digits=(16, Eval('unit_digits', 2)),
            depends=['unit_digits']),
            'get_diff_quantity')

    @fields.depends('product', 'quantity', 'expected_quantity')
    def on_change_product(self):
        super(InventoryLine, self).on_change_product()
        self.diff_quantity = None
        if self.product:
            self.diff_quantity = self.get_diff_quantity()

    @fields.depends('quantity', 'expected_quantity')
    def on_change_quantity(self):
        self.diff_quantity = None
        if self.quantity is not None:
            self.diff_quantity = self.get_diff_quantity()

    def get_diff_quantity(self, name=None):
        if self.expected_quantity is None or \
                self.quantity is None:
            return
        return self.quantity - self.expected_quantity
