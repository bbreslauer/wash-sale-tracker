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
            'Num Shares,Symbol,Description,Buy Date,Adjusted Buy Date,Basis,'
            'Adjusted Basis,Sell Date,Proceeds,Adjustment Code,Adjustment,'
            'Form Position,Buy Lot,Replacement For,Is Replacement,'
            'Loss Processed',
            '10,ABC,A,9/15/2014,9/14/2014,2000,2100,10/5/2014,1800,W,200,form1,'
            'lot1,lot3|lot4,true,true',
            '10,ABC,A,9/15/2014,,2000,,10/5/2014,1800,W,200,form2,lot2,,false,',
            '20,ABC,A,9/25/2014,,3000,,11/5/2014,1800,,,,,,'
        ]
        lots = lots_lib.Lots.create_from_csv_data(csv_data)
        expected_lots_rows = []
        expected_lots_rows.append(lots_lib.Lot(
            10, 'ABC', 'A', datetime.date(2014, 9, 15), datetime.date(
                2014, 9, 14), 2000, 2100, datetime.date(2014, 10, 5), 1800,
            'W', 200, 'form1', 'lot1', ['lot3', 'lot4'], True, True))
        expected_lots_rows.append(lots_lib.Lot(
            10, 'ABC', 'A', datetime.date(2014, 9, 15), datetime.date(
                2014, 9, 15), 2000, 2000, datetime.date(2014, 10, 5), 1800,
            'W', 200, 'form2', 'lot2', [], False, False))
        expected_lots_rows.append(lots_lib.Lot(20, 'ABC', 'A', datetime.date(
            2014, 9, 25), datetime.date(2014, 9, 25), 3000, 3000,
            datetime.date(2014, 11, 5), 1800, '', 0, '', '', [], False, False))
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
        lots_rows.append(lots_lib.Lot(
            10, 'ABC', 'A', datetime.date(2014, 9, 15), datetime.date(
                2014, 9, 14), 2000, 2100, datetime.date(2014, 10, 5), 1800,
            'W', 200, 'form1', 'lot1', ['lot3', 'lot4'], True, True))
        lots_rows.append(lots_lib.Lot(10, 'ABC', 'A', datetime.date(
            2014, 9, 15), datetime.date(2014, 9, 15), 2000, 2000,
            datetime.date(2014, 10, 5), 1800, 'W', 200, 'form2', 'lot2', [],
            False, False))
        lots_rows.append(lots_lib.Lot(20, 'ABC', 'A', datetime.date(
            2014, 9, 25), datetime.date(2014, 9, 25), 3000, 3000,
            datetime.date(2014, 11, 5), 1800, '', 0, '', '', [], False, False))
        lots = lots_lib.Lots(lots_rows)

        actual_output = StringIO.StringIO()
        lots.write_csv_data(actual_output)

        expected_csv_data = [
            'Num Shares,Symbol,Description,Buy Date,Adjusted Buy Date,Basis,'
            'Adjusted Basis,Sell Date,Proceeds,Adjustment Code,Adjustment,'
            'Form Position,Buy Lot,Replacement For,Is Replacement,'
            'Loss Processed',
            '10,ABC,A,09/15/2014,09/14/2014,2000,2100,10/05/2014,1800,W,200,'
            'form1,lot1,lot3|lot4,True,True',
            '10,ABC,A,09/15/2014,,2000,,10/05/2014,1800,W,200,form2,lot2,,,',
            '20,ABC,A,09/25/2014,,3000,,11/05/2014,1800,,,,_1,,,'
        ]

        actual_output.seek(0)
        self.assertSequenceEqual(
            [line.rstrip()
             for line in actual_output.readlines()], expected_csv_data)

    def test_load_then_write_csv_data(self):
        csv_data = [
            'Num Shares,Symbol,Description,Buy Date,Adjusted Buy Date,Basis,'
            'Adjusted Basis,Sell Date,Proceeds,Adjustment Code,Adjustment,'
            'Form Position,Buy Lot,Replacement For,Is Replacement,'
            'Loss Processed',
            '10,ABC,A,09/15/2014,09/14/2014,2000,2100,10/05/2014,1800,W,200,'
            'form1,lot1,lot3|lot4,True,True',
            '10,ABC,A,09/15/2014,,2000,,10/05/2014,1800,W,200,form2,lot2,,,',
            '20,ABC,A,09/25/2014,,3000,,11/05/2014,1800,,,,_1,,,'
        ]
        lots = lots_lib.Lots.create_from_csv_data(csv_data)
        actual_output = StringIO.StringIO()
        lots.write_csv_data(actual_output)
        actual_output.seek(0)
        self.assertSequenceEqual(
            [line.rstrip() for line in actual_output.readlines()], csv_data)

    def test_is_loss(self):
        loss_lot = lots_lib.Lot(10, 'ABC', 'A', datetime.date(2014, 9, 15),
                                datetime.date(2014, 9, 15), 2000, 2000,
                                datetime.date(2014, 10, 5), 1800, '', 0,
                                'form1', 'lot1', [], True, False)
        self.assertTrue(loss_lot.is_loss())

        gain_lot = lots_lib.Lot(10, 'ABC', 'A', datetime.date(2014, 9, 15),
                                datetime.date(2014, 9, 15), 1000, 1000,
                                datetime.date(2014, 10, 5), 1800, '', 0,
                                'form1', 'lot1', [], True, False)
        self.assertFalse(gain_lot.is_loss())

        unsold_lot = lots_lib.Lot(10, 'ABC', 'A', datetime.date(2014, 9, 15),
                                  datetime.date(2014, 9, 15), 2000, 2000, None,
                                  0, '', 0, 'form1', 'lot1', [], True, False)
        self.assertFalse(unsold_lot.is_loss())

    def test_compare_by_buy_date(self):
        lots = []
        lots.append(lots_lib.Lot(1, '', '', datetime.date(2014, 9, 2),
            datetime.date(2014, 9, 2), 0, 0, datetime.date(2014, 11, 5), 0, '',
            0, 'form2', '', [], False, False))
        lots.append(lots_lib.Lot(1, '', '', datetime.date(2014, 9, 1),
            datetime.date(2014, 9, 1), 0, 0, datetime.date(2014, 10, 5), 0, '',
            0, 'form1', '', [], False, False))
        lots.append(lots_lib.Lot(1, '', '', datetime.date(2014, 9, 2),
            datetime.date(2014, 9, 2), 0, 0, datetime.date(2014, 11, 5), 0, '',
            0, 'form1', '', [], False, False))
        lots.append(lots_lib.Lot(2, '', '', datetime.date(2014, 9, 2),
            datetime.date(2014, 9, 2), 0, 0, datetime.date(2014, 11, 5), 0, '',
            0, 'form1', '', [], False, False))
        lots.append(lots_lib.Lot(1, '', '', datetime.date(2014, 9, 3),
            datetime.date(2014, 9, 3), 0, 0, datetime.date(2014, 10, 5), 0, '',
            0, 'form1', '', [], False, False))
        lots.append(lots_lib.Lot(1, '', '', datetime.date(2014, 9, 2),
            datetime.date(2014, 9, 2), 0, 0, None, 0, '', 0, 'form1', '', [],
            False, False))
        lots.append(lots_lib.Lot(1, '', '', datetime.date(2014, 9, 2),
            datetime.date(2014, 9, 2), 0, 0, datetime.date(2014, 10, 5), 0, '',
            0, 'form1', '', [], False, False))
        lots.append(lots_lib.Lot(1, '', '', datetime.date(2014, 9, 3),
            datetime.date(2014, 9, 3), 0, 0, datetime.date(2014, 10, 6), 0, '',
            0, 'form1', '', [], False, False))

        expected = []
        expected.append(lots_lib.Lot(1, '', '', datetime.date(2014, 9, 1),
            datetime.date(2014, 9, 1), 0, 0, datetime.date(2014, 10, 5), 0, '',
            0, 'form1', '', [], False, False))
        expected.append(lots_lib.Lot(1, '', '', datetime.date(2014, 9, 2),
            datetime.date(2014, 9, 2), 0, 0, datetime.date(2014, 10, 5), 0, '',
            0, 'form1', '', [], False, False))
        expected.append(lots_lib.Lot(1, '', '', datetime.date(2014, 9, 2),
            datetime.date(2014, 9, 2), 0, 0, datetime.date(2014, 11, 5), 0, '',
            0, 'form1', '', [], False, False))
        expected.append(lots_lib.Lot(2, '', '', datetime.date(2014, 9, 2),
            datetime.date(2014, 9, 2), 0, 0, datetime.date(2014, 11, 5), 0, '',
            0, 'form1', '', [], False, False))
        expected.append(lots_lib.Lot(1, '', '', datetime.date(2014, 9, 2),
            datetime.date(2014, 9, 2), 0, 0, datetime.date(2014, 11, 5), 0, '',
            0, 'form2', '', [], False, False))
        expected.append(lots_lib.Lot(1, '', '', datetime.date(2014, 9, 2),
            datetime.date(2014, 9, 2), 0, 0, None, 0, '', 0, 'form1', '', [],
            False, False))
        expected.append(lots_lib.Lot(1, '', '', datetime.date(2014, 9, 3),
            datetime.date(2014, 9, 3), 0, 0, datetime.date(2014, 10, 5), 0, '',
            0, 'form1', '', [], False, False))
        expected.append(lots_lib.Lot(1, '', '', datetime.date(2014, 9, 3),
            datetime.date(2014, 9, 3), 0, 0, datetime.date(2014, 10, 6), 0, '',
            0, 'form1', '', [], False, False))

        lots.sort(cmp=lots_lib.Lot.cmp_by_buy_date)
        self.assertTrue(lots == expected)

    def test_compare_by_original_buy_date(self):
        # TODO: Implement this.
        pass

    def test_compare_by_sell_date(self):
        lots = []
        lots.append(lots_lib.Lot(1, '', '', datetime.date(2014, 9, 2),
            datetime.date(2014, 9, 2), 0, 0, datetime.date(2014, 11, 5), 0, '',
            0, 'form2', '', [], False, False))
        lots.append(lots_lib.Lot(1, '', '', datetime.date(2014, 9, 1),
            datetime.date(2014, 9, 1), 0, 0, datetime.date(2014, 10, 5), 0, '',
            0, 'form1', '', [], False, False))
        lots.append(lots_lib.Lot(1, '', '', datetime.date(2014, 9, 2),
            datetime.date(2014, 9, 2), 0, 0, datetime.date(2014, 11, 5), 0, '',
            0, 'form1', '', [], False, False))
        lots.append(lots_lib.Lot(2, '', '', datetime.date(2014, 9, 2),
            datetime.date(2014, 9, 2), 0, 0, datetime.date(2014, 11, 5), 0, '',
            0, 'form1', '', [], False, False))
        lots.append(lots_lib.Lot(1, '', '', datetime.date(2014, 9, 3),
            datetime.date(2014, 9, 3), 0, 0, datetime.date(2014, 10, 5), 0, '',
            0, 'form1', '', [], False, False))
        lots.append(lots_lib.Lot(1, '', '', datetime.date(2014, 9, 2),
            datetime.date(2014, 9, 2), 0, 0, None, 0, '', 0, 'form1', '', [],
            False, False))
        lots.append(lots_lib.Lot(1, '', '', datetime.date(2014, 9, 2),
            datetime.date(2014, 9, 2), 0, 0, datetime.date(2014, 10, 5), 0, '',
            0, 'form1', '', [], False, False))
        lots.append(lots_lib.Lot(1, '', '', datetime.date(2014, 9, 3),
            datetime.date(2014, 9, 3), 0, 0, datetime.date(2014, 10, 6), 0, '',
            0, 'form1', '', [], False, False))

        expected = []
        expected.append(lots_lib.Lot(1, '', '', datetime.date(2014, 9, 1),
            datetime.date(2014, 9, 1), 0, 0, datetime.date(2014, 10, 5), 0, '',
            0, 'form1', '', [], False, False))
        expected.append(lots_lib.Lot(1, '', '', datetime.date(2014, 9, 2),
            datetime.date(2014, 9, 2), 0, 0, datetime.date(2014, 10, 5), 0, '',
            0, 'form1', '', [], False, False))
        expected.append(lots_lib.Lot(1, '', '', datetime.date(2014, 9, 3),
            datetime.date(2014, 9, 3), 0, 0, datetime.date(2014, 10, 5), 0, '',
            0, 'form1', '', [], False, False))
        expected.append(lots_lib.Lot(1, '', '', datetime.date(2014, 9, 3),
            datetime.date(2014, 9, 3), 0, 0, datetime.date(2014, 10, 6), 0, '',
            0, 'form1', '', [], False, False))
        expected.append(lots_lib.Lot(1, '', '', datetime.date(2014, 9, 2),
            datetime.date(2014, 9, 2), 0, 0, datetime.date(2014, 11, 5), 0, '',
            0, 'form1', '', [], False, False))
        expected.append(lots_lib.Lot(2, '', '', datetime.date(2014, 9, 2),
            datetime.date(2014, 9, 2), 0, 0, datetime.date(2014, 11, 5), 0, '',
            0, 'form1', '', [], False, False))
        expected.append(lots_lib.Lot(1, '', '', datetime.date(2014, 9, 2),
            datetime.date(2014, 9, 2), 0, 0, datetime.date(2014, 11, 5), 0, '',
            0, 'form2', '', [], False, False))
        expected.append(lots_lib.Lot(1, '', '', datetime.date(2014, 9, 2),
            datetime.date(2014, 9, 2), 0, 0, None, 0, '', 0, 'form1', '', [],
            False, False))

        lots.sort(cmp=lots_lib.Lot.cmp_by_sell_date)
        self.assertTrue(lots == expected)

    def test_contents_equal(self):
        lots = lots_lib.Lots([])
        lots.add(lots_lib.Lot(1, '', '', datetime.date(2014, 9, 2),
            datetime.date(2014, 9, 2), 0, 0, datetime.date(2014, 11, 5), 0, '',
            0, 'form2', '', [], False, False))
        lots.add(lots_lib.Lot(5, '', '', datetime.date(2014, 9, 1),
            datetime.date(2014, 9, 1), 0, 0, datetime.date(2014, 10, 5), 0, '',
            0, 'form1', '', [], False, False))
        lots.add(lots_lib.Lot(3, '', '', datetime.date(2014, 9, 2),
            datetime.date(2014, 9, 2), 0, 0, datetime.date(2014, 11, 5), 0, '',
            0, 'form1', '', [], False, False))
        self.assertTrue(lots.contents_equal(lots))

        other_lots = copy.deepcopy(lots)
        self.assertTrue(lots.contents_equal(other_lots))

    def test_contents_not_equal(self):
        lots = lots_lib.Lots([])
        lots.add(lots_lib.Lot(1, '', '', datetime.date(2014, 9, 2),
            datetime.date(2014, 9, 2), 0, 0, datetime.date(2014, 11, 5), 0, '',
            0, 'form2', '', [], False, False))
        lots.add(lots_lib.Lot(5, '', '', datetime.date(2014, 9, 1),
            datetime.date(2014, 9, 1), 0, 0, datetime.date(2014, 10, 5), 0, '',
            0, 'form1', '', [], False, False))
        lots.add(lots_lib.Lot(3, '', '', datetime.date(2014, 9, 2),
            datetime.date(2014, 9, 2), 0, 0, datetime.date(2014, 11, 5), 0, '',
            0, 'form1', '', [], False, False))

        other_lots = copy.deepcopy(lots)
        other_lots.lots()[0].num_shares = 2
        self.assertFalse(lots.contents_equal(other_lots))


if __name__ == '__main__':
    unittest.main()
