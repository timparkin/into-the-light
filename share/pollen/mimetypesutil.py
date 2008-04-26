import os.path
import mimetypes

EVEN_MORE = [
    ('image/pjpeg', ['pjpeg']),
    ('text/x-component', ['htc']),
    ]

POSSIBLE_PATHS = [
    '/etc/mime.types',
    ]

def update_types_map(path=None):
    """Update the standard Python mimetypes map with those from a file.

    If the path to the file is not provided then the module will search for
    something suitable. That currently means looking for the file provided
    by the mime-support package on Linux.

    If a file path is not provided and nothing suitable can be found then
    nothing happens and no error is raised.
    """
    if path is None:
        path = best_path()
    stuffToTry = [EVEN_MORE]
    if path is not None:
        stuffToTry.append(parse_file(path))
    for stuff in stuffToTry:
        for mimetype, exts in stuff:
            for ext in exts:
                ext = '.'+ext
                mimetypes.add_type(mimetype, ext)

def best_path():
    for path in POSSIBLE_PATHS:
        if os.path.isfile(path):
            return path

def parse_file(path):
    for line in open(path):
        line = line.strip()
        if not line or line[0] == '#':
            continue
        parts = line.split()
        mimetype, exts = parts[0], parts[1:]
        yield mimetype, exts

__all__ = ['update_types_map']

if __name__ == '__main__':
    update_types_map()
    assert mimetypes.guess_type('.jpe')
    assert mimetypes.guess_type('.jpg')
    assert mimetypes.guess_type('.jpeg')
    assert mimetypes.guess_extension('image/pjpeg')

