import os
import shutil

from pathlib import Path

import pytest

import runhouse as rh
import yaml
from runhouse.rns.folders.folder import Folder
from runhouse.rns.packages import Package

from .test_package import _create_s3_package

pip_reqs = ["torch", "numpy"]

# -------- BASE ENV TESTS ----------- #


@pytest.mark.localtest
def test_create_env_from_name_local():
    env_name = "~/local_env"
    local_env = rh.env(name=env_name, reqs=pip_reqs).save()
    del local_env

    remote_env = rh.env(name=env_name)
    assert remote_env.reqs == pip_reqs


@pytest.mark.rnstest
def test_create_env_from_name_rns():
    env_name = "rns_env"
    env = rh.env(name=env_name, reqs=pip_reqs).save()
    del env

    remote_env = rh.env(name=env_name)
    assert remote_env.reqs == pip_reqs


@pytest.mark.localtest
def test_create_env():
    test_env = rh.env(name="test_env", reqs=pip_reqs)
    assert len(test_env.reqs) == 2
    assert test_env.reqs == pip_reqs


@pytest.mark.clustertest
def test_to_cluster(cpu_cluster):
    test_env = rh.env(name="test_env", reqs=["numpy"])

    test_env.to(cpu_cluster)
    res = cpu_cluster.run_python(["import numpy"])
    assert res[0][0] == 0  # import was successful

    cpu_cluster.run(["pip uninstall numpy"])


@pytest.mark.awstest
@pytest.mark.clustertest
def test_to_fs_to_cluster(cpu_cluster):
    s3_pkg, folder_name = _create_s3_package()

    test_env_s3 = rh.env(name="test_env_s3", reqs=["s3fs", "scipy", s3_pkg]).to("s3")
    count = 0
    for req in test_env_s3.reqs:
        if isinstance(req, Package) and isinstance(req.install_target, Folder):
            assert req.install_target.system == "s3"
            assert req.install_target.exists_in_system()
            count += 1
    assert count == 1

    test_env_cluster = test_env_s3.to(system=cpu_cluster, path=folder_name, mount=True)
    for req in test_env_cluster.reqs:
        if isinstance(req, Package) and isinstance(req.install_target, Folder):
            assert req.install_target.system == cpu_cluster

    assert "sample_file_0.txt" in cpu_cluster.run([f"ls {folder_name}"])[0][1]
    cpu_cluster.run([f"rm -r {folder_name}"])


@pytest.mark.clustertest
def test_function_to_env(cpu_cluster):
    test_env = rh.env(name="test-env", reqs=["parameterized"]).save()

    def summer(a, b):
        return a + b

    rh.function(summer).to(cpu_cluster, test_env)
    res = cpu_cluster.run_python(["import parameterized"])
    assert res[0][0] == 0

    cpu_cluster.run(["pip uninstall parameterized -y"])
    res = cpu_cluster.run_python(["import parameterized"])
    assert res[0][0] == 1

    rh.function(summer, system=cpu_cluster, env="test-env")
    res = cpu_cluster.run_python(["import parameterized"])
    assert res[0][0] == 0

    cpu_cluster.run(["pip uninstall parameterized -y"])


def test_env_git_reqs(cpu_cluster):
    git_package = rh.GitPackage(
        git_url="https://github.com/huggingface/diffusers.git",
        install_method="pip",
        revision="v0.11.1",
    )
    env = rh.env(reqs=[git_package])
    env.to(cpu_cluster)
    res = cpu_cluster.run(["pip freeze | grep diffusers"])
    assert "diffusers" in res[0][1]
    cpu_cluster.run(["pip uninstall diffusers -y"])


# -------- CONDA ENV TESTS ----------- #


def _get_conda_env(name="rh-test", python_version="3.10.9", pip_reqs=[]):
    conda_env = {
        "name": name,
        "channels": ["defaults"],
        "dependencies": [
            f"python={python_version}",
        ],
    }
    return conda_env


def _get_conda_python_version(env, system):
    system.up_if_not()
    env.to(system)
    py_version = system.run([f"{env._run_cmd} python --version"])
    return py_version[0][1]


@pytest.mark.localtest
def test_conda_env_from_name_local():
    env_name = "~/local_conda_env"
    conda_env = _get_conda_env()
    local_env = rh.env(name=env_name, conda_env=conda_env).save()
    del local_env

    remote_env = rh.env(name=env_name)
    assert remote_env.conda_yaml == conda_env
    assert remote_env.env_name == conda_env["name"]


@pytest.mark.rnstest
def test_conda_env_from_name_rns():
    env_name = "rns_conda_env"
    conda_env = _get_conda_env()
    env = rh.env(name=env_name, conda_env=conda_env).save()
    del env

    remote_env = rh.env(name=env_name)
    assert remote_env.conda_yaml == conda_env
    assert remote_env.env_name == conda_env["name"]


