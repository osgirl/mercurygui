from setuptools import setup, find_packages

setup(
    name='mercurygui',
    version='0.0.1',
    description="",
    author='Sam Schott',
    author_email='ss2151@cam.ac.uk',
    url='https://github.com/oe-fet/mercurygui.git',
    license='MIT',
    long_description=open('README.md').read(),
    packages=find_packages(),
    package_data={
        'mercurygui': ['*.ui']
    },
    entry_points={
        'console_scripts': [
            'mercurygui=mercurygui.main:run'
        ],
        'gui_scripts': [
            'mercurygui=mercurygui.main:run'
        ]
    },
    install_requires=[
        'setuptools',
        'QtPy',
        'mercuryitc',
        'matplotlib',
        'pyvisa',
        'setuptools',
        'QDarkStyle',
        'repr',
        'spyder'
    ],
    zip_safe=False,
    keywords='mercurygui',
    classifiers=[
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
    test_suite='tests',
    tests_require=[
    ]
)