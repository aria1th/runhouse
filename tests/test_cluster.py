import unittest
from pathlib import Path
import pytest

from runhouse.rns.hardware.skycluster import Cluster, cluster


def test_cluster_config():
    rh_cpu = cluster(name='^rh-cpu', dryrun=False)
    if not rh_cpu.is_up():
        rh_cpu.up()
    config = rh_cpu.config_for_rns
    cluster2 = Cluster.from_config(config)
    assert cluster2.address == rh_cpu.address


def test_cluster_sharing():
    # TODO [DG] finish
    pass


def test_install():
    c = cluster(name='^rh-cpu', save_to=[])
    c.install_packages(['./',
                        'torch==1.12.1',
                        # 'conda:jupyterlab',  # TODO [DG] make this actually work
                        # 'gh:pytorch/vision'  # TODO [DG] make this actually work
                        ])


def test_basic_run():
    # Create temp file where fn's will be stored
    test_cmd = 'echo hi'
    hw = cluster(name='^rh-cpu')
    res = hw.run(commands=[test_cmd])
    assert 'hi' in res[0][1]


if __name__ == '__main__':
    unittest.main()