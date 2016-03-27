import argparse
import lots as lots_lib

def best_replacement_lot(loss_lot, lots):
    """Finds the best replacement lot for a loss lot.

    If a replacement lot has fewer shares than the loss lot, then the loss lot
    will be split in two. The existing Lot will be adjusted to have the same
    number of shares as the replacement lot, and the other split will be added
    to lots.

    Args:
        loss_lot: A Lot object, which is a loss that should be washed.
        lots: A Lots object, the full set of lots.
    Returns:
        A Lot object, the best replacement lot.
    """

def earliest_unprocessed_loss_lot(lots):
    """Finds the earliest loss lot that has not already been processed.

    Args:
        lots: A Lots object, the full set of lots to search through.
    Returns:
        A Lot, or None.
    """
    #lots.lots().sort(cmp=lots_lib.Lots.cmp_by_buy_date)
    #for lot in lots.lots():

def wash_one_lot(loss_lot, lots):
    """Performs a single wash.

    Given a single loss lot, finds replacement lot(s) and adjusts their basis
    and buy date in place. If the loss lot needs to be split into multiple
    parts (because the replacement lots are for fewer shares) then it will be
    split into two parts and the wash will be performed for only the first
    part. The second part can be taken care of by another call to this method
    with it passed in as the loss_lot.

    A replacement lot is one that is purchased within 30 days of the loss_lot's
    sale, not already used as a replacement, and not part of the same lot as
    the loss_lot.

    Args:
        loss_lot: A Lot object, which is a loss that should be washed.
        lots: A Lots object, the full set of lots.
    """

def wash_all_lots(lots):
    """Performs wash sales of all the lots.

    Args:
        lots: A Lots object.
    """
    while True:
        loss_lot = earliest_unprocessed_loss_lot(lots)
        if not loss_lot:
            break
        wash_one_lot(loss_lot, lots)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-o', '--out_file')
    parser.add_argument('-w', '--do_wash', metavar='in_file')
    parsed = parser.parse_args()

    if parsed.do_wash:
        lots = lots_lib.Lots([])
        with open(parsed.do_wash) as f:
            lots = lots_lib.Lots.create_from_csv_data(f)
        print 'Start lots:'
        lots.do_print()
        wash_all_lots(lots)
        if parsed.out_file:
            with open(parsed.out_file, 'w') as f:
                lots.write_csv_data(f)
        else:
            print 'Final lots:'
            lots.do_print()


if __name__ == "__main__":
    main()
