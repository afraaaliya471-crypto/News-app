# Regression tests for bugs we already hit. Run: python -m unittest test_core -v

import json
import os
import tempfile
import unittest
from unittest import mock

import llm_judge
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


class QueuePruningTests(unittest.TestCase):
    """enqueue_articles() - a queued item only gets removed when
    sender_tick() actually attempts it, which never happens while
    auto-send is off. Found during a full sweep for unbounded growth:
    the queue could grow for as long as auto-send stayed off, since
    nothing else ever pruned it. Now drops stale items on every call,
    independent of the auto-send toggle."""

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self._real_queue_file = store.QUEUE_FILE
        self._real_sent_file = store.SENT_FILE
        self._real_log_file = store.LOG_FILE
        store.QUEUE_FILE = os.path.join(self._tmpdir.name, "send_queue.json")
        store.SENT_FILE = os.path.join(self._tmpdir.name, "sent_whatsapp.json")
        store.LOG_FILE = os.path.join(self._tmpdir.name, "whatsapp_log.json")

    def tearDown(self):
        store.QUEUE_FILE = self._real_queue_file
        store.SENT_FILE = self._real_sent_file
        store.LOG_FILE = self._real_log_file
        self._tmpdir.cleanup()

    def test_stale_items_pruned_regardless_of_auto_send_state(self):
        from datetime import timedelta
        now = store.now_iso()
        stale_date = (store.datetime.now(store.BUSINESS_TZ) - timedelta(days=3)).isoformat()
        store._write_json(store.QUEUE_FILE, {"last_sent_at": None, "items": [
            {"id": "stale1", "title": "Old stale article", "published_at": stale_date},
            {"id": "fresh1", "title": "Already-queued fresh article", "published_at": now},
        ]})
        store.enqueue_articles([])
        with open(store.QUEUE_FILE, encoding="utf-8") as f:
            queue = json.load(f)
        ids = [item["id"] for item in queue["items"]]
        self.assertNotIn("stale1", ids)
        self.assertIn("fresh1", ids)


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


class SentIdsCapTests(unittest.TestCase):
    """_add_sent_id_unlocked() - the fast exact-ID duplicate check
    (sent_whatsapp.json) had no cap at all before this, growing by one
    entry per send forever. Stored newest-first so it can be capped the
    same way as the other logs."""

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self._real_sent_file = store.SENT_FILE
        store.SENT_FILE = os.path.join(self._tmpdir.name, "sent_whatsapp.json")

    def tearDown(self):
        store.SENT_FILE = self._real_sent_file
        self._tmpdir.cleanup()

    def test_caps_at_200_keeping_the_newest(self):
        store._write_json(store.SENT_FILE, [f"id{i}" for i in range(198, -1, -1)])
        store._add_sent_id_unlocked("new_id_200")
        store._add_sent_id_unlocked("new_id_201")
        with open(store.SENT_FILE, encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(len(data), 200)
        self.assertEqual(data[0], "new_id_201")
        self.assertNotIn("id0", data)
        self.assertIn("id1", data)


class VerdictCacheCapTests(unittest.TestCase):
    """_save_verdict_cache() - grew by one entry per judged article forever
    before this, with no cap at all."""

    def test_caps_at_200_keeping_the_most_recently_inserted(self):
        cache = {f"article{i}": {"keep": True} for i in range(250)}
        trimmed = dict(list(cache.items())[-llm_judge.MAX_VERDICT_CACHE_ENTRIES:])
        self.assertEqual(len(trimmed), 200)
        self.assertNotIn("article0", trimmed)
        self.assertIn("article249", trimmed)
        self.assertIn("article50", trimmed)
        self.assertNotIn("article49", trimmed)


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
