# test_core.py
#
# Not a full test suite - this app doesn't have one, and at its size/single-
# maintainer scale, a full suite would be more effort than the app needs.
# This covers specifically the bugs that actually happened in production and
# got fixed, so a future code change can't silently un-fix one of them
# without this failing. Run with: python -m unittest test_core -v

import unittest
from unittest import mock

import store
import app as flask_app


class DuplicateDetectionTests(unittest.TestCase):
    """titles_are_same_story() - the cross-publisher duplicate check.

    Confirmed in production to fail in both directions before this was
    fixed: it wrongly merged two different companies' contracts (because
    they shared generic press-release wording), and separately failed to
    catch a genuine duplicate of the same deal reported by two publishers.
    """

    def test_different_companies_same_boilerplate_not_merged(self):
        # Real headlines from the Send Log. Different company, different
        # city (Riyadh vs JLT/Dubai) - these are NOT the same story, even
        # though they share "Construction lands contract for... mixed-use".
        a = "Mas Engineering & Construction lands contract for Riyadh mixed-use project"
        b = "McLaren Construction lands contract for JLT mixed-use development"
        self.assertFalse(store.titles_are_same_story(a, b))

    def test_same_deal_different_publisher_wording_is_caught(self):
        # Real headlines, same underlying deal (confirmed - both sent to
        # the group a day apart before this was fixed).
        a = "Saudi-Chinese consortium wins $306m Qiddiya stadium contract"
        b = "China-Saudi JV clinches $306m Qiddiya stadium curtain-wall deal"
        self.assertTrue(store.titles_are_same_story(a, b))

    def test_genuinely_different_riyadh_contracts_stay_distinct(self):
        # Negative control - same city, same "contract" wording, different
        # project and different figure. Must not match.
        a = "Riyadh awards $301m Sheikh Jaber road contract"
        b = "Riyadh selects contractor for $534m road works"
        self.assertFalse(store.titles_are_same_story(a, b))


class LogCapTests(unittest.TestCase):
    """_trim_send_log() - keeps 'sent' and 'failed' entries capped
    independently, so a bad day of failures (confirmed: one stuck article
    produced 200+ duplicate failed entries in 13 hours) can't crowd out
    real send history."""

    def test_under_the_cap_nothing_is_trimmed(self):
        log = (
            [{"status": "sent", "id": f"s{i}"} for i in range(5)]
            + [{"status": "failed", "id": f"f{i}"} for i in range(8)]
        )
        trimmed = store._trim_send_log(log)
        self.assertEqual(len(trimmed), 13)

    def test_over_the_cap_each_status_trims_to_its_own_limit(self):
        log = (
            [{"status": "sent", "id": f"s{i}"} for i in range(250)]
            + [{"status": "failed", "id": f"f{i}"} for i in range(250)]
        )
        trimmed = store._trim_send_log(log)
        sent_kept = sum(1 for e in trimmed if e["status"] == "sent")
        failed_kept = sum(1 for e in trimmed if e["status"] == "failed")
        self.assertEqual(sent_kept, store.MAX_SENT_LOG_ENTRIES)
        self.assertEqual(failed_kept, store.MAX_FAILED_LOG_ENTRIES)


class AutoRestartTriggerTests(unittest.TestCase):
    """_note_send_failure() - the WhatsApp bot's self-heal trigger.
    Confirmed in production: this threshold/cooldown logic actually fired
    and recovered a real freeze. These tests pin the exact behavior so it
    can't accidentally get weaker (or spammier) in a future edit."""

    def setUp(self):
        flask_app._consecutive_send_failures = 0
        flask_app._last_auto_restart_at = 0.0

    @mock.patch("app.subprocess.run")
    def test_restart_fires_at_exactly_the_threshold(self, mock_run):
        for _ in range(flask_app.MAX_SEND_ATTEMPTS - 1):
            flask_app._note_send_failure()
        mock_run.assert_not_called()
        flask_app._note_send_failure()
        mock_run.assert_called_once()
        self.assertEqual(flask_app._consecutive_send_failures, 0)

    @mock.patch("app.subprocess.run")
    def test_cooldown_blocks_an_immediate_second_restart(self, mock_run):
        import time
        flask_app._consecutive_send_failures = flask_app.MAX_SEND_ATTEMPTS - 1
        flask_app._last_auto_restart_at = time.time()  # a restart "just happened"
        flask_app._note_send_failure()
        mock_run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
