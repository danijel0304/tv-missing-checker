import tempfile
import unittest
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

from app import (
    build_episode_title_map,
    build_expected_map_imdb,
    build_expected_map_tmdb,
    build_expected_map_tvdb,
    build_file_overview_items,
    choose_best_show_match,
    create_report,
    EpisodeInventory,
    extract_manual_ids,
    find_missing,
    infer_season_from_path,
    make_manual_candidate,
    mark_result_as_manually_ok,
    parse_episode_tokens,
    resolve_series_delete_target,
    scan_library,
    score_candidate,
    ScanSummary,
    ShowResult,
    TVDBClient,
)


class EpisodeParsingTests(unittest.TestCase):
    def test_parses_standard_episode_tokens(self):
        self.assertEqual(parse_episode_tokens("Show.Name.S01E02.mkv"), (1, [2]))
        self.assertEqual(parse_episode_tokens("Show Name - 2x03.mp4"), (2, [3]))

    def test_parses_multi_episode_files(self):
        self.assertEqual(parse_episode_tokens("Show.S02E05-E07.mkv"), (2, [5, 6, 7]))
        self.assertEqual(parse_episode_tokens("Show.S02E05-07.mkv"), (2, [5, 6, 7]))
        self.assertEqual(parse_episode_tokens("Show.2x05-07.mkv"), (2, [5, 6, 7]))
        self.assertEqual(parse_episode_tokens("Show.S02E05E06.mkv"), (2, [5, 6]))

    def test_missing_map_uses_expected_seasons(self):
        missing = find_missing({1: {1, 3}}, {1: {1, 2, 3}, 2: {1}})
        self.assertEqual(missing, {1: [2], 2: [1]})


