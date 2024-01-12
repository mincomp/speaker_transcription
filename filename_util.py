
def append_suffix_to_filename(file, suffix):
    parts = file.split(".")
    parts[-2] += "_" + suffix
    return ".".join(parts)


def update_extension(file, extension):
    parts = file.split(".")
    parts[-1] = extension
    return ".".join(parts)