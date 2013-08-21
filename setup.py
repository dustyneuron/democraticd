from setuptools import setup

setup(name='democraticd',
        version='0.1',
        description='A Democratic Daemon',
        long_description="""\
A democratic daemon is the core system service that runs an
enforced democratic server.

This daemon checks for GitHub pull requests and saves them to a database.
When pull requests are approved, it rebuilds and installs the changed
Debian packages.
""",
        author='Tom Scholl',
        author_email='tom@dustyneuron.com',
        url='https://github.com/democraticd/democraticd',
        packages=['democraticd'],
        package_data = {
            '': ['README.md'],
            },
        entry_points = {
            'console_scripts': [
                'democraticd = democraticd.daemon:start',
                'demod-client = democraticd.client:start',
                ],
            },
        classifiers=[
            'Development Status :: 2 - Pre-Alpha',
            'Environment :: Console',
            'Environment :: Web Environment',
            'Intended Audience :: Developers',
            'Intended Audience :: Information Technology',
            'Intended Audience :: System Administrators',
            'License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)',
            'Operating System :: POSIX :: Linux',
            'Programming Language :: Python :: 3',
            'Topic :: Software Development',
            'Topic :: System :: Systems Administration',
            ],
      )
      
