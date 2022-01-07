# WARNING: This file is overwriten when publishing to PyPI
# __version__ refers to the tag version instead

# VERSION INFORMATION
version_info = {
    'MAJOR_REVISION': 0,
    'MINOR_REVISION': 5,
    'RELEASE_STATUS': 99,  # Dev = 99
}

__version__ = '.'.join([str(v) for v in version_info.values()])
