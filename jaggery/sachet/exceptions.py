from helpers.exceptions import CaneException


class WriteToCacheError(CaneException):
    def __init(self, message, error_key="cache_error"):
        super().__init__(message, error_key)


class CacheExpired(CaneException):
    def __init__(self, message, error_key="cache_expired"):
        super().__init__(message, error_key)


class DatabaseCacheExpired(CaneException):
    def __init__(self, message, error_key="cache_expired"):
        super().__init__(message, error_key)


class FileCacheExpired(CaneException):
    def __init__(self, message, error_key="cache_expired"):
        super().__init__(message, error_key)


class RedisCacheExpired(CaneException):
    def __init__(self, message, error_key="cache_expired"):
        super().__init__(message, error_key)


class CacheBuildAlreadyInitiated(CaneException):
    def __init__(self, message, error_key="cache_build_initiated"):
        super().__init__(message, error_key)


class InvalidSubCatalogException(CaneException):
    def __init__(self, message, error_key="invalid_sub_category"):
        super().__init__(message, error_key)
