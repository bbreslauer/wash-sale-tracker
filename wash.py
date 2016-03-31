import argparse
import copy
import datetime
import lots as lots_lib
import logger as logger_lib

def _split_lot(num_shares, lot, lots, logger, type_of_lot):
    """Splits lot and adds the new lot to lots.

    Args:
        num_shares: An integer, the number of shares that lot should contain.
            The split out lot will contain lot.num_shares - num_shares.
        lot: A Lot object to split.
        lots: A Lots object to add the new lot to.
        logger: A logger_lib.Logger.
        type_of_lot: Either 'loss' or 'replacement'
    """
    existing_lot_portion = float(num_shares) / float(lot.num_shares)
    new_lot_portion = float(lot.num_shares - num_shares) / float(lot.num_shares)

    new_lot = copy.deepcopy(lot)
    new_lot.num_shares -= num_shares
    new_lot.basis = int(round(new_lot.basis * new_lot_portion))
    new_lot.adjusted_basis = int(round(new_lot.adjusted_basis *
                                       new_lot_portion))
    new_lot.proceeds = int(round(new_lot.proceeds * new_lot_portion))
    new_lot.adjustment = int(round(new_lot.adjustment * new_lot_portion))
    lots.add(new_lot)

    lot.num_shares = num_shares
    lot.basis = int(round(lot.basis * existing_lot_portion))
    lot.adjusted_basis = int(round(lot.adjusted_basis * existing_lot_portion))
    lot.proceeds = int(round(lot.proceeds * existing_lot_portion))
    lot.adjustment = int(round(lot.adjustment * existing_lot_portion))

    loss_lots = [lot] if type_of_lot == 'loss' else []
    split_off_loss_lots = [new_lot] if type_of_lot == 'loss' else []
    replacement_lots = [lot] if type_of_lot == 'replacement' else []
    split_off_replacement_lots = [new_lot
                                  ] if type_of_lot == 'replacement' else []
    logger.print_lots('Split {} in two'.format(type_of_lot),
                      lots,
                      loss_lots=loss_lots,
                      split_off_loss_lots=split_off_loss_lots,
                      replacement_lots=replacement_lots,
                      split_off_replacement_lots=split_off_replacement_lots)

def best_replacement_lot(loss_lot, lots):
    """Finds the best replacement lot for a loss lot.

    The search starts from the earliest buy, and continues forward in time. A
    replacement lot must be within 30 days on either side of the loss sale, not
    be part of the same lot, and not already have been used as a replacement.
    If there is only one lot bought on the first such day, then that is
    returned. It may be for fewer, the same, or more shares than the loss lot.
    If there are multiple lots bought on the first such day, then the one sold
    earliest is chosen. If there are multiple lots bought and sold on the same
    day, then the first lot by form position is chosen. For this reason, it is
    best to set a unique form position for each input line.

    If a potential replacement lot is sold before the loss lot is sold, that
    potential replacement lot is not considered. The reason for this is that it
    can push a loss arbitrarily far in the past, which means that it would be
    possible that subsequent year's tax returns would need to be amended. This
    seems wrong, so we don't allow for it. But there doesn't seem to be any IRS
    ruling on this issue, so it's up in the air whether this would present a
    problem. But IANACPA/IANAL.

    Args:
        loss_lot: A Lot object, which is a loss that should be washed.
        lots: A Lots object, the full set of lots.
    Returns:
        A Lot object, the best replacement lot, or None if there is none. May
        have more or fewer shares than the loss_lot.
    """
    # Replacement lots must be chosen oldest first.
    lots.sort(cmp=lots_lib.Lot.cmp_by_original_buy_date)
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
        if lot.buy_lot in loss_lot.replacement_for:
            # If the loss_lot was already a replacement for the lot, then don't
            # also replace in the other direction.  This prevents a loop so
            # that if you have two losses A and B, then B is a replacement for
            # A, or A is a replacement for B, but they are not both
            # replacements.
            continue
        if lot.sell_date and lot.sell_date < loss_lot.sell_date:
            # Don't select lots that were sold before the loss. See the
            # docstring for the reasoning behind this.
            continue
        possible_replacement_lots.append(lot)

    if not possible_replacement_lots:
        return None
    return possible_replacement_lots[0]

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

