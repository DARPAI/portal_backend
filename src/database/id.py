from ulid import ULID


def generate_shortid() -> str:
    return str(ULID())
