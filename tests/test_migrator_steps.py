"""Fine-grained unit tests for individual migration step functions."""

from __future__ import annotations

from envforge.migrator import _migrate_v0_to_v1, _migrate_v1_to_v2


def test_v0_to_v1_string_packages_become_dicts():
    data = {"pip_packages": ["numpy==1.24.0", "pandas==2.0.0"]}
    result = _migrate_v0_to_v1(data)
    assert result["pip_packages"] == [
        {"name": "numpy", "version": "1.24.0"},
        {"name": "pandas", "version": "2.0.0"},
    ]


def test_v0_to_v1_package_without_version():
    data = {"pip_packages": ["somepkg"]}
    result = _migrate_v0_to_v1(data)
    assert result["pip_packages"] == [{"name": "somepkg", "version": ""}]


def test_v0_to_v1_already_dict_packages_unchanged():
    original = [{"name": "flask", "version": "2.2.0"}]
    data = {"pip_packages": list(original)}
    result = _migrate_v0_to_v1(data)
    assert result["pip_packages"] == original


def test_v0_to_v1_empty_packages():
    data = {"pip_packages": []}
    result = _migrate_v0_to_v1(data)
    assert result["pip_packages"] == []


def test_v0_to_v1_preserves_other_keys():
    data = {"pip_packages": [], "label": "keep-me", "env_vars": {"X": "1"}}
    result = _migrate_v0_to_v1(data)
    assert result["label"] == "keep-me"
    assert result["env_vars"] == {"X": "1"}


def test_v1_to_v2_renames_node_key():
    data = {"node": "18.12.0"}
    result = _migrate_v1_to_v2(data)
    assert "node" not in result
    assert result["node_version"] == "18.12.0"


def test_v1_to_v2_no_node_key_unchanged():
    data = {"node_version": "16.0.0", "label": "x"}
    result = _migrate_v1_to_v2(data)
    assert result["node_version"] == "16.0.0"
    assert "node" not in result


def test_v1_to_v2_none_node_value():
    data = {"node": None}
    result = _migrate_v1_to_v2(data)
    assert result["node_version"] is None
    assert "node" not in result


def test_v1_to_v2_does_not_overwrite_existing_node_version():
    # If both keys somehow exist, node_version must not be clobbered
    data = {"node": "14.0.0", "node_version": "18.0.0"}
    result = _migrate_v1_to_v2(data)
    assert result["node_version"] == "18.0.0"