def wash_one_lot(loss_lot, lots, logger=logger_lib.NullLogger()):
    """Performs a single wash.

    Given a single loss lot, finds replacement lot(s) and adjusts their basis
    and buy date in place.

    If the loss lot needs to be split into multiple parts (because the
    replacement lots are for fewer shares) then it will be split into two parts
    and the wash will be performed for only the first part. The second part can
    be taken care of by another call to this method with it passed in as the
    loss_lot.

    If the replacement lot needs to be split into multiple parts (because the
    replacement lot has more shares than the loss lot) then it will be split
    and the second part of the lot will be added to lots.

    A replacement lot is one that is purchased within 30 days of the loss_lot's
    sale, not already used as a replacement, and not part of the same lot as
    the loss_lot.

    Args:
        loss_lot: A Lot object, which is a loss that should be washed.
        lots: A Lots object, the full set of lots.
        logger: A logger_lib.Logger.
    """
    replacement_lot = best_replacement_lot(loss_lot, lots)
    if not replacement_lot:
        logger.print_lots('No replacement lot', lots, loss_lots=[loss_lot])
        loss_lot.loss_processed = True
        return

    logger.print_lots('Found replacement lot',
                      lots,
                      loss_lots=[loss_lot],
                      replacement_lots=[replacement_lot])

    # There is a replacement lot. If it is not for the same number of shares as
    # the loss lot, split the larger one.
    if loss_lot.num_shares > replacement_lot.num_shares:
        _split_lot(replacement_lot.num_shares, loss_lot, lots, logger, 'loss')
    elif replacement_lot.num_shares > loss_lot.num_shares:
        _split_lot(loss_lot.num_shares, replacement_lot, lots, logger,
                   'replacement')

    # Now the loss_lot and replacement_lot have the same number of shares.
    loss_lot.loss_processed = True
    loss_lot.adjustment_code = 'W'
    loss_lot.adjustment = loss_lot.adjusted_basis - loss_lot.proceeds
    replacement_lot.is_replacement = True
    replacement_lot.replacement_for.extend(loss_lot.replacement_for)
    replacement_lot.replacement_for.append(loss_lot.buy_lot)
    replacement_lot.adjusted_basis += loss_lot.adjustment
    replacement_lot.adjusted_buy_date -= (
        loss_lot.sell_date - loss_lot.adjusted_buy_date)

    logger.print_lots('Adjusted basis and buy date',
                      lots,
                      loss_lots=[loss_lot],
                      replacement_lots=[replacement_lot])

def wash_all_lots(lots, logger=logger_lib.NullLogger()):
    """Performs wash sales of all the lots.

    Args:
        lots: A Lots object.
        logger: A logger_lib.Logger.
    """
    while True:
        loss_lot = earliest_loss_lot(lots)
        if not loss_lot:
            break
        logger.print_lots('Found loss', lots, loss_lots=[loss_lot])
        wash_one_lot(loss_lot, lots, logger)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-o', '--out_file')
    parser.add_argument('-w', '--do_wash', metavar='in_file')
    parsed = parser.parse_args()

    logger = logger_lib.TermLogger()
    if parsed.do_wash:
        lots = lots_lib.Lots([])
        with open(parsed.do_wash) as f:
            lots = lots_lib.Lots.create_from_csv_data(f)
        logger.print_lots('Start lots', lots)
        wash_all_lots(lots, logger)
        if parsed.out_file:
            with open(parsed.out_file, 'w') as f:
                lots.write_csv_data(f)
        else:
            logger.print_lots('Final lots', lots)


if __name__ == "__main__":
    main()
