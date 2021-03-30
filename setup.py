from setuptools import setup, find_packages

with open('requirements.txt') as f:
    required = f.read().splitlines()

__version__ = '0.2.0'


setup(
    name='qcpump',
    version=__version__,
    packages=find_packages(),
    package_data={'qcpump': ['watcher_config.yml', 'files/*.png']},
    url='https://github.com/qatrackplus/qcpump',
    keywords="qatrackplus qatrack QATrack+ medical physics qcpump",
    author='Randle Taylor',
    author_email='randy@multileaf.ca',
    description='A client for extracting data from various sources and uploading to QATrack+',
    install_requires=required,
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
