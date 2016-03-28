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

    def assertSameLot(self, a, b):
        self.assertIs(a, b, msg='{} is not {}: \n{}'.format(
            id(a), id(b), lots_lib.Lots([a, b])))

    def test_two_losses(self):
        lots = lots_lib.Lots([self.loss1, self.loss2, self.loss3])
        self.assertSameLot(self.loss1, wash.earliest_loss_lot(lots))

    def test_unsold(self):
        lots = lots_lib.Lots([self.loss1, self.unsold, self.loss2])
        self.assertSameLot(self.loss1, wash.earliest_loss_lot(lots))

    def test_gain(self):
        lots = lots_lib.Lots([self.loss1, self.gain, self.loss2])
        self.assertSameLot(self.loss1, wash.earliest_loss_lot(lots))


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
        self.gain_just_before_loss = create_lot(10, 2012, 1, 1, 100,
                                                    2012, 1, 5, 200)

    def assertSameLot(self, a, b):
        self.assertIs(a, b, msg='{} is not {}: \n{}'.format(
            id(a), id(b), lots_lib.Lots([a, b])))

    def assertSameLots(self, a, b):
        self.assertEqual(a, b, msg='Lots are not equal: \n{}\n{}'.format(a, b))

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
        self.assertSameLot(self.days_early_30,
                            wash.best_replacement_lot(self.loss, lots))

    def test_replacement_30_days_after(self):
        lots = lots_lib.Lots([self.days_after_30])
        self.assertSameLot(self.days_after_30,
                            wash.best_replacement_lot(self.loss, lots))

    def test_replacement_is_unsold(self):
        lots = lots_lib.Lots([self.unsold, self.loss])
        self.assertSameLot(self.unsold,
                            wash.best_replacement_lot(self.loss, lots))

    def test_replacement_is_first_bought(self):
        lots = lots_lib.Lots([self.first_gain, self.first_gain_earlier_sale,
                              self.first_gain_later_sale])
        self.assertSameLot(self.first_gain_earlier_sale,
                            wash.best_replacement_lot(self.loss, lots))

    def test_replacement_checks_sell_date(self):
        # If there are multiple possible replacements that were bought on the
        # same day, the one with the earlier sell date is chosen.
        lots = lots_lib.Lots([self.unsold, self.first_gain, self.loss])
        self.assertSameLot(self.first_gain,
                            wash.best_replacement_lot(self.loss, lots))

    def test_replacement_for_small_loss(self):
        lots = lots_lib.Lots([self.unsold, self.first_gain, self.small_loss])
        wash_lot = wash.best_replacement_lot(self.small_loss, lots)
        self.assertSameLot(self.first_gain, wash_lot)

    def test_replacement_for_loss_multiple_options(self):
        lots = lots_lib.Lots([self.loss, self.small_first_gain,
                              self.large_first_gain])
        wash_lot = wash.best_replacement_lot(self.loss, lots)
        self.assertSameLot(self.large_first_gain, wash_lot)

    def test_replacement_for_large_loss(self):
        lots = lots_lib.Lots([self.unsold, self.first_gain, self.large_loss])
        final_lots = copy.deepcopy(lots)
        wash_lot = wash.best_replacement_lot(self.large_loss, lots)
        self.assertSameLot(self.first_gain, wash_lot)
        self.assertEqual(10, wash_lot.num_shares)
        self.assertEqual(3, lots.size())

        lots.sort(cmp=lots_lib.Lot.cmp_by_buy_date)
        final_lots.sort(cmp=lots_lib.Lot.cmp_by_buy_date)
        self.assertSameLots(lots, final_lots)

    def test_replacement_chooses_same_size_replacement_lot(self):
        lots = lots_lib.Lots([self.loss, self.first_gain,
                              self.small_first_gain, self.large_first_gain])
        self.assertSameLot(self.first_gain,
                            wash.best_replacement_lot(self.loss, lots))

        self.assertSameLot(self.small_first_gain,
                            wash.best_replacement_lot(self.small_loss, lots))

        self.assertSameLot(self.large_first_gain,
                            wash.best_replacement_lot(self.large_loss, lots))

    def test_loss_not_in_lots(self):
        lots = lots_lib.Lots([self.unsold, self.first_gain])
        self.assertSameLot(self.first_gain,
                            wash.best_replacement_lot(self.loss, lots))

    def test_two_similar_lots(self):
        # There are two lots that have the same values, but were bought
        # separately.
        lot1 = create_lot(10, 2012, 1, 1, 120, 2012, 1, 10, 110)
        lot2 = create_lot(10, 2012, 1, 1, 120, 2012, 1, 10, 110)
        lots = lots_lib.Lots([lot1, lot2])
        self.assertSameLot(lot2, wash.best_replacement_lot(lot1, lots))

    def test_two_lots_from_same_buy_lot(self):
        # There are two lots that have the same values, and were bought
        # together.
        lot1 = create_lot(10, 2012, 1, 1, 120, 2012, 1, 10, 110)
        lot1.buy_lot = '1'
        lot2 = create_lot(10, 2012, 1, 1, 120, 2012, 1, 10, 110)
        lot2.buy_lot = '1'
        lots = lots_lib.Lots([lot1, lot2])
        self.assertLotIsNone(wash.best_replacement_lot(lot1, lots))

    def test_already_used_replacement_is_not_used_again(self):
        lot1 = create_lot(10, 2012, 1, 1, 120, 2012, 1, 10, 110)
        lot2 = create_lot(10, 2012, 1, 1, 120, 2012, 1, 10, 110)
        lot2.is_replacement = True
        lots = lots_lib.Lots([lot1, lot2])
        self.assertLotIsNone(wash.best_replacement_lot(lot1, lots))

    def test_lot_sold_before_loss_is_not_replacement(self):
        lots = lots_lib.Lots([self.loss, self.gain_just_before_loss])
        self.assertLotIsNone(wash.best_replacement_lot(self.loss, lots))


