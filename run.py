import os
from os.path import abspath, dirname, join

from makerbase import app


if 'MAKERBASE_SETTINGS' not in os.environ:
    os.environ['MAKERBASE_SETTINGS'] = join(dirname(abspath(__file__)), 'settings.py')

app.config.from_envvar('MAKERBASE_SETTINGS')

if __name__ == '__main__':
    app.run(debug=True)
