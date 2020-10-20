import random

__all__ = ["generate_random_number"]


def generate_random_number(length: int = 6) -> int:
    """
    Generate random number with the provided length (number of digits) ensuring that two neighboring
    digits are always different and with each digit having a value between 1 - 9.
    """
    result = ""

    while len(result) < length:
        random_value = random.randint(1, 9)

        if len(result) == 0:
            # First digit
            result += str(random_value)
        else:
            # Make sure it's different than the previous digit
            if random_value == int(result[-1]):
                continue

            result += str(random_value)

    return int(result)
