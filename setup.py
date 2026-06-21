#!/usr/bin/env python3
import setuptools
from bareunpy._version import version

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

CLASSIFIERS = """\
Development Status :: 5 - Production/Stable
Intended Audience :: Science/Research
Intended Audience :: Developers
License :: OSI Approved :: BSD License
Programming Language :: Python :: 3
Programming Language :: Python :: 3.10
Programming Language :: Python :: 3.12
Programming Language :: Python :: 3.13
Programming Language :: Python :: 3 :: Only
Natural Language :: Korean
Development Status :: 5 - Production/Stable
Operating System :: OS Independent
Typing :: Typed
Topic :: Software Development
Topic :: Scientific/Engineering
Topic :: Scientific/Engineering :: Artificial Intelligence
Topic :: Scientific/Engineering :: Information Analysis
Operating System :: Microsoft :: Windows
Operating System :: POSIX
Operating System :: Unix
Operating System :: MacOS
"""

# import grpc_tools
#
# setuptools.setup(
#     cmdclass={
#         'build_proto_modules': grpc_tools.command.BuildPackageProtos,
#     }
# )

setuptools.setup(
    name="bareunpy",
    version=version,
    author="Gihyun YUN",
    author_email="gih2yun@baikal.ai",
    description="The bareun python API library",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://bareun.ai/",
    download_url="https://pypi.python.org/pypi/bareunpy",
    project_urls={
        "Bug Tracker": "https://github.com/bareun-nlp/bareunpy/issues",
        # "Documentation": get_docs_url(),
        "Source Code": "https://github.com/bareun-nlp/bareunpy",
    },
    license='BSD',
    platform='Independent',
    # bareunpy 본체 + 생성물(bareun) 패키지를 함께 배포한다.
    packages=setuptools.find_packages(),
    # 생성물의 타입 스텁(.pyi)과 PEP 561 마커(py.typed)를 휠에 포함한다.
    package_data={
        'bareun': ['*.pyi', 'py.typed'],
        'bareunpy': ['py.typed'],
    },
    include_package_data=True,
    install_requires=[
        'connectrpc>=0.10.1,<0.11',
        'protobuf>=7.35,<8',
    ],
    classifiers=[_f for _f in CLASSIFIERS.split('\n') if _f],
    python_requires='>=3.10',
)
