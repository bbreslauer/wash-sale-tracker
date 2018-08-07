import copy
import csv
import datetime

_HAS_TERMINALTABLES = False
try:
    import terminaltables
    _HAS_TERMINALTABLES = True
except ImportError:
    print 'Install terminaltables library for formatting tables.'

_HAS_COLORCLASS = False
try:
    import colorclass
    _HAS_COLORCLASS = True
except ImportError:
    print 'Install colorclass library for color coding changes.'


# This is a global value for the number of lots that have been created. It is
# global because we want to increment it whenever a Lot object is created,
# which is done in a number of different places.
_LOT_COUNT = 0


class BadHeadersError(Exception):
    """Raised if the headers that are parsed are not in the correct format."""


class Lot(object):
    """Models a single lot of stock."""

    # A list of the field names for a Lot.
    FIELD_NAMES = ['num_shares', 'symbol', 'description', 'buy_date',
                   'adjusted_buy_date', 'basis', 'adjusted_basis', 'sell_date',
                   'proceeds', 'adjustment_code', 'adjustment',
                   'form_position', 'buy_lot', 'replacement_for',
                   'is_replacement', 'loss_processed']

    def __init__(self, num_shares, symbol, description, buy_date,
                 adjusted_buy_date, basis, adjusted_basis, sell_date, proceeds,
                 adjustment_code, adjustment, form_position, buy_lot,
                 replacement_for, is_replacement, loss_processed):
        """Initializes a lot.

        Args:
            num_shares: An integer.
            symbol: A string, the stock symbol.
            description: A string, an arbitrary description of this lot.
            buy_date: A datetime.date, the original buy date of the shares.
            adjusted_buy_date: A datetime.date, the possibly-adjusted buy date
                of the shares.
            basis: An integer, the number of cents that the lot was bought for.
            adjusted_basis: An integer, the possibly-adjusted number of cents
                that the lot was bought for.
            sell_date: A datetime.date or None.
            proceeds: An integer, the number of cents that the lot was sold
                for, or 0 if the lot is not sold.
            adjustment_code: A string, basically 'W' in case this was a wash
                sale.
            adjustment: An integer, the number of cents of the disallowed loss,
                or 0 if the lot is not sold.
            form_position: A string, an arbitrary value that helps to determine
                which lots are related when a lot is split.
            buy_lot: A string, an arbitrary value that indicates that can be
                used to indicate that multiple entries are part of the same
                logical lot. An empty string indicates that this is a unique
                lot.
            replacement_for: A list of strings, possibly empty, the buy lots,
                possibly a chain of them, that this is a replacement for.
            is_replacement: A boolean, if true then this lot has been used as
                replacement shares. Useful because a lot can only be used as
                replacement shares once.
            loss_processed: A boolean, whether this lot is a loss and has
                already been processed for a potential wash sale.
        """
        self.num_shares = num_shares
        self.symbol = symbol
        self.description = description
        self.buy_date = buy_date
        self.adjusted_buy_date = adjusted_buy_date
        self.basis = basis
        self.adjusted_basis = adjusted_basis
        self.sell_date = sell_date
        self.proceeds = proceeds
        self.adjustment_code = adjustment_code
        self.adjustment = adjustment
        self.form_position = form_position
        self.buy_lot = buy_lot
        self.replacement_for = replacement_for
        self.is_replacement = is_replacement
        self.loss_processed = loss_processed

        # The lot number is only used to sort otherwise equivalent lots.
        global _LOT_COUNT
        self._lot_number = _LOT_COUNT
        _LOT_COUNT += 1

    def is_loss(self):
        """Determines whether this lot is a loss.

        Returns:
            True if this lot was sold for a loss. False if it was sold for a
            gain, or it has not been sold.
        """
        if self.sell_date and self.proceeds < self.adjusted_basis:
            return True
        return False

    def __eq__(self, other):
        return (self.num_shares == other.num_shares and
                self.symbol == other.symbol and
                self.description == other.description and
                self.buy_date == other.buy_date and
                self.adjusted_buy_date == other.adjusted_buy_date and
                self.basis == other.basis and
                self.adjusted_basis == other.adjusted_basis and
                self.sell_date == other.sell_date and
                self.proceeds == other.proceeds and
                self.adjustment_code == other.adjustment_code and
                self.adjustment == other.adjustment and
                self.form_position == other.form_position and
                self.buy_lot == other.buy_lot and
                self.replacement_for == other.replacement_for and
                self.is_replacement == other.is_replacement and
                self.loss_processed == other.loss_processed)

    def __ne__(self, other):
        return not self == other

    def __str__(self):
        return ' '.join(self.str_data())

    __repl__ = __str__

    def str_data(self):
        return ['{:d}'.format(self.num_shares),
                '{}'.format(self.symbol),
                '{}'.format(self.description),
                '{}'.format(self.buy_date),
                '{}'.format(self.adjusted_buy_date),
                '${:.2f}'.format(float(self.basis) / 100),
                '${:.2f}'.format(float(self.adjusted_basis) / 100),
                '{}'.format(self.sell_date),
                '${:.2f}'.format(float(self.proceeds) / 100),
                '{}'.format(self.adjustment_code),
                '${:.2f}'.format(float(self.adjustment) / 100),
                '{}'.format(self.form_position),
                '{}'.format(self.buy_lot),
                '{}'.format(','.join(self.replacement_for)),
                '{}'.format(self.is_replacement),
                '{}'.format(self.loss_processed)]

    @staticmethod
    def cmp_by_buy_date(a, b):
        """Sorts two lots based on their (possibly adjusted) buy dates."""
        if a.adjusted_buy_date != b.adjusted_buy_date:
            return (a.adjusted_buy_date - b.adjusted_buy_date).days
        if a.sell_date != b.sell_date:
            if a.sell_date is None:
                return 1
            if b.sell_date is None:
                return -1
            return (a.sell_date - b.sell_date).days
        if a.form_position != b.form_position:
            if a.form_position < b.form_position:
                return -1
            return 1
        return a._lot_number < b._lot_number

    @staticmethod
    def cmp_by_original_buy_date(a, b):
        """Sorts two lots based on their original buy dates."""
        if a.buy_date != b.buy_date:
            return (a.buy_date - b.buy_date).days
        if a.sell_date != b.sell_date:
            if a.sell_date is None:
                return 1
            if b.sell_date is None:
                return -1
            return (a.sell_date - b.sell_date).days
        if a.form_position != b.form_position:
            if a.form_position < b.form_position:
                return -1
            return 1
        return a._lot_number < b._lot_number

    @staticmethod
    def cmp_by_sell_date(a, b):
        """Sorts two lots based on their sell dates."""
        if a.sell_date != b.sell_date:
            if a.sell_date is None:
                return 1
            if b.sell_date is None:
                return -1
            return (a.sell_date - b.sell_date).days
        if a.buy_date != b.buy_date:
            return (a.buy_date - b.buy_date).days
        if a.form_position != b.form_position:
            if a.form_position < b.form_position:
                return -1
            return 1
        return a._lot_number < b._lot_number


