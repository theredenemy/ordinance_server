import os
def is_file_in_use(filename):
    import os
    if not os.path.isfile(filename):
        return False
    try:
        os.rename(filename, filename)
        return False
    except PermissionError:
        return True