class TestWashOneLot(unittest.TestCase):

    def setUp(self):
        self.loss = create_lot(10, 2011, 6, 1, 120, 2012, 1, 10, 110)
        self.small_loss = create_lot(6, 2011, 6, 1, 120, 2012, 1, 10, 110)
        self.large_loss = create_lot(18, 2011, 6, 1, 120, 2012, 1, 10, 110)
        self.later_loss = create_lot(10, 2012, 1, 20, 140, 2012, 3, 1, 115)
        self.very_early_gain = create_lot(10, 2010, 1, 1, 100, 2011, 1, 1, 200)
        self.first_gain = create_lot(10, 2012, 1, 1, 100, 2012, 6, 1, 200)
        self.small_first_gain = create_lot(6, 2012, 1, 1, 100, 2012, 6, 1, 200)
        self.large_first_gain = create_lot(18, 2012, 1, 1, 100, 2012, 6, 1, 200)
        self.second_gain = create_lot(10, 2012, 2, 1, 150, 2012, 8, 1, 250)
        self.very_late_gain = create_lot(10, 2013, 1, 1, 150, 2013, 8, 1, 250)
        self.unsold = create_lot(10, 2012, 1, 5, 130)

    def assertSameLots(self, a, b):
        self.assertEqual(a, b, msg='Lots are not equal: \n{}\n{}'.format(a, b))

    def test_no_wash_if_no_replacement_shares(self):
        lots = lots_lib.Lots([self.loss, self.very_early_gain,
                              self.very_late_gain])

        final_lots = copy.deepcopy(lots)
        loss = final_lots.lots()[0]
        loss.loss_processed = True

        wash.wash_one_lot(self.loss, lots)
        self.assertSameLots(lots, final_lots)

    def test_wash_against_single_purchase(self):
        lots = lots_lib.Lots([self.loss, self.first_gain])

        final_lots = copy.deepcopy(lots)
        disallowed_loss = final_lots.lots()[0]
        disallowed_loss.adjustment_code = 'W'
        disallowed_loss.adjustment = 10
        disallowed_loss.loss_processed = True
        replacement = final_lots.lots()[1]
        replacement.basis = 110
        replacement.buy_date -= self.loss.sell_date - self.loss.buy_date
        replacement.is_replacement = True

        wash.wash_one_lot(self.loss, lots)
        self.assertSameLots(lots, final_lots)

    def test_wash_against_first_purchase(self):
        lots = lots_lib.Lots([self.loss, self.first_gain, self.second_gain])

        final_lots = copy.deepcopy(lots)
        disallowed_loss = final_lots.lots()[0]
        disallowed_loss.adjustment_code = 'W'
        disallowed_loss.adjustment = 10
        disallowed_loss.loss_processed = True
        replacement = final_lots.lots()[1]
        replacement.basis = 110
        replacement.buy_date -= self.loss.sell_date - self.loss.buy_date
        replacement.is_replacement = True

        wash.wash_one_lot(self.loss, lots)
        self.assertSameLots(lots, final_lots)

    def test_wash_against_unsold(self):
        lots = lots_lib.Lots([self.loss, self.unsold])

        final_lots = copy.deepcopy(lots)
        disallowed_loss = final_lots.lots()[0]
        disallowed_loss.adjustment_code = 'W'
        disallowed_loss.adjustment = 10
        disallowed_loss.loss_processed = True
        replacement = final_lots.lots()[1]
        replacement.basis = 140
        replacement.buy_date -= self.loss.sell_date - self.loss.buy_date
        replacement.is_replacement = True

        wash.wash_one_lot(self.loss, lots)
        self.assertSameLots(lots, final_lots)

    def test_wash_against_subsequent_loss(self):
        lots = lots_lib.Lots([self.loss, self.later_loss])

        final_lots = copy.deepcopy(lots)
        disallowed_loss = final_lots.lots()[0]
        disallowed_loss.adjustment_code = 'W'
        disallowed_loss.adjustment = 10
        disallowed_loss.loss_processed = True
        replacement = final_lots.lots()[1]
        replacement.basis = 150
        replacement.buy_date -= self.loss.sell_date - self.loss.buy_date
        replacement.is_replacement = True

        wash.wash_one_lot(self.loss, lots)
        self.assertSameLots(lots, final_lots)

    def test_wash_against_small_replacement(self):
        lots = lots_lib.Lots([self.loss, self.small_first_gain])

        final_lots = copy.deepcopy(lots)
        disallowed_loss = final_lots.lots()[0]
        # Create the split lot.
        split_lot = copy.deepcopy(disallowed_loss)
        split_lot.num_shares = 4
        split_lot.basis *= 4./10.
        split_lot.proceeds *= 4./10.
        final_lots.add(split_lot)

        disallowed_loss.num_shares = 6
        disallowed_loss.basis *= 6./10.
        disallowed_loss.proceeds *= 6./10.
        disallowed_loss.adjustment_code = 'W'
        disallowed_loss.adjustment = 6
        disallowed_loss.loss_processed = True
        replacement = final_lots.lots()[1]
        replacement.basis = 106
        replacement.buy_date -= self.loss.sell_date - self.loss.buy_date
        replacement.is_replacement = True

        wash.wash_one_lot(self.loss, lots)
        self.assertSameLots(lots, final_lots)

    def test_wash_against_large_replacement(self):
        lots = lots_lib.Lots([self.loss, self.large_first_gain])

        final_lots = copy.deepcopy(lots)
        disallowed_loss = final_lots.lots()[0]
        disallowed_loss.adjustment_code = 'W'
        disallowed_loss.adjustment = 10
        disallowed_loss.loss_processed = True
        replacement = final_lots.lots()[1]

        # Create the split lot.
        split_lot = copy.deepcopy(replacement)
        split_lot.num_shares = 8
        split_lot.basis = int(round(split_lot.basis * 8. / 18.))
        split_lot.proceeds = int(round(split_lot.proceeds * 8. / 18.))
        final_lots.add(split_lot)

        replacement.num_shares = 10
        replacement.basis = int(round(replacement.basis * 10. / 18.))
        replacement.proceeds = int(round(replacement.proceeds * 10. / 18.))
        replacement.basis += 10
        replacement.buy_date -= self.loss.sell_date - self.loss.buy_date
        replacement.is_replacement = True

        wash.wash_one_lot(self.loss, lots)
        self.assertSameLots(lots, final_lots)



# wash_all_lots is tested with run_integ_tests using the files in the tests/
# directory.


if __name__ == '__main__':
    unittest.main()
