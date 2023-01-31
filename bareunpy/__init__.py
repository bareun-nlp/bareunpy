"""
bareunpy
=====
Provides
  1. a Korean Part-Of-Speech Tagger as bareun client
  2. Multiple custom dictionaries which is kept in the your bareun server.


How to use the documentation
----------------------------
Full documentation for bareun is available in
installable tarball or docker images.
- see `docs/intro.html` at installable tarball.
- or `http://localhost:5757/intro.html` after running docker.

The docstring examples assume that `bareunpy` has been imported as `brn`::
  >>> import bareunpy as brn

Use the built-in ``help`` function to view a class's docstring::
  >>> help(brn.Tagger)
  ...

Classes
-------
Tagger
    the bareun POS tagger for Korean
    `from bareunpy import Tagger`
Tagged
    Wrapper for tagged output
    `from bareunpy import Tagged`
CustomDict
    Custom dictionary for Korean.
    `from bareunpy import CustomDict`

Version
-------
```
import bareunpy as brn
print(brn.version)
print(brn.bareun_version)
```

Get bareun
----------------------------
- Use docker, https://hub.docker.com/r/bareunai/bareun
- Or visit https://bareun.ai/
"""

import sys
import os

from bareunpy._tagger import Tagger, Tagged
from bareunpy._tokenizer import Tokenizer, Tokenized
from bareunpy._custom_dict import CustomDict
from bareunpy._custom_dict_client import CustomDictionaryServiceClient
from bareunpy._lang_service_client import BareunLanguageServiceClient

version = "1.4.1"
bareun_version = "1.7.26"