@pytest.mark.clustertest
def test_conda_env_path_to_system(cpu_cluster):
    env_name = "from_path"
    python_version = "3.9.16"
    tmp_path = Path.cwd() / "test-env"
    file_path = f"{tmp_path}/{env_name}.yml"
    tmp_path.mkdir(exist_ok=True)
    yaml.dump(
        _get_conda_env(name=env_name, python_version=python_version),
        open(file_path, "w"),
    )
    conda_env = rh.env(conda_env=file_path)
    shutil.rmtree(tmp_path)

    assert python_version in _get_conda_python_version(conda_env, cpu_cluster)


@pytest.mark.clustertest
def test_conda_env_local_to_system(cpu_cluster):
    env_name = "local-env"
    python_version = "3.9.16"
    os.system(f"conda create -n {env_name} -y python=={python_version}")

    conda_env = rh.env(conda_env=env_name)
    assert python_version in _get_conda_python_version(conda_env, cpu_cluster)


@pytest.mark.clustertest
def test_conda_env_dict_to_system(cpu_cluster):
    conda_env = _get_conda_env(python_version="3.9.16")
    test_env = rh.env(name="test_env", conda_env=conda_env)

    assert "3.9.16" in _get_conda_python_version(test_env, cpu_cluster)

    # ray installed successfully
    res = cpu_cluster.run([f"{test_env._run_cmd} python -c 'import ray'"])
    assert res[0][0] == 0


@pytest.mark.clustertest
def test_function_to_conda_env(cpu_cluster):
    conda_env = _get_conda_env(python_version="3.9.16")
    test_env = rh.env(name="test_env", conda_env=conda_env)

    def summer(a, b):
        return a + b

    rh.function(summer).to(cpu_cluster, test_env)
    assert "3.9.16" in _get_conda_python_version(test_env, cpu_cluster)


@pytest.mark.clustertest
def test_conda_additional_reqs(cpu_cluster):
    new_conda_env = _get_conda_env(name="test-add-reqs")
    new_conda_env = rh.env(name="conda_env", reqs=["scipy"], conda_env=new_conda_env)
    new_conda_env.to(cpu_cluster)
    res = cpu_cluster.run([f"{new_conda_env._run_cmd} python -c 'import scipy'"])
    assert res[0][0] == 0  # reqs successfully installed
    cpu_cluster.run([f"{new_conda_env._run_cmd} pip uninstall scipy"])


@pytest.mark.clustertest
def test_conda_git_reqs(cpu_cluster):
    conda_env = _get_conda_env(name="test-add-reqs")
    git_package = rh.GitPackage(
        git_url="https://github.com/huggingface/diffusers.git",
        install_method="pip",
        revision="v0.11.1",
    )
    conda_env = rh.env(conda_env=conda_env, reqs=[git_package])
    conda_env.to(cpu_cluster)
    res = cpu_cluster.run([f"{conda_env._run_cmd} pip freeze | grep diffusers"])
    assert "diffusers" in res[0][1]
    cpu_cluster.run([f"{conda_env._run_cmd} pip uninstall diffusers"])


@pytest.mark.clustertest
def test_conda_env_to_fs_to_cluster(cpu_cluster):
    s3_pkg, folder_name = _create_s3_package()

    conda_env = _get_conda_env(name="s3-env")
    conda_env_s3 = rh.env(reqs=["s3fs", "scipy", s3_pkg], conda_env=conda_env).to("s3")
    count = 0
    for req in conda_env_s3.reqs:
        if isinstance(req, Package) and isinstance(req.install_target, Folder):
            assert req.install_target.system == "s3"
            assert req.install_target.exists_in_system()
            count += 1
    assert count == 1

    count = 0
    conda_env_cluster = conda_env_s3.to(
        system=cpu_cluster, path=folder_name, mount=True
    )
    for req in conda_env_cluster.reqs:
        if isinstance(req, Package) and isinstance(req.install_target, Folder):
            assert req.install_target.system == cpu_cluster
            count += 1
    assert count == 1

    assert "sample_file_0.txt" in cpu_cluster.run([f"ls {folder_name}"])[0][1]
    assert "s3-env" in cpu_cluster.run(["conda info --envs"])[0][1]

    cpu_cluster.run([f"rm -r {folder_name}"])
    cpu_cluster.run(["conda env remove -n s3-env"])


# -------- CONDA ENV + FUNCTION TESTS ----------- #


def np_summer(a, b):
    import numpy as np

    return int(np.sum([a, b]))


@pytest.mark.clustertest
def test_conda_call_fn(cpu_cluster):
    conda_dict = _get_conda_env(name="c", pip_reqs=["numpy"])
    conda_env = rh.env(conda_env=conda_dict, reqs=["pytest"])
    fn = rh.function(np_summer).to(system=cpu_cluster, env=conda_env)
    result = fn(1, 4)
    assert result == 5


@pytest.mark.clustertest
def test_conda_map_fn(cpu_cluster):
    conda_dict = _get_conda_env(name="test-map-fn", pip_reqs=["numpy"])
    conda_env = rh.env(conda_env=conda_dict, reqs=["pytest"])
    map_fn = rh.function(np_summer, system=cpu_cluster, env=conda_env)
    inputs = list(zip(range(5), range(4, 9)))
    results = map_fn.starmap(inputs)
    assert results == [4, 6, 8, 10, 12]
