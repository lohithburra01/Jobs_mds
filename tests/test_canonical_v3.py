import hashlib
import unittest
from pathlib import Path

from support import scratch
from v3_support import ARCHIVE_HASH, make_canonical_v3_fixture, validate_canonical_fixture


class CanonicalV3Tests(unittest.TestCase):
    def test_real_canonical_has_complete_four_employer_migration(self):
        from harness.canonical import check_migration, load_canonical_v3

        root = Path(__file__).resolve().parents[1]
        canonical = load_canonical_v3(root / "canonical.yaml")
        result = check_migration(canonical, root / canonical.source_archive)
        self.assertTrue(result["complete"], result)
        self.assertEqual([item.id for item in canonical.employers], [
            "corominas", "formula_dream", "think_round", "cognizant"
        ])
        self.assertEqual(len(canonical.employers), 4)
        self.assertGreaterEqual(sum(len(item.systems) for item in canonical.employers), 19)
        self.assertTrue(canonical.policies.include_independent_project)
        self.assertEqual(canonical.policies.max_bullets_per_employer, 4)

    def test_real_canonical_preserves_critical_separate_evidence(self):
        from harness.canonical import load_canonical_v3

        root = Path(__file__).resolve().parents[1]
        canonical = load_canonical_v3(root / "canonical.yaml")
        metrics = {item.id: item for item in canonical.metrics}
        facts = {item.id: item.text for item in canonical.facts}
        self.assertEqual(metrics["corominas.inference_cost"].status.value, "achieved")
        self.assertEqual(metrics["corominas.growth_target"].status.value, "target")
        self.assertIn("under 60 seconds", metrics["corominas.approval_latency"].display_text)
        self.assertIn("50M+", metrics["cognizant.daily_rows"].display_text)
        self.assertIn("48 hours", metrics["cognizant.kpi_latency"].display_text)
        self.assertTrue(any("board review" in text for text in facts.values()))
        self.assertTrue(any("durable posted-state markers" in text for text in facts.values()))
        self.assertEqual(canonical.prototype_pattern.metric_ids, [])

    def test_duplicate_yaml_keys_fail(self):
        from harness.canonical import load_yaml_unique

        with scratch() as directory:
            path = directory / "canonical.yaml"
            path.write_text("schema_version: 3\nschema_version: 4\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "duplicate key.*schema_version"):
                load_yaml_unique(path)

    def test_company_metric_cannot_be_claimed_by_local_project(self):
        canonical = make_canonical_v3_fixture()
        canonical["prototype_pattern"]["metric_ids"] = ["one.metric"]
        with self.assertRaisesRegex(ValueError, "prototype.*employer metric"):
            validate_canonical_fixture(canonical)

    def test_metric_reference_cannot_cross_systems(self):
        canonical = make_canonical_v3_fixture()
        canonical["employers"][1]["systems"][0]["metric_ids"] = ["one.metric"]
        with self.assertRaisesRegex(ValueError, "metric.*system"):
            validate_canonical_fixture(canonical)

    def test_metric_status_survives_validation(self):
        canonical = validate_canonical_fixture(make_canonical_v3_fixture())
        statuses = {metric.id: metric.status for metric in canonical.metrics}
        self.assertEqual(statuses["one.metric"].value, "achieved")
        self.assertEqual(statuses["one.target"].value, "target")

    def test_source_quotes_match_archive_lines_and_migration_covers_content(self):
        from harness.canonical import check_migration

        with scratch() as directory:
            archive = directory / "canonical-v2.md"
            archive.write_text("Built system one.\nBuilt system two.\n", encoding="utf-8")
            canonical = make_canonical_v3_fixture()
            digest = hashlib.sha256(archive.read_bytes()).hexdigest()
            canonical["source_archive_sha256"] = digest
            for collection in (canonical["facts"], canonical["metrics"], canonical["boundaries"]):
                for record in collection:
                    for reference in record["source_refs"]:
                        reference["archive_sha256"] = digest
            for employer in canonical["employers"]:
                for system in employer["systems"]:
                    for reference in system["source_refs"]:
                        reference["archive_sha256"] = digest
            result = check_migration(validate_canonical_fixture(canonical), archive)
            self.assertTrue(result["complete"], result)
            self.assertEqual(result["invalid_source_refs"], [])
            self.assertEqual(result["unmapped_nonblank_lines"], [])

    def test_changed_source_quote_fails_migration(self):
        from harness.canonical import check_migration

        with scratch() as directory:
            archive = directory / "canonical-v2.md"
            archive.write_text("Built system one.\nBuilt system two.\n", encoding="utf-8")
            canonical = make_canonical_v3_fixture()
            canonical["source_archive_sha256"] = hashlib.sha256(archive.read_bytes()).hexdigest()
            canonical["employers"][0]["systems"][0]["source_refs"][0]["quote"] = "Changed quote"
            result = check_migration(validate_canonical_fixture(canonical), archive)
            self.assertFalse(result["complete"])
            self.assertTrue(result["invalid_source_refs"])


if __name__ == "__main__":
    unittest.main()
