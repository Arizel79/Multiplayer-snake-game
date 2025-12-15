import random


def get_random_id():
    return hex(random.randint(0, 131_072))
