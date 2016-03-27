import copy
import datetime
import unittest

import lots as lots_lib
import wash


def create_lot(num_shares,
               buy_year,
               buy_month,
               buy_day,
               basis,
               sell_year=0,
               sell_month=0,
               sell_day=0,
               proceeds=0):
    buy_date = datetime.date(buy_year, buy_month, buy_day)
    sell_date = None
    if sell_year:
        sell_date = datetime.date(sell_year, sell_month, sell_day)
    return lots_lib.Lot(num_shares, 'ABC', 'A', buy_date, basis, sell_date,
                        proceeds, '', 0, '', '', False)


class TestEarliestLossLot(unittest.TestCase):
    # In these tests, we compare the object ids, since we want to ensure that
    # the actual object, and not a copy, is returned.

    def setUp(self):
        self.loss1 = create_lot(10, 2014, 9, 17, 200, 2014, 10, 2, 100)
        self.loss2 = create_lot(10, 2014, 9, 16, 200, 2014, 10, 3, 100)
        self.loss3 = create_lot(10, 2014, 9, 15, 200, 2014, 10, 4, 100)
        self.gain = create_lot(10, 2014, 9, 14, 200, 2014, 10, 1, 300)
        self.unsold = create_lot(10, 2014, 9, 13, 200)

    def assertLotsSame(self, a, b):
        self.assertIs(a, b, msg='{} is not {}: \n{}'.format(
            id(a), id(b), lots_lib.Lots([a, b])))

    def test_two_losses(self):
        lots = lots_lib.Lots([self.loss1, self.loss2, self.loss3])
        self.assertLotsSame(self.loss1, wash.earliest_loss_lot(lots))

    def test_unsold(self):
        lots = lots_lib.Lots([self.loss1, self.unsold, self.loss2])
        self.assertLotsSame(self.loss1, wash.earliest_loss_lot(lots))

    def test_gain(self):
        lots = lots_lib.Lots([self.loss1, self.gain, self.loss2])
        self.assertLotsSame(self.loss1, wash.earliest_loss_lot(lots))


