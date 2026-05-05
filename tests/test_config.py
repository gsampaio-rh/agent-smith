"""Tests for environment config and bind-shell detection."""

from __future__ import annotations

import json
from unittest.mock import patch

import pytest

from smith.config import PodInfo, SmithConfig, check_bind_shell, discover_agent_pods, resolve_agent_ip


class TestSmithConfigDefaults:
    def test_defaults_match_lib_sh(self, clean_env) -> None:
        cfg = SmithConfig.from_env()
        assert cfg.agent_ns == "agent-namespace"
        assert cfg.bind_port == 4444
        assert cfg.neo_ui_svc == "neo-ui.agent-namespace.svc:3458"
        assert cfg.attacker_ns == "attacker"

    def test_env_overrides(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("AGENT_NS", "custom-ns")
        monkeypatch.setenv("BIND_PORT", "5555")
        monkeypatch.setenv("NEO_UI_SVC", "my-svc:1234")
        monkeypatch.setenv("ATTACKER_NS", "evil")

        cfg = SmithConfig.from_env()
        assert cfg.agent_ns == "custom-ns"
        assert cfg.bind_port == 5555
        assert cfg.neo_ui_svc == "my-svc:1234"
        assert cfg.attacker_ns == "evil"

    def test_neo_ui_svc_derived_from_agent_ns(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("AGENT_NS", "foo-ns")
        monkeypatch.delenv("NEO_UI_SVC", raising=False)

        cfg = SmithConfig.from_env()
        assert cfg.neo_ui_svc == "neo-ui.foo-ns.svc:3458"


class TestResolveAgentIP:
    def test_returns_none_when_no_sa_token(self, default_config) -> None:
        with patch("smith.config.os.path.isfile", return_value=False):
            assert resolve_agent_ip(default_config) is None

    def test_returns_none_on_network_error(self, default_config) -> None:
        with (
            patch("smith.config.os.path.isfile", return_value=True),
            patch("builtins.open", side_effect=OSError("no file")),
        ):
            assert resolve_agent_ip(default_config) is None


class TestCheckBindShell:
    def test_returns_false_on_connection_refused(self) -> None:
        assert check_bind_shell("127.0.0.1", 1, timeout=0.1) is False

    def test_returns_false_on_unreachable_host(self) -> None:
        assert check_bind_shell("192.0.2.1", 4444, timeout=0.1) is False


class TestDiscoverAgentPods:
    def test_returns_empty_when_no_sa_token(self, default_config) -> None:
        with patch("smith.config.os.path.isfile", return_value=False):
            pods = discover_agent_pods(default_config)
            assert pods == []

    def test_returns_pods_from_api(self, default_config) -> None:
        fake_items = [
            {
                "metadata": {"name": "neo-abc", "namespace": "agent-namespace"},
                "status": {"podIP": "10.0.0.1", "phase": "Running"},
            },
            {
                "metadata": {"name": "neo-xyz", "namespace": "agent-namespace"},
                "status": {"podIP": "10.0.0.2", "phase": "Running"},
            },
        ]

        with (
            patch("smith.config._query_k8s_pods", return_value=fake_items),
            patch("smith.config.check_bind_shell", return_value=False),
        ):
            pods = discover_agent_pods(default_config)
            assert len(pods) == 2
            assert pods[0].name == "neo-abc"
            assert pods[0].ip == "10.0.0.1"
            assert pods[1].name == "neo-xyz"
            assert isinstance(pods[0], PodInfo)

    def test_skips_pods_without_ip(self, default_config) -> None:
        fake_items = [
            {
                "metadata": {"name": "neo-pending", "namespace": "agent-namespace"},
                "status": {"podIP": "", "phase": "Pending"},
            },
        ]
        with (
            patch("smith.config._query_k8s_pods", return_value=fake_items),
        ):
            pods = discover_agent_pods(default_config)
            assert pods == []


class TestPodInfo:
    def test_dataclass_creation(self) -> None:
        pod = PodInfo(
            name="test-pod", ip="10.0.0.1",
            status="Running", namespace="ns",
        )
        assert pod.name == "test-pod"
        assert pod.shell_open is False

    def test_shell_open_flag(self) -> None:
        pod = PodInfo(
            name="test-pod", ip="10.0.0.1",
            status="Running", namespace="ns",
            shell_open=True,
        )
        assert pod.shell_open is True
