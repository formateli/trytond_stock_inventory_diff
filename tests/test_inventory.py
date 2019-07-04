# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
import unittest
import trytond.tests.test_tryton
from trytond.tests.test_tryton import ModuleTestCase, with_transaction
from trytond.pool import Pool
from trytond.transaction import Transaction
from trytond.modules.company.tests import create_company, set_company
import datetime
from decimal import Decimal


class InventoryDiffTestCase(ModuleTestCase):
    'Test Stock Inventory Diff'
    module = 'stock_inventory_diff'

    @with_transaction()
    def test_stock_inventory_diff(self):
        pool = Pool()
        Inventory = pool.get('stock.inventory')
        Line = pool.get('stock.inventory.line')
        Location = pool.get('stock.location')

        today = datetime.date.today()

        company = create_company()
        with set_company(company):
            supplier_loc, = Location.search([('code', '=', 'SUP')])
            storage_loc, = Location.search([('code', '=', 'STO')])
            customer_loc, = Location.search([('code', '=', 'CUS')])

            unit, kg, product, product2 = self._create_products()

            # Fill stock
            self._create_stock_move(company, today, product, unit, 1,
                Decimal('100.0'), supplier_loc, storage_loc)
            self._create_stock_move(company, today, product2, kg, 2.5,
                Decimal('70.0'), supplier_loc, storage_loc)

            # Create Inventory
            inventory = Inventory(
                location=storage_loc,
            )
            inventory.save()

            Inventory.complete_lines([inventory])
            line_by_product = {l.product.id: l for l in inventory.lines}

            line_p1 = line_by_product[product.id]
            self.assertEqual(1.0, line_p1.expected_quantity)
            self.assertEqual(None, line_p1.diff_quantity)

            line_p1.quantity = 3
            line_p1.on_change_quantity()
            self.assertEqual(2.0, line_p1.diff_quantity)

            line_p2 = line_by_product[product2.id]
            self.assertEqual(2.5, line_p2.expected_quantity)
            line_p2.quantity = 2.5
            line_p2.on_change_quantity()
            self.assertEqual(0.0, line_p2.diff_quantity)

            # More stock moves
            self._create_stock_move(company, today, product, unit, 1,
                Decimal('100.0'), supplier_loc, storage_loc)
            self._create_stock_move(company, today, product2, kg, 1.3,
                Decimal('70.0'), supplier_loc, storage_loc)
            
            # Check inventory change
            Inventory.complete_lines([inventory])

            self.assertEqual(2.0, line_p1.expected_quantity)
            self.assertEqual(3.0, line_p1.quantity)
            line_p1.on_change_quantity()
            self.assertEqual(1.0, line_p1.diff_quantity)

            self.assertEqual(3.8, line_p2.expected_quantity)
            self.assertEqual(2.5, line_p2.quantity)
            line_p2.on_change_quantity()
            self.assertEqual(-1.3, round(line_p2.diff_quantity, 1))

    def _create_stock_move(self, company, today, product, unit, quantity,
                unit_price, from_location, to_location):
        pool = Pool()
        StockMove = pool.get('stock.move')

        move = StockMove(
            product=product,
            uom=unit,
            quantity=quantity,
            from_location=from_location,
            to_location=to_location,
            planned_date=today,
            effective_date=today,
            company=company,
            unit_price=unit_price,
            currency=company.currency,
        )
        move.save()
        StockMove.do([move])

    def _create_products(self):
        pool = Pool()
        ProductUom = pool.get('product.uom')

        unit, = ProductUom.search([('name', '=', 'Unit')])
        product = self._create_product(
            'Product', unit, Decimal('300.0'), Decimal('80.0'))

        kg, = ProductUom.search([('name', '=', 'Kilogram')])
        product2 = self._create_product(
            'Product 2', kg, Decimal('140.0'), Decimal('60.0'))

        return unit, kg, product, product2

    @classmethod
    def _create_product(self, name, uom, list_price, cost_price):
        pool = Pool()
        Template = pool.get('product.template')
        Product = pool.get('product.product')

        template=Template(
            name=name,
            default_uom=uom,
            type='goods',
            list_price=list_price,
            cost_price=cost_price,
            cost_price_method='average')
        template.save()

        product = Product(
            template=template
        )
        product.save()
        return product


def suite():
    suite = trytond.tests.test_tryton.suite()
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(
        InventoryDiffTestCase))
    return suite
