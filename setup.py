from setuptools import setup, find_packages

requirements = [
    "Jinja2<2.12.0",
    "PyPAC<0.16.0",
    "appdirs<1.5.4",
    "fdb<2.1.0",
    "firebirdsql<1.2.0",
    "pyodbc<4.1.0",
    "pytest-coverage",
    "pytest-sugar",
    "pytest<6.3.2",
    "python-certifi-win32<1.7",
    "requests[socks]<2.26.0",
    "toposort<1.7.0",
    "wxPython<4.2.0",
]

__version__ = '0.3.16'


setup(
    name='qcpump',
    version=__version__,
    packages=find_packages(),
    package_data={'qcpump': []},
    url='https://github.com/qatrackplus/qcpump',
    keywords="qatrackplus qatrack QATrack+ medical physics qcpump",
    author='Randle Taylor',
    author_email='randy@multileaf.ca',
    description='A client for extracting data from various sources and uploading to QATrack+',
    install_requires=requirements,
    license='MIT',
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Healthcare Industry",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Topic :: Scientific/Engineering :: Medical Science Apps.",
    ]
)
