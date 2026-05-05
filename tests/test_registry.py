"""Tests for the attack registry — completeness, uniqueness, validity."""

from __future__ import annotations

from pathlib import Path

import pytest

from smith.registry import ATTACKS, ATTACKS_BY_ID, Phase, attacks_by_phase, get_attack


class TestRegistryCompleteness:
    """Every real script has a registry entry and vice versa."""

    def _script_files(self, scripts_dir: Path) -> set[str]:
        """Get all .sh filenames from scripts/attacks/ (excluding lib.sh)."""
        excluded = {"lib.sh"}
        return {
            f.name
            for f in scripts_dir.glob("*.sh")
            if f.name not in excluded
        }

    def test_every_script_has_registry_entry(self, scripts_dir: Path) -> None:
        script_files = self._script_files(scripts_dir)
        registry_scripts = {a.script for a in ATTACKS}
        missing = script_files - registry_scripts
        assert not missing, f"Scripts without registry entry: {missing}"

    def test_no_phantom_registry_entries(self, scripts_dir: Path) -> None:
        script_files = self._script_files(scripts_dir)
        registry_scripts = {a.script for a in ATTACKS}
        phantom = registry_scripts - script_files
        assert not phantom, f"Registry entries without script: {phantom}"


class TestRegistryUniqueness:
    def test_no_duplicate_ids(self) -> None:
        ids = [a.id for a in ATTACKS]
        assert len(ids) == len(set(ids)), f"Duplicate IDs: {ids}"

    def test_no_duplicate_scripts(self) -> None:
        scripts = [a.script for a in ATTACKS]
        assert len(scripts) == len(set(scripts)), f"Duplicate scripts: {scripts}"


class TestRegistryFields:
    @pytest.mark.parametrize("attack", ATTACKS, ids=lambda a: a.id)
    def test_required_fields_populated(self, attack) -> None:
        assert attack.id, "id must not be empty"
        assert attack.name, "name must not be empty"
        assert attack.script, "script must not be empty"
        assert attack.description, "description must not be empty"
        assert isinstance(attack.phase, Phase)
        assert isinstance(attack.requires_bind_shell, bool)

    @pytest.mark.parametrize("attack", ATTACKS, ids=lambda a: a.id)
    def test_script_name_ends_with_sh(self, attack) -> None:
        assert attack.script.endswith(".sh")

    @pytest.mark.parametrize("attack", ATTACKS, ids=lambda a: a.id)
    def test_enrichment_fields_populated(self, attack) -> None:
        assert attack.technique, "technique must not be empty"
        assert attack.impact, "impact must not be empty"
        assert attack.briefing, "briefing must not be empty"
        assert isinstance(attack.loot_types, list)
        assert isinstance(attack.steps, list)
        assert len(attack.steps) >= 2, "at least 2 steps required"

    @pytest.mark.parametrize("attack", ATTACKS, ids=lambda a: a.id)
    def test_technique_looks_like_mitre(self, attack) -> None:
        assert attack.technique.startswith("T"), f"technique should start with T: {attack.technique}"


class TestRegistryLookup:
    def test_get_attack_valid(self) -> None:
        attack = get_attack("recon")
        assert attack.id == "recon"
        assert attack.script == "attack-recon.sh"

    def test_get_attack_invalid_raises(self) -> None:
        with pytest.raises(ValueError, match="Unknown attack 'nonexistent'"):
            get_attack("nonexistent")

    def test_attacks_by_phase_covers_all(self) -> None:
        grouped = attacks_by_phase()
        total = sum(len(v) for v in grouped.values())
        assert total == len(ATTACKS)

    def test_attacks_by_id_consistent(self) -> None:
        assert len(ATTACKS_BY_ID) == len(ATTACKS)
