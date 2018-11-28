class FullQueueException(Exception):
    def __init__(self, err="full queue"):
        super(FullQueueException, self).__init__(err)


class EmptyQueueException(Exception):
    def __init__(self, err="empty queue"):
        super(EmptyQueueException, self).__init__(err)


class InvalidPositionException(Exception):
    def __init__(self, err="invalid position"):
        super(InvalidPositionException, self).__init__(err)
