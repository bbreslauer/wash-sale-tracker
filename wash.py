import argparse
import copy
import datetime
import lots as lots_lib

def _split_lot(num_shares, lot, lots):
    """Splits lot and adds the new lot to lots.

    Args:
        num_shares: An integer, the number of shares that the lot should be
            split into.
        lot: A Lot object to split.
        lots: A Lots object to add the new lot to.
    """
    new_lot = copy.deepcopy(lot)
    new_lot.num_shares -= num_shares
    lot.num_shares = num_shares
    lots.add(new_lot)

def best_replacement_lot(loss_lot, lots):
    """Finds the best replacement lot for a loss lot.

    If a replacement lot has fewer shares than the loss lot, then the loss lot
    will be split in two. The existing Lot will be adjusted to have the same
    number of shares as the replacement lot, and the other split will be added
    to lots and can be processed later.

    Args:
        loss_lot: A Lot object, which is a loss that should be washed.
        lots: A Lots object, the full set of lots.
    Returns:
        A Lot object, the best replacement lot, or None if there is none. If
        not None, then this lot will be for <= the number of shares of the
        loss_lot.
    """
    # Replacement lots must be chosen oldest first.
    lots.sort(cmp=lots_lib.Lot.cmp_by_buy_date)
    possible_replacement_lots = []
    for lot in lots:
        if abs(loss_lot.sell_date - lot.buy_date) > datetime.timedelta(days=30):
            # A replacement lot must be within 61 days (30 before, day of, and
            # 30 after) of the sale.
            continue
        if loss_lot is lot or (loss_lot.buy_lot != '' and
                               loss_lot.buy_lot == lot.buy_lot):
            # A lot cannot wash against itself.
            continue
        if lot.is_replacement:
            # This lot was already used as a replacement lot, and a lot can
            # only be used as a replacement once, per 26 CFR 1.1091-1(e) (the
            # "one bite of the apple" rule).
            continue
        possible_replacement_lots.append(lot)

    if not possible_replacement_lots:
        return None

    # At this point, we have found all the lots that could be replacements,
    # sorted by buy date. We need to choose the one that was purchased first,
    # but in the case of multiple lots being purchased on the same (first) day
    # and also sold on the same day (though the purchase and sale dates may be
    # different), why not choose one that matches (or is greater than) the
    # number of loss shares, so that we don't create more splits than necessary.
    #
    # For instance, if we have a loss of 10 shares, and 2 purchases on the same
    # day, one for 5 shares and one for 12 shares, we might as well pair with
    # the 12 shares. This means that we'll split the 12 shares into two lots, a
    # 10-share one and a 2-share one. If we had instead chosen the 5 share lot,
    # then we'd split the loss lot into two 5-share lots, and then need to pair
    # the second 5-share loss lot with the 12-share lot, which would involve
    # another split.
    #
    # Note that the requirement here that the lots are sold on the same day is
    # not backed up by anything in Pub550, as far as I know. It just seems
    # reasonable that the first sold stock is more reasonably replacement
    # stock.

    first_day_lots = []
    first_buy_date = possible_replacement_lots[0].buy_date
    first_sell_date = possible_replacement_lots[0].sell_date
    for lot in possible_replacement_lots:
        if lot.buy_date == first_buy_date and lot.sell_date == first_sell_date:
            first_day_lots.append(lot)

    if len(first_day_lots) == 1:
        lot = first_day_lots[0]
        if lot.num_shares > loss_lot.num_shares:
            _split_lot(loss_lot.num_shares, lot, lots)
        return lot

    # If we have gotten here, then we know that there are at least 2 lots to
    # choose from. Choose the one with the same number of shares as the loss,
    # or the smallest number of shares greater than the loss.
    first_day_lots.sort(lots_lib.Lot.cmp_by_num_shares)
    for lot in first_day_lots:
        if lot.num_shares < loss_lot.num_shares:
            continue
        if lot.num_shares > loss_lot.num_shares:
            _split_lot(loss_lot.num_shares, lot, lots)
        return lot

    # If we have gotten here, then there is no replacement lot that has at
    # least as many shares as the loss. Return the lot with the largest number
    # of replacement shares (the rest of the loss will be washed later).
    return first_day_lots[-1]

def earliest_loss_lot(lots):
    """Finds the first loss sale that has not already been processed.

    Args:
        lots: A Lots object, the full set of lots to search through.
    Returns:
        A Lot, or None.
    """
    lots.sort(cmp=lots_lib.Lot.cmp_by_sell_date)
    for lot in lots:
        if not lot.is_loss():
            continue
        if lot.loss_processed:
            continue
        return lot
    return None

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
        loss_lot = earliest_loss_lot(lots)
        if not loss_lot:
            break
        wash_one_lot(loss_lot, lots)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-o', '--out_file')
    parser.add_argument('-w', '--do_wash', metavar='in_file')
    parsed = parser.parse_args()

    # TODO sort before printing
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
