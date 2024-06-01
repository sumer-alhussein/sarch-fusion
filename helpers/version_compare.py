def version_tuple(version:str):
    return tuple(map(int, (version.split("."))))


def is_newer_version(current:str, latest:str):
    current_version = version_tuple(current)
    latest_version = version_tuple(latest)
    if latest_version > current_version:
        return True
    return False
