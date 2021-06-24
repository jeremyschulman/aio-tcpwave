# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['aiotcpwave']

package_data = \
{'': ['*']}

install_requires = \
['bidict>=0.21.2,<0.22.0', 'httpx>=0.17.1,<0.18.0', 'tenacity>=7.0.0,<8.0.0']

setup_kwargs = {
    'name': 'aio-tcpwave',
    'version': '0.0.4',
    'description': 'AsyncIO client for TCPWave',
    'long_description': None,
    'author': 'Jeremy Schulman',
    'author_email': 'jeremy.schulman@mlb.com',
    'maintainer': None,
    'maintainer_email': None,
    'url': None,
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'python_requires': '>=3.8,<4.0',
}


setup(**setup_kwargs)
