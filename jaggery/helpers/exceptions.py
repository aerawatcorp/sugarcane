class CaneException(Exception):
    """
    Base exception for every cane exception.
    """

    # message: display message for each exception
    # error_key: error key of each exception: defaults to cane_error

    def __init__(self, message, error_key="cane_error"):
        super(CaneException, self).__init__(message, error_key)
        self.message = message
        self.error_key = error_key
