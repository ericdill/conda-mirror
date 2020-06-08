import bz2
import copy
import json
import os
import sys

from os.path import join

from conda_mirror import conda_mirror

import pytest


anaconda_channel = 'https://repo.continuum.io/pkgs/free'


@pytest.fixture(scope='module')
def repodata():
    repodata = {}
    repodata['conda-forge'] = conda_mirror.get_repodata('conda-forge',
                                                        'linux-64')
    repodata[anaconda_channel] = conda_mirror.get_repodata(anaconda_channel,
                                                           'linux-64')
    return repodata


def test_match(repodata):
    repodata_info, repodata_packages = repodata[anaconda_channel]
    matched = conda_mirror._match(repodata_packages, {'name': 'jupyter'})
    assert set([v['name'] for v in matched.values()]) == set(['jupyter'])

    matched = conda_mirror._match(repodata_packages, {'name': "*"})
    assert len(matched) == len(repodata_packages)


def test_version():
    old_args = copy.copy(sys.argv)
    sys.argv = ['conda-mirror', '--version']
    with pytest.raises(SystemExit):
        conda_mirror.cli()
    sys.argv = old_args


def _get_smallest_packages(packages, num=1):
    return sorted(packages, key=lambda x: packages[x]['size'])[:num]


@pytest.mark.parametrize(
    'channel,platform,num_threads',
    ((anaconda_channel, 'linux-64', 0),
     ('conda-forge',    'linux-64', 1)))
def test_cli(tmpdir, channel, platform, repodata, num_threads):
    info, packages = repodata[channel]
    smallest_package, = _get_smallest_packages(packages)

    # drop the html stuff. get just the channel
    f2 = tmpdir.mkdir(channel.rsplit('/', 1)[-1])
    f2.mkdir(platform)
    f1 = tmpdir.mkdir('conf').join('conf.yaml')

    f1.write('''
blacklist:
    - name: "*"
whitelist:
    - name: {}
      version: {}'''.format(packages[smallest_package]['name'],
                            packages[smallest_package]['version']))
    cli_args = ("conda-mirror"
                " --config {config}"
                " --upstream-channel {channel}"
                " --target-directory {target_directory}"
                " --platform {platform}"
                " --num-threads {num_threads}"
                " --pdb"
                " -vvv"
                ).format(config=f1.strpath,
                         channel=channel,
                         target_directory=f2.strpath,
                         platform=platform,
                         num_threads=num_threads)
    if 'anaconda.com' in channel or 'continuum.io' in channel:
        cli_args += " --not-a-commercial-entity"
    old_argv = copy.deepcopy(sys.argv)
    sys.argv = cli_args.split(' ')
    # Write a package that does not exist in the upstream repodata into the
    # mirror path to make sure we exercise a broken code path
    # https://github.com/maxpoint/conda-mirror/issues/29
    _write_bad_package(channel_dir=f2.strpath, platform_name=platform,
                       pkg_name='bad-1-0.tar.bz2')

    # Write a bad package that does exist in the upstream repodata into the
    # mirror path to make sure we can handle that case too
    info, packages = repodata[channel]
    upstream_pkg_name = next(iter(packages.keys()))

    _write_bad_package(channel_dir=f2.strpath, platform_name=platform,
                       pkg_name=upstream_pkg_name)
    conda_mirror.cli()
    sys.argv = old_argv

    for f in ['repodata.json', 'repodata.json.bz2']:
        # make sure the repodata file exists
        assert f in os.listdir(os.path.join(f2.strpath, platform))

    # make sure that the repodata contains less than upstream since we prune it
    with open(os.path.join(f2.strpath, platform, 'repodata.json'), 'r') as f:
        disk_repodata = json.load(f)
    disk_info = disk_repodata.get('info', {})
    assert len(disk_info) == len(info)
    disk_packages = disk_repodata.get('packages', {})
    assert len(disk_packages) < len(packages)
    with bz2.BZ2File(os.path.join(f2.strpath,
                                  platform,
                                  'repodata.json.bz2'), 'r') as f:
        contents = f.read().decode()
        rd = json.loads(contents)
        assert len(rd['info']) == len(disk_info)
        assert len(rd['packages']) == len(disk_packages)


def _write_bad_package(channel_dir, platform_name, pkg_name):
    target_dir = os.path.join(channel_dir, platform_name)
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
    with bz2.BZ2File(os.path.join(target_dir, pkg_name), 'wb') as f:
        f.write("This is a fake package".encode())


def test_main(tmpdir, repodata):
    platform = 'linux-64'
    channel = 'conda-forge'
    target_directory = tmpdir.mkdir(platform)
    temp_directory = tmpdir.mkdir(join(platform, 'temp'))
    info, packages = repodata[channel]
    smallest_package, next_smallest_package = _get_smallest_packages(packages, num=2)

    ret = conda_mirror.main(
        upstream_channel=channel,
        target_directory=target_directory.strpath,
        temp_directory=temp_directory.strpath,
        platform=platform,
        blacklist=[{'name': '*'}],
        whitelist=[{'name': packages[smallest_package]['name'],
                    'version': packages[smallest_package]['version']}])

    assert len(ret['validating-existing']) == 0, "There should be no already-downloaded packages"
    validated_all_downloads = len(ret['downloaded']) == len(ret['validating-new'])
    assert validated_all_downloads, "We should have downloaded at least one package"
    previously_downloaded_packages = len(ret['downloaded'])

    ret = conda_mirror.main(
        upstream_channel=channel,
        target_directory=target_directory.strpath,
        temp_directory=temp_directory.strpath,
        platform=platform,
        blacklist=[{'name': '*'}],
        whitelist=[{'name': packages[next_smallest_package]['name'],
                    'version': packages[next_smallest_package]['version']}])

    msg = "We should have %s packages downloaded now" % previously_downloaded_packages
    assert len(ret['validating-existing']) == previously_downloaded_packages, msg
    validated_all_downloads = len(ret['downloaded']) == len(ret['validating-new'])
    assert validated_all_downloads, "We should have downloaded at least one package"


def test_dry_run_dumb(tmpdir):
    platform = 'linux-64'
    channel = 'conda-forge'
    target_directory = tmpdir.mkdir(platform)
    temp_directory = tmpdir.mkdir(join(platform, 'temp'))
    ret = conda_mirror.main(
        upstream_channel=channel,
        platform=platform,
        target_directory=target_directory.strpath,
        temp_directory=temp_directory.strpath,
        dry_run=True
    )
    assert len(ret['to-mirror']) > 1, "We should have a great deal of packages slated to download"


@pytest.mark.parametrize(
    'channel', ('https://repo.anaconda.com/pkgs/main',
                'https://repo.continuum.io/pkgs./main',
                'conda-forge',
                'bioconda'))
def test_TOS(tmpdir, channel):
    platform = 'linux-64'
    # drop the html stuff. get just the channel
    f2 = tmpdir.mkdir(channel.rsplit('/', 1)[-1])
    f2.mkdir(platform)

    cli_args = ("conda-mirror"
                " --config example-conf.yaml"
                " --upstream-channel {channel}"
                " --target-directory {target_directory}"
                " --platform {platform}"
                " -vvv"
                ).format(channel=channel,
                         target_directory=f2.strpath,
                         platform=platform)
    old_argv = copy.deepcopy(sys.argv)
    sys.argv = cli_args.split(' ')
    should_raise = 'anaconda.com' in channel or 'continuum.io' in channel
    if should_raise:
        with pytest.raises(RuntimeError):
            conda_mirror._parse_and_format_args()
    else:
        conda_mirror._parse_and_format_args()
    sys.argv = old_argv
