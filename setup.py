from setuptools import setup, find_packages

setup(
    name='mercurygui',
    version='1.0.0',
    description="",
    author='Florian Forster, Sam Schott',
    author_email='f.forster@physik.uni-muenchen.de',
    url='https://github.com/crazyfermions/python-mercury_driver',
    license='MIT',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    packages=find_packages(),
    package_data={
        'mercurygui': ['*.ui', '*.mplstyle'],
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
        'mercuryitc',
        'matplotlib',
        'numpy',
        'pyvisa',
        'qtpy',
        'repr',
        'setuptools',
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