class Lots(object):
    """Contains a set of lots."""

    # A map of Lot field name to CSV header value.
    HEADERS = {
        'num_shares': 'Num Shares',
        'symbol': 'Symbol',
        'description': 'Description',
        'buy_date': 'Buy Date',
        'adjusted_buy_date': 'Adjusted Buy Date',
        'basis': 'Basis',
        'adjusted_basis': 'Adjusted Basis',
        'sell_date': 'Sell Date',
        'proceeds': 'Proceeds',
        'adjustment_code': 'Adjustment Code',
        'adjustment': 'Adjustment',
        'form_position': 'Form Position',
        'buy_lot': 'Buy Lot',
        'replacement_for': 'Replacement For',
        'is_replacement': 'Is Replacement',
        'loss_processed': 'Loss Processed'
    }

    # A map of Lot field name to short strings naming the column.
    SHORT_HEADERS = {
        'num_shares': 'Num',
        'symbol': 'Symb',
        'description': 'Desc',
        'buy_date': 'BuyDate',
        'adjusted_buy_date': 'AdjBuyDate',
        'basis': 'Basis',
        'adjusted_basis': 'AdjBasis',
        'sell_date': 'Sell Date',
        'proceeds': 'Proceeds',
        'adjustment_code': 'AdjCode',
        'adjustment': 'Adj',
        'form_position': 'Pos',
        'buy_lot': 'BuyLot',
        'replacement_for': 'ReplFor',
        'is_replacement': 'IsRepl',
        'loss_processed': 'Processed'
    }

    def __init__(self, lots):
        """Creates a new set of lots.

        Populates the buy_lot field in each lot if it is not set.

        Args:
            lots: A list of Lot objects.
        """
        i = 1
        for lot in lots:
            if not lot.buy_lot:
                lot.buy_lot = '_{}'.format(i)
                i += 1
        self._lots = lots

    def lots(self):
        """Returns the list of Lot objects."""
        return self._lots

    def add(self, lot):
        """Adds a lot to this object.

        Args:
            lot: The Lot to add.
        """
        self._lots.append(lot)

    def size(self):
        """Returns the number of lots."""
        return len(self._lots)

    def sort(self, **kwargs):
        self._lots.sort(**kwargs)

    def contents_equal(self, other):
        """Returns True if the individual lots are the same.

        This is different than __eq__ because the individual Lot objects do not
        need to have the same id(), just be equivalent.
        """
        for this, that in zip(self._lots, other._lots):
            if this != that:
                return False
        return True

    def __eq__(self, other):
        if len(self._lots) != len(other._lots):
            return False
        for lot in self._lots:
            if lot not in other._lots:
                return False
        return True

    def __ne__(self, other):
        return not self == other

    def __str__(self):
        global _HAS_TERMINALTABLES
        if _HAS_TERMINALTABLES:
            return self._terminaltables_str()
        else:
            return self._simple_str()

    def __iter__(self):
        return iter(self._lots)

    def do_print(self,
                 loss_lots=None,
                 split_off_loss_lots=None,
                 replacement_lots=None,
                 split_off_replacement_lots=None):
        global _HAS_TERMINALTABLES
        if _HAS_TERMINALTABLES:
            print self._terminaltables_str(loss_lots, split_off_loss_lots,
                                           replacement_lots,
                                           split_off_replacement_lots)
        else:
            print self._simple_str(loss_lots, split_off_loss_lots,
                                   replacement_lots,
                                   split_off_replacement_lots)

    @staticmethod
    def _classify_lot(lot,
                      loss_lots=None,
                      split_off_loss_lots=None,
                      replacement_lots=None,
                      split_off_replacement_lots=None):
        """Classifies the provided lot based on the lists of lots provided.

        Args:
            lot: A Lot to classify.
            loss_lots: A list of Lot objects.
            split_off_loss_lots: A list of Lot objects.
            replacement_lots: A list of Lot objects.
            split_off_replacement_lots: A list of Lot objects.

        Returns:
            (characters, color) or ()
            characters: A string containing classification characters, like * .
            color: A string containing the color to highlight the lot as.
        """
        characters = ''
        color = ''
        if loss_lots and id(lot) in map(id, loss_lots):
            characters += '*'
            color = 'red'
        elif split_off_loss_lots and id(lot) in map(id, split_off_loss_lots):
            characters += 'x'
            color = 'magenta'
        elif replacement_lots and id(lot) in map(id, replacement_lots):
            characters += 'o'
            color = 'green'
        elif split_off_replacement_lots and id(lot) in map(
                id, split_off_replacement_lots):
            characters += '+'
            color = 'blue'

        if characters or color:
            return (characters, color)
        return ()

    @staticmethod
    def _color_string(color, s):
        """Colors a string, if colorclass is imported.

        Args:
            color: A string representing the color.
            s: A string to color.
        Returns:
            A possibly-colorized string.
        """
        if _HAS_COLORCLASS:
            return colorclass.Color('{' + color + '}' + s + '{/' + color + '}')
        return s

    def _terminaltables_str(self,
                            loss_lots=None,
                            split_off_loss_lots=None,
                            replacement_lots=None,
                            split_off_replacement_lots=None):
        """Generates an ASCII table of this Lots object.

        Any lots in the optional lists are highlighted.

        Args:
            loss_lots: A list of Lot objects.
            split_off_loss_lots: A list of Lot objects.
            replacement_lots: A list of Lot objects.
            split_off_replacement_lots: A list of Lot objects.
        Returns:
            A string representing this Lots object.
        """
        # Make a shallow copy so that we can sort but id(lot) still works.
        lots = copy.copy(self._lots)
        lots.sort(cmp=Lot.cmp_by_original_buy_date)
        lots_data = [[self.SHORT_HEADERS[field] for field in Lot.FIELD_NAMES]]
        lots_data[0].append('Matched')
        for lot in lots:
            str_data = lot.str_data()
            classification = Lots._classify_lot(
                lot, loss_lots, split_off_loss_lots, replacement_lots,
                split_off_replacement_lots)
            if classification:
                str_data.append(classification[0])
                color = classification[1]
                str_data = map(lambda x: Lots._color_string(color, x), str_data)
            else:
                str_data.append('')
            lots_data.append(str_data)
        return terminaltables.AsciiTable(lots_data).table

    def _simple_str(self,
                    loss_lots=None,
                    split_off_loss_lots=None,
                    replacement_lots=None,
                    split_off_replacement_lots=None):
        # Make a shallow copy so that we can sort but id(lot) still works.
        lots = copy.copy(self._lots)
        lots.sort(cmp=Lot.cmp_by_original_buy_date)
        lot_strings = []
        lot_strings.append(' '.join([self.SHORT_HEADERS[field]
                                     for field in Lot.FIELD_NAMES]))
        for lot in lots:
            classification = Lots._classify_lot(
                lot, loss_lots, split_off_loss_lots, replacement_lots,
                split_off_replacement_lots)
            str_data = str(lot)
            if classification:
                str_data = classification[0] + ' ' + str_data
                color = classification[1]
                str_data = Lots._color_string(color, str_data)
            lot_strings.append(str_data)
        return '\n'.join(lot_strings)

    __repl__ = __str__

    @staticmethod
    def create_from_csv_data(data):
        """Creates a Lots object based on a multi-line string of csv data.

        The first line of the csv file must contain headers, which are the
        values of the HEADERS dict in order. All other lines should contain the
        values. See the test data for examples.

        Args:
            data: A list of strings, where each line is a CSV row that matches
                    the format above
        Returns:
            A Lots object
        """

        def convert_to_int(value):
            if value:
                return int(value)
            return 0

        def convert_to_date(value):
            if value:
                return datetime.datetime.strptime(value, '%m/%d/%Y').date()
            return None

        def convert_to_bool(value):
            if value:
                return value.lower() == 'true'
            return False

        def convert_to_string_list(value):
            if value:
                return value.split(';')
            return []

        reader = csv.DictReader(data, fieldnames=Lot.FIELD_NAMES)
        header_row = reader.next()
        if header_row != Lots.HEADERS:
            raise BadHeadersError(str(header_row) + str(Lots.HEADERS))
        lots = []
        for row in reader:
            row['num_shares'] = convert_to_int(row['num_shares'])
            row['buy_date'] = convert_to_date(row['buy_date'])
            row['adjusted_buy_date'] = convert_to_date(row['adjusted_buy_date'])
            if not row['adjusted_buy_date']:
                row['adjusted_buy_date'] = copy.deepcopy(row['buy_date'])
            row['basis'] = convert_to_int(row['basis'])
            row['adjusted_basis'] = convert_to_int(row['adjusted_basis'])
            if not row['adjusted_basis']:
                row['adjusted_basis'] = row['basis']
            row['sell_date'] = convert_to_date(row['sell_date'])
            row['proceeds'] = convert_to_int(row['proceeds'])
            row['adjustment'] = convert_to_int(row['adjustment'])
            row['replacement_for'] = convert_to_string_list(row[
                'replacement_for'])
            row['is_replacement'] = convert_to_bool(row['is_replacement'])
            row['loss_processed'] = convert_to_bool(row['loss_processed'])
            lots.append(Lot(**row))
        return Lots(lots)

    def write_csv_data(self, output_file):
        """Writes this lots data as CSV data to an output file.

        Args:
            output_file: A file-like object to write to.
        """

        def convert_from_int(value):
            if value:
                return str(value)
            return ''

        def convert_from_date(value):
            if value:
                return value.strftime('%m/%d/%Y')
            return ''

        def convert_from_bool(value):
            if value:
                return 'True'
            return ''

        def convert_from_string_list(value):
            if value:
                return ';'.join(value)
            return ''

        writer = csv.DictWriter(output_file, fieldnames=Lot.FIELD_NAMES)
        writer.writerow(self.HEADERS)
        for lot in self._lots:
            row = {}
            row['num_shares'] = convert_from_int(lot.num_shares)
            row['symbol'] = lot.symbol
            row['description'] = lot.description
            row['buy_date'] = convert_from_date(lot.buy_date)
            if lot.buy_date == lot.adjusted_buy_date:
                row['adjusted_buy_date'] = ''
            else:
                row['adjusted_buy_date'] = convert_from_date(
                    lot.adjusted_buy_date)
            row['basis'] = convert_from_int(lot.basis)
            if lot.basis == lot.adjusted_basis:
                row['adjusted_basis'] = ''
            else:
                row['adjusted_basis'] = convert_from_int(lot.adjusted_basis)
            row['sell_date'] = convert_from_date(lot.sell_date)
            row['proceeds'] = convert_from_int(lot.proceeds)
            row['adjustment_code'] = lot.adjustment_code
            row['adjustment'] = convert_from_int(lot.adjustment)
            row['form_position'] = lot.form_position
            row['buy_lot'] = lot.buy_lot
            row['replacement_for'] = convert_from_string_list(
                lot.replacement_for)
            row['is_replacement'] = convert_from_bool(lot.is_replacement)
            row['loss_processed'] = convert_from_bool(lot.loss_processed)
            writer.writerow(row)
