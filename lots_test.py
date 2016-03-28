import copy
import datetime
import unittest
import StringIO

import lots as lots_lib

class TestLots(unittest.TestCase):

    def assertSameLots(self, a, b):
        self.assertEqual(a, b, msg='Lots are not equal: \n{}\n{}'.format(a, b))

    def test_parse_valid_csv_file(self):
        csv_data = [
            'Num Shares,Symbol,Description,Buy Date,Basis,Sell Date,'
            'Proceeds,Adjustment Code,Adjustment,Form Position,Buy Lot,'
            'Is Replacement',
            '10,ABC,A,9/15/2014,2000,10/5/2014,1800,W,200,form1,lot1,true',
            '10,ABC,A,9/15/2014,2000,10/5/2014,1800,W,200,form2,lot2,false',
            '20,ABC,A,9/25/2014,3000,11/5/2014,1800,,,,'
        ]
        lots = lots_lib.Lots.create_from_csv_data(csv_data)
        expected_lots_rows = []
        expected_lots_rows.append(lots_lib.Lot(10, 'ABC', 'A',
            datetime.date(2014, 9, 15), 2000, datetime.date(2014, 10, 5), 1800,
            'W', 200, 'form1', 'lot1', True))
        expected_lots_rows.append(lots_lib.Lot(10, 'ABC', 'A',
            datetime.date(2014, 9, 15), 2000, datetime.date(2014, 10, 5), 1800,
            'W', 200, 'form2', 'lot2', False))
        expected_lots_rows.append(lots_lib.Lot(20, 'ABC', 'A',
            datetime.date(2014, 9, 25), 3000, datetime.date(2014, 11, 5), 1800,
            '', 0, '', '', False))
        expected_lots = lots_lib.Lots(expected_lots_rows)
        self.assertSameLots(lots, expected_lots)

    def test_parse_legacy_valid_csv_file(self):
        csv_data = [
            'Cnt,Sym,Desc,BuyDate,Basis,SellDate,Proceeds,AdjCode,Adj,'
            'FormPosition,BuyLot,IsReplacement',
            '10,ABC,A,9/15/2014,2000,10/5/2014,1800,W,200,form1,lot1,true',
            '10,ABC,A,9/15/2014,2000,10/5/2014,1800,W,200,form2,lot2,false',
            '20,ABC,A,9/25/2014,3000,11/5/2014,1800,,,,'
        ]
        lots = lots_lib.Lots.create_from_csv_data(csv_data)
        expected_lots_rows = []
        expected_lots_rows.append(lots_lib.Lot(10, 'ABC', 'A',
            datetime.date(2014, 9, 15), 2000, datetime.date(2014, 10, 5), 1800,
            'W', 200, 'form1', 'lot1', True))
        expected_lots_rows.append(lots_lib.Lot(10, 'ABC', 'A',
            datetime.date(2014, 9, 15), 2000, datetime.date(2014, 10, 5), 1800,
            'W', 200, 'form2', 'lot2', False))
        expected_lots_rows.append(lots_lib.Lot(20, 'ABC', 'A',
            datetime.date(2014, 9, 25), 3000, datetime.date(2014, 11, 5), 1800,
            '', 0, '', '', False))
        expected_lots = lots_lib.Lots(expected_lots_rows)
        self.assertSameLots(lots, expected_lots)

    def test_parse_invalid_headers(self):
        csv_data = [
            'Num,Symbol,Description,Buy Date,Basis,Sell Date,'
            'Proceeds,Adjustment Code,Adjustment,Form Position,Buy Lot,'
            'Is Replacement',
            '10,ABC,A,9/15/2014,2000,10/5/2014,1800,,,lot1'
        ]
        with self.assertRaises(lots_lib.BadHeadersError):
            lots = lots_lib.Lots.create_from_csv_data(csv_data)

    def test_write_csv_data(self):
        lots_rows = []
        lots_rows.append(lots_lib.Lot(10, 'ABC', 'A',
            datetime.date(2014, 9, 15), 2000, datetime.date(2014, 10, 5), 1800,
            'W', 200, 'form1', 'lot1', True))
        lots_rows.append(lots_lib.Lot(10, 'ABC', 'A',
            datetime.date(2014, 9, 15), 2000, datetime.date(2014, 10, 5), 1800,
            'W', 200, 'form2', 'lot2', False))
        lots_rows.append(lots_lib.Lot(20, 'ABC', 'A',
            datetime.date(2014, 9, 25), 3000, datetime.date(2014, 11, 5), 1800,
            '', 0, '', '', False))
        lots = lots_lib.Lots(lots_rows)

        actual_output = StringIO.StringIO()
        lots.write_csv_data(actual_output)

        expected_csv_data = [
            'Num Shares,Symbol,Description,Buy Date,Basis,Sell Date,'
            'Proceeds,Adjustment Code,Adjustment,Form Position,Buy Lot,'
            'Is Replacement',
            '10,ABC,A,09/15/2014,2000,10/05/2014,1800,W,200,form1,lot1,True',
            '10,ABC,A,09/15/2014,2000,10/05/2014,1800,W,200,form2,lot2,False',
            '20,ABC,A,09/25/2014,3000,11/05/2014,1800,,,,_1,False'
        ]

        actual_output.seek(0)
        self.assertSequenceEqual(
            [line.rstrip()
             for line in actual_output.readlines()], expected_csv_data)

    def test_is_loss(self):
        loss_lot = lots_lib.Lot(10, 'ABC', 'A', datetime.date(2014, 9, 15),
                2000, datetime.date(2014, 10, 5), 1800, '', 0, 'form1', 'lot1',
                True)
        self.assertTrue(loss_lot.is_loss())

        gain_lot = lots_lib.Lot(10, 'ABC', 'A', datetime.date(2014, 9, 15),
                1000, datetime.date(2014, 10, 5), 1800, '', 0, 'form1', 'lot1',
                True)
        self.assertFalse(gain_lot.is_loss())

        unsold_lot = lots_lib.Lot(10, 'ABC', 'A', datetime.date(2014, 9, 15),
                2000, None, 0, '', 0, 'form1', 'lot1', True)
        self.assertFalse(unsold_lot.is_loss())

    def test_compare_by_buy_date(self):
        lots = []
        lots.append(lots_lib.Lot(1, '', '', datetime.date(2014, 9, 2), 0,
            datetime.date(2014, 11, 5), 0, '', 0, 'form2', '', False))
        lots.append(lots_lib.Lot(1, '', '', datetime.date(2014, 9, 1), 0,
            datetime.date(2014, 10, 5), 0, '', 0, 'form1', '', False))
        lots.append(lots_lib.Lot(1, '', '', datetime.date(2014, 9, 2), 0,
            datetime.date(2014, 11, 5), 0, '', 0, 'form1', '', False))
        lots.append(lots_lib.Lot(1, '', '', datetime.date(2014, 9, 2), 0,
            datetime.date(2014, 11, 5), 0, '', 0, 'form1', '', False))
        lots.append(lots_lib.Lot(1, '', '', datetime.date(2014, 9, 3), 0,
            datetime.date(2014, 10, 5), 0, '', 0, 'form1', '', False))
        lots.append(lots_lib.Lot(1, '', '', datetime.date(2014, 9, 2), 0,
            None, 0, '', 0, 'form1', '', False))
        lots.append(lots_lib.Lot(1, '', '', datetime.date(2014, 9, 2), 0,
            datetime.date(2014, 10, 5), 0, '', 0, 'form1', '', False))
        lots.append(lots_lib.Lot(1, '', '', datetime.date(2014, 9, 3), 0,
            datetime.date(2014, 10, 6), 0, '', 0, 'form1', '', False))

        expected = []
        expected.append(lots_lib.Lot(1, '', '', datetime.date(2014, 9, 1), 0,
            datetime.date(2014, 10, 5), 0, '', 0, 'form1', '', False))
        expected.append(lots_lib.Lot(1, '', '', datetime.date(2014, 9, 2), 0,
            datetime.date(2014, 10, 5), 0, '', 0, 'form1', '', False))
        expected.append(lots_lib.Lot(1, '', '', datetime.date(2014, 9, 2), 0,
            datetime.date(2014, 11, 5), 0, '', 0, 'form1', '', False))
        expected.append(lots_lib.Lot(1, '', '', datetime.date(2014, 9, 2), 0,
            datetime.date(2014, 11, 5), 0, '', 0, 'form1', '', False))
        expected.append(lots_lib.Lot(1, '', '', datetime.date(2014, 9, 2), 0,
            datetime.date(2014, 11, 5), 0, '', 0, 'form2', '', False))
        expected.append(lots_lib.Lot(1, '', '', datetime.date(2014, 9, 2), 0,
            None, 0, '', 0, 'form1', '', False))
        expected.append(lots_lib.Lot(1, '', '', datetime.date(2014, 9, 3), 0,
            datetime.date(2014, 10, 5), 0, '', 0, 'form1', '', False))
        expected.append(lots_lib.Lot(1, '', '', datetime.date(2014, 9, 3), 0,
            datetime.date(2014, 10, 6), 0, '', 0, 'form1', '', False))

        lots.sort(cmp=lots_lib.Lot.cmp_by_buy_date)
        self.assertTrue(lots == expected)

    def test_compare_by_sell_date(self):
        lots = []
        lots.append(lots_lib.Lot(1, '', '', datetime.date(2014, 9, 2), 0,
            datetime.date(2014, 11, 5), 0, '', 0, 'form2', '', False))
        lots.append(lots_lib.Lot(1, '', '', datetime.date(2014, 9, 1), 0,
            datetime.date(2014, 10, 5), 0, '', 0, 'form1', '', False))
        lots.append(lots_lib.Lot(1, '', '', datetime.date(2014, 9, 2), 0,
            datetime.date(2014, 11, 5), 0, '', 0, 'form1', '', False))
        lots.append(lots_lib.Lot(1, '', '', datetime.date(2014, 9, 2), 0,
            datetime.date(2014, 11, 5), 0, '', 0, 'form1', '', False))
        lots.append(lots_lib.Lot(1, '', '', datetime.date(2014, 9, 3), 0,
            datetime.date(2014, 10, 5), 0, '', 0, 'form1', '', False))
        lots.append(lots_lib.Lot(1, '', '', datetime.date(2014, 9, 2), 0,
            None, 0, '', 0, 'form1', '', False))
        lots.append(lots_lib.Lot(1, '', '', datetime.date(2014, 9, 2), 0,
            datetime.date(2014, 10, 5), 0, '', 0, 'form1', '', False))
        lots.append(lots_lib.Lot(1, '', '', datetime.date(2014, 9, 3), 0,
            datetime.date(2014, 10, 6), 0, '', 0, 'form1', '', False))

        expected = []
        expected.append(lots_lib.Lot(1, '', '', datetime.date(2014, 9, 1), 0,
            datetime.date(2014, 10, 5), 0, '', 0, 'form1', '', False))
        expected.append(lots_lib.Lot(1, '', '', datetime.date(2014, 9, 2), 0,
            datetime.date(2014, 10, 5), 0, '', 0, 'form1', '', False))
        expected.append(lots_lib.Lot(1, '', '', datetime.date(2014, 9, 3), 0,
            datetime.date(2014, 10, 5), 0, '', 0, 'form1', '', False))
        expected.append(lots_lib.Lot(1, '', '', datetime.date(2014, 9, 3), 0,
            datetime.date(2014, 10, 6), 0, '', 0, 'form1', '', False))
        expected.append(lots_lib.Lot(1, '', '', datetime.date(2014, 9, 2), 0,
            datetime.date(2014, 11, 5), 0, '', 0, 'form1', '', False))
        expected.append(lots_lib.Lot(1, '', '', datetime.date(2014, 9, 2), 0,
            datetime.date(2014, 11, 5), 0, '', 0, 'form1', '', False))
        expected.append(lots_lib.Lot(1, '', '', datetime.date(2014, 9, 2), 0,
            datetime.date(2014, 11, 5), 0, '', 0, 'form2', '', False))
        expected.append(lots_lib.Lot(1, '', '', datetime.date(2014, 9, 2), 0,
            None, 0, '', 0, 'form1', '', False))

        lots.sort(cmp=lots_lib.Lot.cmp_by_sell_date)
        self.assertTrue(lots == expected)

    def test_compare_by_num_shares(self):
        lots = []
        lots.append(lots_lib.Lot(1, '', '', datetime.date(2014, 9, 2), 0,
            datetime.date(2014, 11, 5), 0, '', 0, 'form2', '', False))
        lots.append(lots_lib.Lot(5, '', '', datetime.date(2014, 9, 1), 0,
            datetime.date(2014, 10, 5), 0, '', 0, 'form1', '', False))
        lots.append(lots_lib.Lot(3, '', '', datetime.date(2014, 9, 2), 0,
            datetime.date(2014, 11, 5), 0, '', 0, 'form1', '', False))
        lots.append(lots_lib.Lot(2, '', '', datetime.date(2014, 9, 2), 0,
            datetime.date(2014, 11, 5), 0, '', 0, 'form1', '', False))
        lots.append(lots_lib.Lot(7, '', '', datetime.date(2014, 9, 3), 0,
            datetime.date(2014, 10, 5), 0, '', 0, 'form1', '', False))

        expected = []
        expected.append(lots_lib.Lot(1, '', '', datetime.date(2014, 9, 2), 0,
            datetime.date(2014, 11, 5), 0, '', 0, 'form2', '', False))
        expected.append(lots_lib.Lot(2, '', '', datetime.date(2014, 9, 2), 0,
            datetime.date(2014, 11, 5), 0, '', 0, 'form1', '', False))
        expected.append(lots_lib.Lot(3, '', '', datetime.date(2014, 9, 2), 0,
            datetime.date(2014, 11, 5), 0, '', 0, 'form1', '', False))
        expected.append(lots_lib.Lot(5, '', '', datetime.date(2014, 9, 1), 0,
            datetime.date(2014, 10, 5), 0, '', 0, 'form1', '', False))
        expected.append(lots_lib.Lot(7, '', '', datetime.date(2014, 9, 3), 0,
            datetime.date(2014, 10, 5), 0, '', 0, 'form1', '', False))

        lots.sort(cmp=lots_lib.Lot.cmp_by_num_shares)
        self.assertTrue(lots == expected)

    def test_contents_equal(self):
        lots = lots_lib.Lots([])
        lots.add(lots_lib.Lot(1, '', '', datetime.date(2014, 9, 2), 0,
            datetime.date(2014, 11, 5), 0, '', 0, 'form2', '', False))
        lots.add(lots_lib.Lot(5, '', '', datetime.date(2014, 9, 1), 0,
            datetime.date(2014, 10, 5), 0, '', 0, 'form1', '', False))
        lots.add(lots_lib.Lot(3, '', '', datetime.date(2014, 9, 2), 0,
            datetime.date(2014, 11, 5), 0, '', 0, 'form1', '', False))
        self.assertTrue(lots.contents_equal(lots))

        other_lots = copy.deepcopy(lots)
        self.assertTrue(lots.contents_equal(other_lots))

    def test_contents_not_equal(self):
        lots = lots_lib.Lots([])
        lots.add(lots_lib.Lot(1, '', '', datetime.date(2014, 9, 2), 0,
            datetime.date(2014, 11, 5), 0, '', 0, 'form2', '', False))
        lots.add(lots_lib.Lot(5, '', '', datetime.date(2014, 9, 1), 0,
            datetime.date(2014, 10, 5), 0, '', 0, 'form1', '', False))
        lots.add(lots_lib.Lot(3, '', '', datetime.date(2014, 9, 2), 0,
            datetime.date(2014, 11, 5), 0, '', 0, 'form1', '', False))

        other_lots = copy.deepcopy(lots)
        other_lots.lots()[0].num_shares = 2
        self.assertFalse(lots.contents_equal(other_lots))


if __name__ == '__main__':
    unittest.main()
