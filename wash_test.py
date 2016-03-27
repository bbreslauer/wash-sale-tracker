import datetime
import unittest

import lots as lots_lib
import wash


class TestEarliestLossLot(unittest.TestCase):
    # In these tests, we compare the object ids, since we want to ensure that
    # the actual object, and not a copy, is returned.

    def setUp(self):
        self.loss1 = lots_lib.Lot(10, 'ABC', 'A', datetime.date(2014, 9, 17),
                                  2000, datetime.date(2014, 10, 2), 1800, '',
                                  0, '', '', True)
        self.loss2 = lots_lib.Lot(10, 'ABC', 'A', datetime.date(2014, 9, 16),
                                  2000, datetime.date(2014, 10, 3), 1800, '',
                                  0, '', '', False)
        self.loss3 = lots_lib.Lot(10, 'ABC', 'A', datetime.date(2014, 9, 15),
                                  2000, datetime.date(2014, 10, 4), 1800, '',
                                  0, '', '', False)
        self.gain = lots_lib.Lot(10, 'ABC', 'A', datetime.date(2014, 9, 14),
                                 2000, datetime.date(2014, 10, 1), 2800, '', 0,
                                 '', '', False)
        self.unsold = lots_lib.Lot(10, 'ABC', 'A', datetime.date(2014, 9, 13),
                                   2000, None, 0, '', 0, '', '', False)

    def test_two_losses(self):
        lots = lots_lib.Lots([self.loss1, self.loss2, self.loss3])
        self.assertEqual(id(self.loss1), id(wash.earliest_loss_lot(lots)))

    def test_unsold(self):
        lots = lots_lib.Lots([self.loss1, self.unsold, self.loss2])
        self.assertEqual(id(self.loss1), id(wash.earliest_loss_lot(lots)))

    def test_gain(self):
        lots = lots_lib.Lots([self.loss1, self.gain, self.loss2])
        self.assertEqual(id(self.loss1), id(wash.earliest_loss_lot(lots)))


if __name__ == '__main__':
    unittest.main()
