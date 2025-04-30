def no_error(output) -> bool:
    return not bool(output.get("error"))


def has_results(output) -> bool:
    return bool(output.get("results"))