class TestBestReplacementLot(unittest.TestCase):
    # In these tests, we compare the object ids, since we want to ensure that
    # the actual object, and not a copy, is returned.

    def setUp(self):
        self.loss = create_lot(10, 2011, 6, 1, 120, 2012, 1, 10, 110)
        self.small_loss = create_lot(5, 2011, 6, 1, 120, 2012, 1, 10, 110)
        self.large_loss = create_lot(20, 2011, 6, 1, 120, 2012, 1, 10, 110)
        self.very_early_gain = create_lot(10, 2010, 1, 1, 100, 2011, 1, 1, 200)
        self.first_gain = create_lot(10, 2012, 1, 1, 100, 2012, 6, 1, 200)
        self.first_gain_earlier_sale = create_lot(10, 2012, 1, 1, 100,
                                                      2012, 5, 1, 200)
        self.first_gain_later_sale = create_lot(10, 2012, 1, 1, 100,
                                                    2012, 7, 1, 200)
        self.small_first_gain = create_lot(5, 2012, 1, 1, 100, 2012, 6, 1, 200)
        self.large_first_gain = create_lot(20, 2012, 1, 1, 100, 2012, 6, 1, 200)
        self.second_gain = create_lot(10, 2012, 3, 1, 150, 2012, 8, 1, 250)
        self.unsold = create_lot(10, 2012, 1, 5, 130)
        self.days_early_31 = create_lot(10, 2011, 12, 10, 130)
        self.days_early_30 = create_lot(10, 2011, 12, 11, 130)
        self.days_after_30 = create_lot(10, 2012, 2, 9, 130)
        self.days_after_31 = create_lot(10, 2012, 2, 10, 130)

    def assertLotsSame(self, a, b):
        self.assertIs(a, b, msg='{} is not {}: \n{}'.format(
            id(a), id(b), lots_lib.Lots([a, b])))

    def assertLotIsNone(self, a):
        self.assertIsNone(a, msg='{} is not None: \n{}'.format(
            id(a), lots_lib.Lots([a]) if a else None))

    def test_only_loss_lot_exists(self):
        lots = lots_lib.Lots([self.loss])
        self.assertLotIsNone(wash.best_replacement_lot(self.loss, lots))

    def test_no_replacement_too_early(self):
        lots = lots_lib.Lots([self.very_early_gain, self.loss])
        self.assertLotIsNone(wash.best_replacement_lot(self.loss, lots))

    def test_no_replacement_too_late(self):
        lots = lots_lib.Lots([self.second_gain, self.loss])
        self.assertLotIsNone(wash.best_replacement_lot(self.loss, lots))

    def test_no_replacement_31_days_before(self):
        lots = lots_lib.Lots([self.days_early_31])
        self.assertLotIsNone(wash.best_replacement_lot(self.loss, lots))

    def test_no_replacement_31_days_after(self):
        lots = lots_lib.Lots([self.days_after_31])
        self.assertLotIsNone(wash.best_replacement_lot(self.loss, lots))

    def test_replacement_30_days_before(self):
        lots = lots_lib.Lots([self.days_early_30])
        self.assertLotsSame(self.days_early_30,
                            wash.best_replacement_lot(self.loss, lots))

    def test_replacement_30_days_after(self):
        lots = lots_lib.Lots([self.days_after_30])
        self.assertLotsSame(self.days_after_30,
                            wash.best_replacement_lot(self.loss, lots))

    def test_replacement_is_unsold(self):
        lots = lots_lib.Lots([self.unsold, self.loss])
        self.assertLotsSame(self.unsold,
                            wash.best_replacement_lot(self.loss, lots))

    def test_replacement_is_first_bought(self):
        lots = lots_lib.Lots([self.first_gain, self.first_gain_earlier_sale,
                              self.first_gain_later_sale])
        self.assertLotsSame(self.first_gain_earlier_sale,
                            wash.best_replacement_lot(self.loss, lots))

    def test_replacement_checks_sell_date(self):
        # If there are multiple possible replacements that were bought on the
        # same day, the one with the earlier sell date is chosen.
        lots = lots_lib.Lots([self.unsold, self.first_gain, self.loss])
        self.assertLotsSame(self.first_gain,
                            wash.best_replacement_lot(self.loss, lots))

    def test_replacement_for_small_loss(self):
        lots = lots_lib.Lots([self.unsold, self.first_gain, self.small_loss])
        final_lots = copy.deepcopy(lots)
        wash_lot = wash.best_replacement_lot(self.small_loss, lots)
        self.assertLotsSame(self.first_gain, wash_lot)
        self.assertEqual(5, wash_lot.num_shares)
        self.assertEqual(self.first_gain.buy_lot, wash_lot.buy_lot)
        self.assertEqual(4, lots.size())

        final_lots.add(copy.deepcopy(final_lots.lots()[1]))
        final_lots.lots()[1].num_shares = 5
        final_lots.lots()[3].num_shares = 5
        lots.sort(cmp=lots_lib.Lot.cmp_by_buy_date)
        final_lots.sort(cmp=lots_lib.Lot.cmp_by_buy_date)
        self.assertTrue(lots == final_lots)

    def test_replacement_for_small_loss_multiple_options(self):
        lots = lots_lib.Lots([self.loss, self.small_first_gain,
                              self.large_first_gain])
        final_lots = copy.deepcopy(lots)
        wash_lot = wash.best_replacement_lot(self.loss, lots)
        self.assertLotsSame(self.large_first_gain, wash_lot)
        self.assertEqual(10, wash_lot.num_shares)
        self.assertEqual(self.large_first_gain.buy_lot, wash_lot.buy_lot)
        self.assertEqual(4, lots.size())

        final_lots.add(copy.deepcopy(final_lots.lots()[2]))
        final_lots.lots()[2].num_shares = 10
        final_lots.lots()[3].num_shares = 10
        lots.sort(cmp=lots_lib.Lot.cmp_by_buy_date)
        final_lots.sort(cmp=lots_lib.Lot.cmp_by_buy_date)
        self.assertTrue(lots == final_lots)

    def test_replacement_for_large_loss(self):
        lots = lots_lib.Lots([self.unsold, self.first_gain, self.large_loss])
        final_lots = copy.deepcopy(lots)
        wash_lot = wash.best_replacement_lot(self.large_loss, lots)
        self.assertLotsSame(self.first_gain, wash_lot)
        self.assertEqual(10, wash_lot.num_shares)
        self.assertEqual(3, lots.size())

        lots.sort(cmp=lots_lib.Lot.cmp_by_buy_date)
        final_lots.sort(cmp=lots_lib.Lot.cmp_by_buy_date)
        self.assertTrue(lots == final_lots)

    def test_replacement_chooses_same_size_replacement_lot(self):
        lots = lots_lib.Lots([self.loss, self.first_gain,
                              self.small_first_gain, self.large_first_gain])
        self.assertLotsSame(self.first_gain,
                            wash.best_replacement_lot(self.loss, lots))

        self.assertLotsSame(self.small_first_gain,
                            wash.best_replacement_lot(self.small_loss, lots))

        self.assertLotsSame(self.large_first_gain,
                            wash.best_replacement_lot(self.large_loss, lots))

    def test_loss_not_in_lots(self):
        lots = lots_lib.Lots([self.unsold, self.first_gain])
        self.assertLotsSame(self.first_gain,
                            wash.best_replacement_lot(self.loss, lots))

    # TODO add tests for buy_lot being set, and is_replacement being set

if __name__ == '__main__':
    unittest.main()
