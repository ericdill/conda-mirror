# conda-mirror

[![Build Status](https://travis-ci.org/regro/conda-mirror.svg?branch=master)](https://travis-ci.org/regro/conda-mirror)
[![PyPI version](https://badge.fury.io/py/conda-mirror.svg)](https://badge.fury.io/py/conda-mirror)
[![codecov](https://codecov.io/gh/regro/conda-mirror/branch/master/graph/badge.svg)](https://codecov.io/gh/regro/conda-mirror)

Mirrors an upstream conda channel to a local directory.

## Install

`conda-mirror` is available on PyPI and conda-forge.

Install with:

`pip install conda-mirror`

or:

`conda install conda-mirror -c conda-forge`

## Compatibility

`conda-mirror` is intentionally a py3 only package

## CLI

CLI interface for `conda-mirror.py`

```
usage: conda-mirror [-h] [--upstream-channel UPSTREAM_CHANNEL]
                    [--target-directory TARGET_DIRECTORY]
                    [--temp-directory TEMP_DIRECTORY] [--platform PLATFORM]
                    [-v] [--config CONFIG] [--pdb] [--num-threads NUM_THREADS]
                    [--version] [--dry-run] [--no-validate-target]
                    [--minimum-free-space MINIMUM_FREE_SPACE] [--proxy PROXY]
                    [--ssl-verify SSL_VERIFY] [-k] [--max-retries MAX_RETRIES]

CLI interface for conda-mirror.py

optional arguments:
  -h, --help            show this help message and exit
  --upstream-channel UPSTREAM_CHANNEL
                        The target channel to mirror. Can be a channel on
                        anaconda.org like "conda-forge" or a full qualified
                        channel like "https://repo.continuum.io/pkgs/free/"
  --target-directory TARGET_DIRECTORY
                        The place where packages should be mirrored to
  --temp-directory TEMP_DIRECTORY
                        Temporary download location for the packages. Defaults
                        to a randomly selected temporary directory. Note that
                        you might need to specify a different location if your
                        default temp directory has less available space than
                        your mirroring target
  --platform PLATFORM   The OS platform(s) to mirror. one of: {'linux-64',
                        'linux-32','osx-64', 'win-32', 'win-64'}
  -v, --verbose         logging defaults to error/exception only. Takes up to
                        three '-v' flags. '-v': warning. '-vv': info. '-vvv':
                        debug.
  --config CONFIG       Path to the yaml config file
  --pdb                 Enable PDB debugging on exception
  --num-threads NUM_THREADS
                        Num of threads for validation. 1: Serial mode. 0: All
                        available.
  --version             Print version and quit
  --dry-run             Show what will be downloaded and what will be removed.
                        Will not validate existing packages
  --no-validate-target  Skip validation of files already present in target-
                        directory
  --minimum-free-space MINIMUM_FREE_SPACE
                        Threshold for free diskspace. Given in megabytes.
  --proxy PROXY         Proxy URL to access internet if needed
  --ssl-verify SSL_VERIFY, --ssl_verify SSL_VERIFY
                        Path to a CA_BUNDLE file with certificates of trusted
                        CAs, this may be "False" to disable verification as
                        per the requests API.
  -k, --insecure        Allow conda to perform "insecure" SSL connections and
                        transfers. Equivalent to setting 'ssl_verify' to
                        'false'.
  --max-retries MAX_RETRIES
                        Maximum number of retries before a download error is
                        reraised, defaults to 100
```

## Example Usage

WARNING: Invoking this command will pull ~10GB and take at least an hour

`conda-mirror --upstream-channel conda-forge --target-directory local_mirror --platform linux-64`

## More Details

### denylist/allowlist configuration

example-conf.yaml:

```yaml
denylist:
    - license: "*agpl*"
    - license: None
    - license: ""

allowlist:
    - name: system
```

`denylist` removes package(s) that match the condition(s) listed from the
upstream repodata.

`allowlist` re-includes any package(s) from denylist that match the
allowlist conditions.

denylist and allowlist both take lists of dictionaries. The keys in the
dictionary need to be values in the `repodata.json` metadata. The values are
(unix) globs to match on. Go here for the full repodata of the upstream
"defaults" channel:
http://conda.anaconda.org/anaconda/linux-64/repodata.json

Here are the contents of one of the entries in repodata['packages']

```python
{'botocore-1.4.10-py34_0.tar.bz2': {'arch': 'x86_64',
  'binstar': {'channel': 'main',
   'owner_id': '55fc8527d3234d09d4951c71',
   'package_id': '56b88ea1be1cc95a362b218e'},
  'build': 'py34_0',
  'build_number': 0,
  'date': '2016-04-11',
  'depends': ['docutils >=0.10',
   'jmespath >=0.7.1,<1.0.0',
   'python 3.4*',
   'python-dateutil >=2.1,<3.0.0'],
  'license': 'Apache',
  'md5': 'b35a5c1240ba672e0d9d1296141e383c',
  'name': 'botocore',
  'platform': 'linux',
  'requires': [],
  'size': 1831799,
  'version': '1.4.10'}}
```

See implementation details in the `conda_mirror:match` function for more
information.

#### Common usage patterns
##### Mirror **only** one specific package
If you wanted to match exactly the botocore package listed above with your
config, then you could use the following configuration to first denylist
**all** packages and then include just the botocore packages:

```yaml
denylist:
    - name: "*"
allowlist:
    - name: botocore
      version: 1.4.10
      build: py34_0
```
##### Mirror everything but agpl licenses
```yaml
denylist:
    - license: "*agpl*"
```

##### Mirror only python 3 packages
```yaml
denylist:
    - name: "*"
allowlist:
    - build: "*py3*"
```

## Testing

### Install test requirements

Note: Will install packages from pip

```
$ pip install -r test-requirements.txt
Requirement already satisfied: pytest in /home/edill/miniconda/lib/python3.5/site-packages (from -r test-requirements.txt (line 1))
Requirement already satisfied: coverage in /home/edill/miniconda/lib/python3.5/site-packages (from -r test-requirements.txt (line 2))
Requirement already satisfied: pytest-ordering in /home/edill/miniconda/lib/python3.5/site-packages (from -r test-requirements.txt (line 3))
Requirement already satisfied: py>=1.4.29 in /home/edill/miniconda/lib/python3.5/site-packages (from pytest->-r test-requirements.txt (line 1))
```

### Run the tests, invoking with the `coverage` tool.

```
$ coverage run run_tests.py
sys.argv=['run_tests.py']
========================================= test session starts ==========================================
platform linux -- Python 3.5.3, pytest-3.0.6, py-1.4.31, pluggy-0.4.0 -- /home/edill/miniconda/bin/python
cachedir: .cache
rootdir: /home/edill/dev/maxpoint/github/conda-mirror, inifile:
plugins: xonsh-0.5.2, ordering-0.4
collected 4 items

test/test_conda_mirror.py::test_match PASSED
test/test_conda_mirror.py::test_cli[https://repo.continuum.io/pkgs/free-linux-64] PASSED
test/test_conda_mirror.py::test_cli[conda-forge-linux-64] PASSED
test/test_conda_mirror.py::test_handling_bad_package PASSED

======================================= 4 passed in 4.41 seconds =======================================
```

### Show the coverage statistics

```
$ coverage report -m
Name                           Stmts   Miss  Cover   Missing
------------------------------------------------------------
conda_mirror/__init__.py           3      0   100%
conda_mirror/conda_mirror.py     236     20    92%   203-205, 209-210, 214, 240, 249-254, 262-264, 303, 366, 497, 542-543, 629
------------------------------------------------------------
TOTAL                            239     20    92%
```

## Other

After a new contributor makes a pull-request that is approved, we will reach out
and invite you to be a maintainer of the project.


## Releasing

To release you need three things

1. Commit rights to conda-mirror
2. A github token
3. The version number that you want to use for the new tag

After you have all three of these things, run the release.sh script (on a unix machine) and
pass it the tag that you want to use and your github token:

```bash
GITHUB_TOKEN=<github_token> ./release.sh <tag>
```
