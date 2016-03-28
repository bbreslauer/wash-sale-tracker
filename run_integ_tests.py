import lots as lots_lib
import wash as wash_lib

import os


def run_test(infile, outfile):
    """Runs a single test.

    Args:
        infile: Input filename.
        outfile: Expected output filename.
    """
    lots = lots_lib.Lots.create_from_csv_data(open(infile))
    wash_lib.wash_all_lots(lots)
    expected = lots_lib.Lots.create_from_csv_data(open(outfile))
    lots.sort(cmp=lots_lib.Lot.cmp_by_buy_date)
    expected.sort(cmp=lots_lib.Lot.cmp_by_buy_date)
    if lots.contents_equal(expected):
        print 'Test failed: {}'.format(infile)
        print 'Got result:'
        lots.do_print()
        print 'Expected:'
        expected.do_print()
        print '\n\n'
    else:
        print "Test passed: {}".format(infile)


def main():
    tests_dir = os.path.join(os.getcwd(), 'tests')
    tests = [name
             for name in os.listdir(tests_dir)
             if name.endswith('.csv') and not name.endswith('_out.csv')]
    for test in tests:
        run_test(os.path.join(tests_dir, test),
             os.path.join(tests_dir, test.rsplit('.', 1)[0] + "_out.csv"))

if __name__ == "__main__":
  main()
