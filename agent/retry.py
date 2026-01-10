MAX_RETRIES = 3

RETRIABLE_TESTS = ["ConnectionError", "NetworkError", "TimeoutError", "NoSuchElementException", "ResourceUnavailable"]
NON_RETRIABLE_TESTS = ["AssertionError", "ModuleNotFoundError", ]


def retry_policy(retries: int, error_types: list) -> bool:
    if retries >= MAX_RETRIES:
        return False

    if any(err in NON_RETRIABLE_TESTS for err in error_types):
        return False

    if all(err in RETRIABLE_TESTS for err in error_types):
        return True

    return False

