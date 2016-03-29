import abc


class Logger(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def print_lots(self,
                   message,
                   lots,
                   loss_lots=None,
                   split_off_loss_lots=None,
                   replacement_lots=None,
                   split_off_replacement_lots=None):
        """Prints out the lots, along with the provided message.

        Args:
            message: A string to print before the lots.
            lots: A Lots object.
            loss_lots: A list of Lot objects to highlight.
            split_off_loss_lots: A list of Lot objects to highlight.
            replacement_lots: A list of Lot objects to highlight.
            split_off_replacement_lots: A list of Lot objects to highlight.
        """
        raise NotImplementedError()


class TermLogger(Logger):
    def print_lots(self,
                   message,
                   lots,
                   loss_lots=None,
                   split_off_loss_lots=None,
                   replacement_lots=None,
                   split_off_replacement_lots=None):
        print ''
        lots.do_print(loss_lots, split_off_loss_lots, replacement_lots,
                      split_off_replacement_lots)
        raw_input(message + '. Hit enter to continue>')


class NullLogger(Logger):
    def print_lots(self,
                   message,
                   lots,
                   loss_lots=None,
                   split_off_loss_lots=None,
                   replacement_lots=None,
                   split_off_replacement_lots=None):
        pass