class LibraryScanTests(unittest.TestCase):
    def test_root_level_mixed_series_are_not_merged_into_root_folder(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "First.Show.S01E01.mkv").write_text("")
            (root / "Second Show - 1x02.mp4").write_text("")

            shows, unparsed = scan_library(root)

        self.assertEqual(unparsed, [])
        self.assertIn("First Show", shows)
        self.assertIn("Second Show", shows)
        self.assertEqual(shows["First Show"].episodes[1], {1})
        self.assertEqual(shows["Second Show"].episodes[1], {2})

    def test_single_show_folder_with_generic_filenames_uses_folder_name(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "Example Show"
            root.mkdir()
            (root / "S01E01.mkv").write_text("")
            (root / "S01E02.mkv").write_text("")

            shows, unparsed = scan_library(root)

        self.assertEqual(unparsed, [])
        self.assertEqual(list(shows), ["Example Show"])
        self.assertEqual(shows["Example Show"].episodes[1], {1, 2})

    def test_single_show_folder_with_season_subfolder_uses_root_name(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "Example Show"
            season = root / "Season 01"
            season.mkdir(parents=True)
            (season / "S01E01.mkv").write_text("")
            (season / "S01E02.mkv").write_text("")

            shows, unparsed = scan_library(root)

        self.assertEqual(unparsed, [])
        self.assertEqual(list(shows), ["Example Show"])
        self.assertEqual(shows["Example Show"].episodes[1], {1, 2})

    def test_infers_season_from_folder_for_title_matching(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "Example Show" / "Season 02" / "Pilot.mkv"
            self.assertEqual(infer_season_from_path(path, root), 2)


class ExpectedEpisodeMapTests(unittest.TestCase):
    def test_tmdb_map_skips_specials_and_future_episodes_when_aired_only(self):
        show = {
            "id": 123,
            "name": "Example",
            "first_air_date": "2020-01-01",
            "_season_details": [
                {
                    "season_number": 0,
                    "episodes": [{"episode_number": 1, "air_date": "2000-01-01"}],
                },
                {
                    "season_number": 1,
                    "episodes": [
                        {"episode_number": 1, "air_date": "2000-01-01"},
                        {"episode_number": 2, "air_date": "2099-01-01"},
                    ],
                },
            ],
        }

        name, year, expected, url = build_expected_map_tmdb(show, aired_only=True)

        self.assertEqual(name, "Example")
        self.assertEqual(year, 2020)
        self.assertEqual(expected, {1: {1}})
        self.assertEqual(url, "https://www.themoviedb.org/tv/123")

    def test_imdb_map_uses_imdb_episode_number_field_and_link(self):
        show = {
            "id": "tt1234567",
            "name": "Example",
            "first_air_date": "2020-01-01",
            "_season_details": [
                {
                    "season_number": 1,
                    "episodes": [
                        {"number": 1, "name": "Pilot", "airdate": "2000-01-01"},
                    ],
                },
            ],
        }

        name, year, expected, url = build_expected_map_imdb(show, aired_only=True)
        title_map = build_episode_title_map(show, "IMDb", aired_only=True)

        self.assertEqual(name, "Example")
        self.assertEqual(year, 2020)
        self.assertEqual(expected, defaultdict(set, {1: {1}}))
        self.assertEqual(title_map, {1: {1: "Pilot"}})
        self.assertEqual(url, "https://www.imdb.com/title/tt1234567/episodes/")

    def test_tvdb_map_uses_episode_number_and_dereferrer_link(self):
        show = {
            "id": 123,
            "name": "Example",
            "year": "2020",
            "_episodes": [
                {"seasonNumber": 1, "number": 1, "aired": "2020-01-01", "name": "Pilot"},
                {"seasonNumber": 1, "number": 2, "aired": "2099-01-01", "name": "Future"},
                {"seasonNumber": 0, "number": 1, "aired": "2020-01-01", "name": "Special"},
            ],
        }

        name, year, expected, url = build_expected_map_tvdb(show, aired_only=True)
        title_map = build_episode_title_map(show, "TVDB", aired_only=True)

        self.assertEqual(name, "Example")
        self.assertEqual(year, 2020)
        self.assertEqual(expected, {1: {1}})
        self.assertEqual(title_map, {1: {1: "Pilot"}})
        self.assertEqual(url, "https://thetvdb.com/dereferrer/series/123")

    def test_tvdb_token_expires_after_seven_days_locally(self):
        fresh = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        expired = (datetime.now() - timedelta(days=8)).strftime("%Y-%m-%d %H:%M:%S")

        self.assertFalse(TVDBClient(token="abc", token_created_at=fresh).token_expired())
        self.assertTrue(TVDBClient(token="abc", token_created_at=expired).token_expired())


class ManualMatchTests(unittest.TestCase):
    def test_extracts_direct_ids_from_links(self):
        self.assertEqual(extract_manual_ids("https://www.imdb.com/title/tt1234567/episodes/", "IMDb"), ["tt1234567"])
        self.assertEqual(extract_manual_ids("https://www.tvmaze.com/shows/123/example", "TVMaze"), ["123"])
        self.assertEqual(extract_manual_ids("https://www.themoviedb.org/tv/456-example", "TMDb"), ["456"])
        self.assertEqual(extract_manual_ids("https://www.thetvdb.com/dereferrer/series/321", "TVDB"), ["321"])
        self.assertEqual(extract_manual_ids("789", "TVMaze"), ["789"])

    def test_manual_candidate_previews_missing_status(self):
        inv = EpisodeInventory(show_name="Example Show", year=2020)
        inv.episodes[1] = {1}
        show = {
            "id": 123,
            "name": "Example Show",
            "premiered": "2020-01-01",
            "url": "https://www.tvmaze.com/shows/123/example-show",
            "_embedded": {
                "episodes": [
                    {"season": 1, "number": 1, "airdate": "2020-01-01", "name": "Pilot"},
                    {"season": 1, "number": 2, "airdate": "2020-01-08", "name": "Second"},
                ],
            },
        }

        candidate = make_manual_candidate(inv, show, "TVMaze", "Example Show", aired_only=True)

        self.assertIsNotNone(candidate)
        self.assertEqual(candidate.status, "MISSING")
        self.assertEqual(candidate.missing_count, 1)
        self.assertEqual(candidate.source_url, "https://www.tvmaze.com/shows/123/example-show")


class FileOverviewTests(unittest.TestCase):
    def test_builds_have_missing_and_unknown_rows(self):
        result = ShowResult(
            local_name="Example Show",
            seasons_local={1: [1]},
            seasons_expected={1: [1, 2]},
            missing={1: [2]},
            files=[
                "/library/Example Show/Example.Show.S01E01.mkv",
                "/library/Example Show/Season 01/Behind the Scenes.mkv",
            ],
        )

        items = build_file_overview_items(result)
        statuses = [item.status for item in items]

        self.assertIn("HAVE", statuses)
        self.assertIn("MISSING", statuses)
        self.assertIn("UNKNOWN", statuses)
        self.assertEqual(next(item for item in items if item.status == "MISSING").episode_label, "S01E02")


class ManualOverrideTests(unittest.TestCase):
    def test_marks_missing_result_as_ok(self):
        result = ShowResult(
            local_name="Example Show",
            status="MISSING",
            missing={1: [2]},
            match_reason="online missing",
        )

        mark_result_as_manually_ok(result)

        self.assertEqual(result.status, "OK")
        self.assertEqual(result.missing, {})
        self.assertEqual(result.match_reason, "Ručno označeno kao OK.")


class ReportTests(unittest.TestCase):
    def test_report_includes_detailed_episode_and_match_information(self):
        summary = ScanSummary(
            root="/library",
            created_at="2026-07-10 12:00:00",
            missing_count=1,
            results=[
                ShowResult(
                    local_name="Example Show",
                    local_year=2020,
                    official_name="Example Show",
                    official_year=2020,
                    status="MISSING",
                    source="TVMaze",
                    match_score=88,
                    match_reason="test reason",
                    matched_query="Example Show 2020",
                    source_url="https://www.tvmaze.com/shows/123/example-show",
                    seasons_local={1: [1]},
                    seasons_expected={1: [1, 2, 3]},
                    missing={1: [2, 3]},
                    files=["/library/Example Show/Example.Show.S01E01.mkv"],
                )
            ],
        )

        report = create_report(summary)

        self.assertIn("Series in report: 1", report)
        self.assertIn("Local video files: 1", report)
        self.assertIn("Episode summary: have 1/3 | missing 2", report)
        self.assertIn("Match reason: test reason", report)
        self.assertIn("Local folder: /library/Example Show", report)
        self.assertIn("Local: 1 episodes (E01)", report)
        self.assertIn("Expected: 3 episodes (E01-E03)", report)
        self.assertIn("Missing: E02-E03", report)

        hr_report = create_report(summary, language="hr")

        self.assertIn("Serija u izvještaju: 1", hr_report)
        self.assertIn("Sažetak epizoda: imam 1/3 | nedostaje 2", hr_report)


class SeriesDeleteTargetTests(unittest.TestCase):
    def test_deletes_series_folder_not_season_subfolder(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            show_folder = root / "Example Show"
            season_folder = show_folder / "Season 01"
            season_folder.mkdir(parents=True)
            file_path = season_folder / "Example.Show.S01E01.mkv"
            file_path.write_text("")
            result = ShowResult(local_name="Example Show", files=[str(file_path)])

            target = resolve_series_delete_target(result, root, total_results=2)

        self.assertIsNotNone(target)
        self.assertEqual(target.kind, "folder")
        self.assertEqual(target.paths, [show_folder])

    def test_deletes_only_files_when_series_is_mixed_in_scan_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            file_path = root / "Example.Show.S01E01.mkv"
            file_path.write_text("")
            result = ShowResult(local_name="Example Show", files=[str(file_path)])

            target = resolve_series_delete_target(result, root, total_results=2)

        self.assertIsNotNone(target)
        self.assertEqual(target.kind, "files")
        self.assertEqual(target.paths, [file_path])


class CandidateScoringTests(unittest.TestCase):
    def test_wrong_year_candidate_cannot_pass_auto_match_threshold(self):
        good_score, _good_reason = score_candidate(
            "Legacy Show",
            1980,
            "Legacy Show",
            1980,
            {1: {1}},
            {1: {1}},
        )
        wrong_score, wrong_reason = score_candidate(
            "Legacy Show",
            1980,
            "Legacy Show",
            2005,
            {1: {1}},
            {1: {1}},
        )

        self.assertGreater(good_score, wrong_score)
        self.assertLess(wrong_score, 42)
        self.assertIn("mismatch", wrong_reason)


class MatchFlowTests(unittest.TestCase):
    def test_skips_imdb_when_tvmaze_match_is_confident(self):
        inv = EpisodeInventory(show_name="Example Show", year=2020)
        inv.guesses = ["Example Show"]
        inv.year_guesses = [2020]
        inv.episodes[1] = {1, 2}

        class FakeTVMaze:
            def search_shows(self, query):
                return [{"show": {"id": 123}}]

            def fetch_show_with_episodes_by_id(self, show_id):
                return {
                    "id": show_id,
                    "name": "Example Show",
                    "premiered": "2020-01-01",
                    "_embedded": {
                        "episodes": [
                            {"season": 1, "number": 1, "airdate": "2020-01-01"},
                            {"season": 1, "number": 2, "airdate": "2020-01-08"},
                        ]
                    },
                }

        class FakeTMDb:
            enabled = False

        class FakeTVDB:
            enabled = False

        class FakeIMDb:
            called = False

            def search_shows(self, query):
                self.called = True
                return []

        imdb = FakeIMDb()
        best_show, matched_query, score, reason, source = choose_best_show_match(
            FakeTVMaze(),
            FakeTMDb(),
            FakeTVDB(),
            imdb,
            inv,
            aired_only=True,
        )

        self.assertIsNotNone(best_show)
        self.assertEqual(matched_query, "Example Show 2020")
        self.assertGreaterEqual(score, 72)
        self.assertEqual(source, "TVMaze")
        self.assertFalse(imdb.called, reason)

    def test_prefers_same_name_candidate_with_matching_year(self):
        inv = EpisodeInventory(show_name="Legacy Show", year=1980)
        inv.guesses = ["Legacy Show"]
        inv.year_guesses = [1980]
        inv.episodes[1] = {1}

        class FakeTVMaze:
            def __init__(self):
                self.queries = []

            def search_shows(self, query):
                self.queries.append(query)
                return [{"show": {"id": 1}}, {"show": {"id": 2}}]

            def fetch_show_with_episodes_by_id(self, show_id):
                year = 2005 if show_id == 1 else 1980
                return {
                    "id": show_id,
                    "name": "Legacy Show",
                    "premiered": f"{year}-01-01",
                    "_embedded": {
                        "episodes": [
                            {"season": 1, "number": 1, "airdate": f"{year}-01-01"},
                        ]
                    },
                }

        class FakeTMDb:
            enabled = False

        class FakeTVDB:
            enabled = False

        class FakeIMDb:
            def search_shows(self, query):
                return []

        tvmaze = FakeTVMaze()
        best_show, matched_query, score, reason, source = choose_best_show_match(
            tvmaze,
            FakeTMDb(),
            FakeTVDB(),
            FakeIMDb(),
            inv,
            aired_only=True,
        )

        self.assertIsNotNone(best_show)
        self.assertEqual(best_show["premiered"], "1980-01-01")
        self.assertEqual(matched_query, "Legacy Show 1980")
        self.assertEqual(source, "TVMaze")
        self.assertGreaterEqual(score, 82)
        self.assertIn("Legacy Show 1980", tvmaze.queries)


if __name__ == "__main__":
    unittest.main()
