class ServiceUnavailableException(Exception):
    def __init__(self, message="Service temporarily unavailable") -> None:
        super(BaseException, self).__init__()
        self.message = message
