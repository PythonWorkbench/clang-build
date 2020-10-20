"""Module containing platform specific definitions.

.. data:: PLATFORM

    The platform name as it can appear in clang-build
    TOML files.

.. data:: EXECUTABLE_PREFIX

    Prefix added to executable file names.

.. data:: EXECUTABLE_SUFFIX

    Suffix added to executable name, including extension.

.. data:: EXECUTABLE_OUTPUT

    Folder to place compiled executable in.

.. data:: SHARED_LIBRARY_PREFIX

    Prefix added to shared library file names.

.. data:: SHARED_LIBRARY_SUFFIX

    Suffix added to shared library name, including extension.

.. data:: SHARED_LIBRARY_OUTPUT

    Folder to place compiled shared library in.

.. data:: STATIC_LIBRARY_PREFIX

    Prefix added to static library file names.

.. data:: STATIC_LIBRARY_SUFFIX

    Suffix added to static library name, including extension.

.. data:: STATIC_LIBRARY_OUTPUT

    Folder to place compiled static library in.

.. data:: PLATFORM_EXTRA_FLAGS_EXECUTABLE

    Platform specific flags that are added to the compilation of
    executables.

.. data:: PLATFORM_EXTRA_FLAGS_SHARED

    Platform specific flags that are added to the compilation of
    shared libraries.

.. data:: PLATFORM_EXTRA_FLAGS_STATIC

    Platform specific flags that are added to the compilation of
    static libraries.

.. data:: PLATFORM_PYTHON_INCLUDE_PATH

    Include directory that can be added in order to use the Python
    headers.

.. data:: PLATFORM_PYTHON_LIBRARY_PATH

    Library directory that can be added in order to link to the
    Python library.

.. data:: PLATFORM_PYTHON_LIBRARY_NAME

    Python library name that can be used to link Python.

.. data:: PLATFORM_PYTHON_EXTENSION_SUFFIX

    The platform- and Python-specific suffix for binary extension
    modules.
"""

from sys import platform as _platform
from sys import version_info as _version_info
from pathlib import Path as _Path
from sysconfig import get_paths as _get_paths
from sysconfig import get_config_var as _get_config_var


if _platform == 'linux':
    # Linux
    PLATFORM = 'linux'
    EXECUTABLE_OUTPUT_DIR            = 'bin'
    SHARED_LIBRARY_OUTPUT_DIR        = 'lib'
    STATIC_LIBRARY_OUTPUT_DIR        = 'lib'
    PLATFORM_PYTHON_INCLUDE_PATH     = _Path(_get_paths()['include'])
    PLATFORM_PYTHON_LIBRARY_PATH     = _Path(_get_paths()['data']) / "lib"
    PLATFORM_PYTHON_LIBRARY_NAME     = f"python{_version_info.major}.{_version_info.minor}"
    PLATFORM_PYTHON_EXTENSION_SUFFIX = _get_config_var('EXT_SUFFIX')

elif _platform == 'darwin':
    # OSX
    PLATFORM = 'osx'
    EXECUTABLE_OUTPUT_DIR            = 'bin'
    SHARED_LIBRARY_OUTPUT_DIR        = 'lib'
    STATIC_LIBRARY_OUTPUT_DIR        = 'lib'
    PLATFORM_PYTHON_INCLUDE_PATH     = _Path(_get_paths()['include'])
    PLATFORM_PYTHON_LIBRARY_PATH     = _Path(_get_paths()['data']) / "lib"
    PLATFORM_PYTHON_LIBRARY_NAME     = f"python{_version_info.major}.{_version_info.minor}"
    PLATFORM_PYTHON_EXTENSION_SUFFIX = _get_config_var('EXT_SUFFIX')

elif _platform == 'win32':
    # Windows
    PLATFORM = 'windows'
    EXECUTABLE_OUTPUT_DIR            = 'bin'
    SHARED_LIBRARY_OUTPUT_DIR        = 'bin'
    STATIC_LIBRARY_OUTPUT_DIR        = 'lib'
    PLATFORM_PYTHON_INCLUDE_PATH     = _Path(_get_paths()['include'])
    PLATFORM_PYTHON_LIBRARY_PATH     = _Path(_get_paths()['data']) / "libs"
    PLATFORM_PYTHON_LIBRARY_NAME     = f"python{_version_info.major}{_version_info.minor}"
    PLATFORM_PYTHON_EXTENSION_SUFFIX = _get_config_var('EXT_SUFFIX')

else:
    raise RuntimeError('Platform ' + _platform + 'is currently not supported.')