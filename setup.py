"""
Runhouse breaks down the silos between machine learning compute and data environments, and makes interacting with cloud resources easy and Pythonic:
With Runhouse, you can:
- Run effortlessly on any hardware in experimentation, research, or production, iterating and debugging like you’re running locally on bare metal.
- Scale up, productionize, or share your work without weeks of packaging or translating into platform DSLs.
- Retain control of their underlying infra, customizing it to your unique needs and continuing to use any ML tools you would from cloud instances.
"""
# Adapted from: https://github.com/skypilot-org/skypilot/blob/master/sky/setup_files/setup.py

import io
import os
import platform
import re
import warnings
import datetime

import setuptools

ROOT_DIR = os.path.dirname(__file__)

system = platform.system()
if system == 'Darwin':
    mac_version = platform.mac_ver()[0]
    mac_major, mac_minor = mac_version.split('.')[:2]
    mac_major = int(mac_major)
    mac_minor = int(mac_minor)
    if mac_major < 10 or (mac_major == 10 and mac_minor < 15):
        warnings.warn(
            f'\'Detected MacOS version {mac_version}. MacOS version >=10.15 '
            'is required to install ray>=1.9\'')


def find_version(*filepath):
    # Extract version information from filepath
    with open(os.path.join(ROOT_DIR, *filepath)) as fp:
        version_match = re.search(r'^__version__ = [\'"]([^\'"]*)[\'"]',
                                  fp.read(), re.M)
        if version_match:
            return version_match.group(1)
        raise RuntimeError('Unable to find version string.')


def parse_readme(readme: str) -> str:
    """Parse the README.md file to be pypi compatible."""
    # Replace the footnotes.
    readme = readme.replace('<!-- Footnote -->', '#')
    footnote_re = re.compile(r'\[\^([0-9]+)\]')
    readme = footnote_re.sub(r'<sup>[\1]</sup>', readme)

    # Remove the dark mode switcher
    mode_re = re.compile(
        r'<picture>[\n ]*<source media=.*>[\n ]*<img(.*)>[\n ]*</picture>',
        re.MULTILINE)
    readme = mode_re.sub(r'<img\1>', readme)
    return readme


install_requires = [
    'wheel',
    'rich',
    'fsspec',
    'pyarrow',
    'sshtunnel',
    'typer',
    'skypilot @ git+https://github.com/skypilot-org/skypilot.git@30476aa'
]

# NOTE: Change the templates/spot-controller.yaml.j2 file if any of the following
# packages dependencies are changed.
extras_require = {
    'aws': [
        'awscli',
        'boto3',
        # 'Crypto' module used in authentication.py for AWS.
        'pycryptodome==3.12.0',
    ],
    'azure': ['azure-cli==2.31.0', 'azure-core'],
    'gcp': ['google-api-python-client', 'google-cloud-storage'],
    'docker': ['docker'],
}

extras_require['all'] = sum(extras_require.values(), [])

# Install aws requirements by default, as it is the most common cloud provider,
# and the installation is quick.
install_requires += extras_require['aws']

long_description = ''
readme_filepath = 'README.md'
if os.path.exists(readme_filepath):
    long_description = io.open(readme_filepath, 'r', encoding='utf-8').read()
    long_description = parse_readme(long_description)

# Flip to True to build the nightly instead of release.
nightly = True
version = find_version('runhouse', '__init__.py')

setuptools.setup(
    # NOTE: this affects the package.whl wheel name. When changing this (if
    # ever), you must grep for '.whl' and change all corresponding wheel paths
    # (templates/*.j2 and wheel_utils.py).
    name="runhouse" if not nightly else "runhouse-nightly",
    # append .dev and the date in YYYYMMDD format for nightly builds
    version=version + f'.dev{datetime.datetime.today().strftime("%Y%m%d")}' if nightly else version,
    packages=setuptools.find_packages(),
    author='Runhouse Team',
    license='Apache 2.0',
    readme='README.md',
    description='Runhouse: A multiplayer cloud compute and data environment, like Google Docs for ML',
    long_description=long_description,
    long_description_content_type='text/markdown',
    setup_requires=['wheel'],
    requires_python='>=3.7',
    install_requires=install_requires,
    extras_require=extras_require,
    entry_points={
        'console_scripts': ['runhouse = runhouse.main:app'],
    },
    include_package_data=True,
    classifiers=[
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: System :: Distributed Computing',
    ],
    project_urls={
        'Homepage': 'https://api.run.house',
        'Issues': 'https://github.com/run-house/runhouse/issues/',
        'Documentation': 'https://runhouse-docs.readthedocs-hosted.com/en/latest/',
    },
)