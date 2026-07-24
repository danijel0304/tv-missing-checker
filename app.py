#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import html
import json
import os
import queue
import re
import shutil
import subprocess
import sys
import threading
import traceback
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from datetime import date, datetime
from datetime import timedelta
from difflib import SequenceMatcher
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk

VIDEO_EXTS = {
    ".mkv", ".mp4", ".avi", ".mov", ".wmv", ".m4v", ".ts", ".m2ts", ".webm",
    ".mpg", ".mpeg", ".flv", ".ogv", ".iso"
}

EPISODE_SEPARATORS = r"[-_ \u2013\u2014]"
SEASON_EP_PATTERNS = [
    re.compile(rf'(?i)\bS(?P<season>\d{{1,2}})E(?P<ep1>\d{{1,3}})(?:{EPISODE_SEPARATORS}?E?(?P<ep2>\d{{1,3}}))?(?:{EPISODE_SEPARATORS}?E?(?P<ep3>\d{{1,3}}))?(?:{EPISODE_SEPARATORS}?E?(?P<ep4>\d{{1,3}}))?\b'),
    re.compile(rf'(?i)\b(?P<season>\d{{1,2}})x(?P<ep1>\d{{1,3}})(?:{EPISODE_SEPARATORS}?(?P<ep2>\d{{1,3}}))?(?:{EPISODE_SEPARATORS}?(?P<ep3>\d{{1,3}}))?(?:{EPISODE_SEPARATORS}?(?P<ep4>\d{{1,3}}))?\b'),
]
EPISODE_TOKEN_CLEANUP_RE = re.compile(
    rf'(?i)\b(?:S\d{{1,2}}E\d{{1,3}}(?:{EPISODE_SEPARATORS}?E?\d{{1,3}}){{0,4}}|\d{{1,2}}x\d{{1,3}}(?:{EPISODE_SEPARATORS}?\d{{1,3}}){{0,4}})\b'
)

YEAR_IN_PARENS = re.compile(r'\((19|20)\d{2}\)')
YEAR_ANYWHERE = re.compile(r'\b((?:19|20)\d{2})\b')
SEASON_FOLDER_RE = re.compile(r'(?i)\b(?:season|series|serija|stagione|stagion|book|part|volume|vol|s)\s*[-._ ]*(\d{1,2})\b')
STANDALONE_SEASON_RE = re.compile(r'(?i)^s(\d{1,2})$')
NOISE_TOKENS = re.compile(
    r'(?i)\b(2160p|1080p|720p|480p|x264|x265|h264|h265|hevc|bluray|bdrip|web[- ]?dl|webrip|hdrip|dvdrip|aac|dts|ac3|amzn|nf|proper|repack|remux|internal|multi|subbed|dubbed|extended|criterion|readnfo)\b'
)
STOP_WORDS = {"the", "a", "an", "and", "of", "to", "in", "us", "uk", "tv", "series", "show"}
CONFIG_PATH = Path.home() / ".tv_missing_checker.json"
HTTP_TIMEOUT_SECONDS = 10
MAX_SCAN_WORKERS = 4
MAX_GUESSES_PER_SHOW = 4
MAX_TVMAZE_CANDIDATES = 5
MAX_TMDB_CANDIDATES = 4
MAX_TVDB_CANDIDATES = 4
MAX_IMDB_CANDIDATES = 3
DEFAULT_TVDB_API_KEY = (
    os.environ.get("TV_MISSING_CHECKER_TVDB_API_KEY")
    or os.environ.get("TVDB_API_KEY")
    or ""
)
TVDB_TOKEN_TTL_DAYS = 7
DEFAULT_LANGUAGE = "en"
APP_VERSION = "1.0.2"
GITHUB_REPO = "danijel0304/tv-missing-checker"
GITHUB_RELEASES_API = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
GITHUB_RELEASES_URL = f"https://github.com/{GITHUB_REPO}/releases/latest"
PAYPAL_DONATE_URL = "https://www.paypal.com/paypalme/danijel0304"
LANGUAGE_CHOICES = (("en", "English"), ("hr", "Hrvatski"))
LANGUAGE_LABEL_BY_CODE = dict(LANGUAGE_CHOICES)
LANGUAGE_CODE_BY_LABEL = {label: code for code, label in LANGUAGE_CHOICES}

TRANSLATIONS = {
    "en": {
        "app_title": "TV Missing Checker",
        "subtitle": "Check local seasons, missing episodes, and manual matches.",
        "version_label": "Version {version}",
        "language": "Language",
        "check_updates": "Update",
        "donate": "Donate",
        "checking_updates": "Checking updates...",
        "update_available_title": "Update available",
        "update_available_msg": "A new TV Missing Checker version is available.\n\nCurrent version: {current}\nNew version: {latest}\n\nOpen the download page?",
        "update_current_title": "Up to date",
        "update_current_msg": "You are using the latest version ({current}).",
        "update_failed_title": "Update check failed",
        "update_failed_msg": "I could not check for a new version. Check the internet connection and try again.",
        "update_in_progress_title": "Check in progress",
        "update_in_progress_msg": "The update check is already running.",
        "library": "Library",
        "main_folder": "Main TV series folder",
        "choose_folder": "Browse",
        "start_scan": "Start scan",
        "online_sources": "Online sources",
        "scan_settings": "Scan settings",
        "aired_only": "Only aired episodes",
        "include_unparsed": "Include unrecognized files",
        "exclude_ok_report": "Exclude OK from TXT/JSON report",
        "status": "Status",
        "status_filter": "Status filter",
        "all": "All",
        "missing": "Missing",
        "unmatched": "Unmatched",
        "hide_ok": "Hide OK series",
        "displayed": "Displayed",
        "results": "Results",
        "clear": "Clear",
        "remove_ok": "Remove OK",
        "series": "Series",
        "year_short": "Year",
        "source": "Source",
        "matched_as": "Matched as",
        "missing_count": "# Missing",
        "details": "Details",
        "missing_overview": "Missing overview",
        "txt_report": "TXT report",
        "selected_actions": "Actions for selected series",
        "manual_match": "Manual match",
        "files": "Files",
        "open_web": "Open web",
        "mark_ok": "Mark OK",
        "open_folder": "Open folder",
        "save_txt": "Save TXT",
        "save_json": "Save JSON",
        "copy_missing": "Copy missing",
        "copy_unmatched": "Copy unmatched",
        "delete_disk": "Delete from disk",
        "open_browser": "Open in browser",
        "open_series_folder": "Open series folder",
        "file_overview": "File overview",
        "check_tmdb": "Check with TMDb",
        "mark_series_ok": "Mark series as OK",
        "copy_link": "Copy link",
        "delete_series_disk": "Delete series from disk...",
        "copy": "Copy",
        "status_choose_folder": "Choose a TV series folder.",
        "progress": "Progress: {done}/{total}",
        "missing_folder_title": "Missing folder",
        "missing_folder_msg": "Choose a TV series folder.",
        "invalid_folder_title": "Invalid folder",
        "invalid_folder_msg": "The selected path is not a folder.",
        "scanning_library": "Scanning library...",
        "no_video_files": "No video files to check in the selected folder.",
        "found_summary": "Found series: {shows} | Video files: {videos} | Sources: {sources}{parallel}",
        "parallel": " | Parallel: {workers}",
        "checking": "Checking: {show}{suffix}",
        "checking_suffix": " ({workers} parallel)",
        "done": "Done.",
        "error": "Error.",
        "selected_text_copied": "Selected text copied to clipboard.",
        "series_label": "Series",
        "query": "Query",
        "score": "Score",
        "reason": "Reason",
        "local_seasons": "Local seasons",
        "episodes": "episodes",
        "online_expected": "Online expected",
        "have": "Have",
        "missing_for": "Missing overview for",
        "total_missing_episodes": "Total missing episodes",
        "seasons_with_missing": "Seasons with missing episodes",
        "missing_none": "nothing",
        "series_complete": "This series is complete according to the online database.",
        "missing_no_data": "There is not enough data for a missing episode overview because the match is not confirmed.",
        "manual_match_title": "Manual match",
        "select_series_first": "Select a series from the results first.",
        "local_series": "Local series",
        "name": "Name",
        "id_link": "ID/link",
        "all_sources": "All sources",
        "manual_search_hint": "Enter a title for live search or a direct ID/link below.",
        "close": "Close",
        "open_link": "Open link",
        "apply_selected": "Apply selected",
        "select_candidate": "Select a candidate from the list.",
        "matched_manually": "Manually matched: {local} -> {name}",
        "previous_search_wait": "Waiting for the previous search to finish...",
        "enter_name_id": "Enter a title, ID, or link.",
        "tmdb_missing": "TMDb key/token is not set.",
        "tvdb_missing": "TheTVDB API key is not set.",
        "searching_candidates": "Searching candidates...",
        "found_candidates": "Found candidates: {count}",
        "no_candidates": "No candidates for that query.",
        "live_min_chars": "Enter at least 3 characters for live search.",
        "live_searching": "Live candidate search...",
        "enter_id_link": "Enter an ID or link.",
        "loading_id": "Loading direct ID/link...",
        "search": "Search",
        "load_id": "Load ID",
        "tmdb_token_prompt_title": "TMDb token",
        "tmdb_token_prompt": "Enter TMDb Bearer token (v4). Click Cancel to enter an API key instead.",
        "tmdb_api_key_prompt_title": "TMDb API key",
        "tmdb_api_key_prompt": "Enter TMDb API key (v3):",
        "tmdb_check": "TMDb check: {name}",
        "tmdb_no_match": "TMDb did not find a good match for:\n{name}",
        "tmdb_no_match_status": "TMDb did not find a good match.",
        "tmdb_error": "TMDb error:\n{error}",
        "tmdb_done": "TMDb check finished: {name}",
        "no_results_title": "No results",
        "run_scan_first": "Run a scan first.",
        "save_txt_title": "Save TXT report",
        "save_json_title": "Save JSON report",
        "saved": "Saved: {path}",
        "no_missing_series": "No missing series.",
        "missing_copied": "Missing list copied to clipboard.",
        "no_unmatched_series": "No unmatched series.",
        "unmatched_copied": "Unmatched list copied to clipboard.",
        "marked_ok_status": "Manually marked as OK: {name}",
        "delete_active_title": "Scan is active",
        "delete_active_msg": "Wait for the scan to finish before deleting from disk.",
        "delete_title": "Delete from disk",
        "delete_select_msg": "Select a series from the results first.",
        "delete_no_path": "This series has no local path I can delete.",
        "delete_folder_action": "This folder and all of its contents will be permanently deleted:",
        "delete_files_action": "{count} local files for this series will be permanently deleted:",
        "delete_confirm_msg": "{action}\n\n{target}\n\nThis action cannot be undone from the app. Continue?",
        "delete_extra_title": "Additional confirmation",
        "delete_extra_msg": "To permanently delete '{name}', type: DELETE",
        "delete_cancelled": "Deletion cancelled.",
        "delete_cancelled_confirm": "Deletion cancelled because the extra confirmation was not entered.",
        "delete_failed_title": "Deletion was not completed",
        "delete_failed_status": "Deletion was not completed. Check the error message.",
        "deleted_status": "Series deleted from disk: {name}",
        "more_files": "... and {count} more files",
        "file_status_have": "Have",
        "file_status_unknown": "Unknown",
        "file_status_missing": "Missing",
        "file_overview_title": "File overview",
        "unknown": "Unknown",
        "file_summary": "{name}{year} | Have: {have} | Missing: {missing} | Unknown: {unknown}",
        "episode": "Episode",
        "file_episode": "File / episode",
        "path": "Path",
        "not_on_disk": "not on disk",
        "file_overview_hint": "Double-click a local file to open it in the file manager.",
        "select_local_file": "Select a local file.",
        "missing_no_local_file": "Missing episode has no local file on disk.",
        "opened_file_manager": "Opened in file manager.",
        "open_file_manager_error": "Cannot open in file manager:\n{error}",
        "no_local_path": "This series has no local path.",
        "opened_series_folder": "Opened series folder.",
        "open_folder_error": "Cannot open folder:\n{error}",
        "open_selected": "Open selected",
        "open_web_status": "Series link opened in browser.",
        "open_search_status": "Search opened in browser.",
        "link_copied": "Link copied to clipboard.",
        "folder_opened_manager": "Series folder opened in file manager.",
        "language_locked_scanning": "Language can be changed after the current scan finishes.",
        "report_date": "Date",
        "report_series": "Series in report",
        "report_local_files": "Local video files",
        "report_local_episodes": "Locally recognized episodes",
        "report_expected": "Online expected episodes",
        "report_total_missing": "Total missing episodes",
        "report_ok_series": "OK series",
        "report_missing_series": "Series with missing episodes",
        "report_unmatched": "Failed online matches / empty database",
        "report_unparsed": "Unrecognized video files",
        "report_match_query": "Query attempt",
        "report_match_reason": "Match reason",
        "report_local_folder": "Local folder",
        "report_local_file_count": "Local files",
        "report_episode_summary": "Episode summary",
        "report_i_have": "have",
        "report_missing_word": "missing",
        "report_local_have": "locally have",
        "report_online_unavailable": "online expected unavailable",
        "report_seasons": "Seasons",
        "report_local": "Local",
        "report_expected_word": "Expected",
        "report_missing_label": "Missing",
        "report_local_seasons": "Local seasons",
        "report_unparsed_heading": "UNRECOGNIZED VIDEO FILES",
    },
    "hr": {
        "app_title": "TV Missing Checker",
        "subtitle": "Provjera lokalnih sezona, missing epizoda i ručni match.",
        "version_label": "Verzija {version}",
        "language": "Jezik",
        "check_updates": "Update",
        "donate": "Donacija",
        "checking_updates": "Provjeravam update...",
        "update_available_title": "Dostupna je nova verzija",
        "update_available_msg": "Dostupna je nova verzija programa TV Missing Checker.\n\nTrenutna verzija: {current}\nNova verzija: {latest}\n\nOtvoriti stranicu za preuzimanje?",
        "update_current_title": "Program je ažuran",
        "update_current_msg": "Koristite najnoviju verziju programa ({current}).",
        "update_failed_title": "Provjera nije uspjela",
        "update_failed_msg": "Nisam uspio provjeriti novu verziju. Provjerite internet vezu i pokušajte ponovno.",
        "update_in_progress_title": "Provjera je u tijeku",
        "update_in_progress_msg": "Provjera nove verzije već je pokrenuta.",
        "library": "Biblioteka",
        "main_folder": "Glavni folder sa serijama",
        "choose_folder": "Odaberi folder",
        "start_scan": "Pokreni scan",
        "online_sources": "Online izvori",
        "scan_settings": "Postavke scana",
        "aired_only": "Samo emitirane epizode",
        "include_unparsed": "Uključi neprepoznate fileove",
        "exclude_ok_report": "Bez OK u TXT/JSON reportu",
        "status": "Status",
        "status_filter": "Filter statusa",
        "all": "Sve",
        "missing": "Missing",
        "unmatched": "Unmatched",
        "hide_ok": "Sakrij OK serije",
        "displayed": "Prikazano",
        "results": "Rezultati",
        "clear": "Očisti",
        "remove_ok": "Makni OK",
        "series": "Serija",
        "year_short": "God.",
        "source": "Izvor",
        "matched_as": "Matched as",
        "missing_count": "# Missing",
        "details": "Detalji",
        "missing_overview": "Missing pregled",
        "txt_report": "TXT report",
        "selected_actions": "Akcije za odabranu seriju",
        "manual_match": "Ručno matchaj",
        "files": "Datoteke",
        "open_web": "Otvori web",
        "mark_ok": "Označi OK",
        "open_folder": "Otvori folder",
        "save_txt": "Spremi TXT",
        "save_json": "Spremi JSON",
        "copy_missing": "Kopiraj missing",
        "copy_unmatched": "Kopiraj unmatched",
        "delete_disk": "Izbriši s diska",
        "open_browser": "Otvori u browseru",
        "open_series_folder": "Otvori folder serije",
        "file_overview": "Pregled datoteka",
        "check_tmdb": "Provjeri s TMDb",
        "mark_series_ok": "Označi seriju kao OK",
        "copy_link": "Kopiraj link",
        "delete_series_disk": "Izbriši seriju s diska...",
        "copy": "Kopiraj",
        "status_choose_folder": "Odaberi folder sa serijama.",
        "progress": "Napredak: {done}/{total}",
        "missing_folder_title": "Nedostaje folder",
        "missing_folder_msg": "Odaberi folder sa serijama.",
        "invalid_folder_title": "Neispravan folder",
        "invalid_folder_msg": "Odabrani path nije folder.",
        "scanning_library": "Skeniram biblioteku...",
        "no_video_files": "Nema video fileova za provjeru u odabranom folderu.",
        "found_summary": "Pronađeno serija: {shows} | Video fileova: {videos} | Izvor: {sources}{parallel}",
        "parallel": " | Paralelno: {workers}",
        "checking": "Provjeravam: {show}{suffix}",
        "checking_suffix": " ({workers} paralelno)",
        "done": "Gotovo.",
        "error": "Greška.",
        "selected_text_copied": "Odabrani tekst je kopiran u clipboard.",
        "series_label": "Serija",
        "query": "Upit",
        "score": "Score",
        "reason": "Razlog",
        "local_seasons": "Lokalne sezone",
        "episodes": "epizoda",
        "online_expected": "Online očekivano",
        "have": "Imam",
        "missing_for": "Pregled missing za",
        "total_missing_episodes": "Ukupno nedostaje epizoda",
        "seasons_with_missing": "Broj sezona s missing epizodama",
        "missing_none": "ništa",
        "series_complete": "Ova serija je kompletna prema online bazi.",
        "missing_no_data": "Nema dovoljno podataka za pregled missing epizoda jer match nije potvrđen.",
        "manual_match_title": "Ručni match",
        "select_series_first": "Prvo odaberi seriju iz rezultata.",
        "local_series": "Lokalna serija",
        "name": "Naziv",
        "id_link": "ID/link",
        "all_sources": "Svi izvori",
        "manual_search_hint": "Upiši naziv za live pretragu ili direktni ID/link ispod.",
        "close": "Zatvori",
        "open_link": "Otvori link",
        "apply_selected": "Primijeni odabrano",
        "select_candidate": "Odaberi kandidata iz liste.",
        "matched_manually": "Ručno matchano: {local} -> {name}",
        "previous_search_wait": "Čekam da završi prethodna pretraga...",
        "enter_name_id": "Upiši naziv, ID ili link.",
        "tmdb_missing": "TMDb ključ/token nije unesen.",
        "tvdb_missing": "TheTVDB API key nije unesen.",
        "searching_candidates": "Tražim kandidate...",
        "found_candidates": "Pronađeno kandidata: {count}",
        "no_candidates": "Nema kandidata za taj upit.",
        "live_min_chars": "Za live pretragu upiši barem 3 znaka.",
        "live_searching": "Live pretraga kandidata...",
        "enter_id_link": "Upiši ID ili link.",
        "loading_id": "Učitavam direktni ID/link...",
        "search": "Traži",
        "load_id": "Učitaj ID",
        "tmdb_token_prompt_title": "TMDb token",
        "tmdb_token_prompt": "Unesi TMDb Bearer token (v4). Klikni Cancel ako želiš umjesto toga unijeti API key.",
        "tmdb_api_key_prompt_title": "TMDb API key",
        "tmdb_api_key_prompt": "Unesi TMDb API key (v3):",
        "tmdb_check": "TMDb provjera: {name}",
        "tmdb_no_match": "TMDb nije pronašao dobar match za:\n{name}",
        "tmdb_no_match_status": "TMDb nije pronašao dobar match.",
        "tmdb_error": "TMDb greška:\n{error}",
        "tmdb_done": "TMDb provjera gotova: {name}",
        "no_results_title": "Nema rezultata",
        "run_scan_first": "Prvo pokreni scan.",
        "save_txt_title": "Spremi TXT report",
        "save_json_title": "Spremi JSON report",
        "saved": "Spremljeno: {path}",
        "no_missing_series": "Nema missing serija.",
        "missing_copied": "Missing lista kopirana u clipboard.",
        "no_unmatched_series": "Nema unmatched serija.",
        "unmatched_copied": "Unmatched lista kopirana u clipboard.",
        "marked_ok_status": "Ručno označeno kao OK: {name}",
        "delete_active_title": "Scan je aktivan",
        "delete_active_msg": "Pričekaj da scan završi prije brisanja s diska.",
        "delete_title": "Brisanje s diska",
        "delete_select_msg": "Prvo odaberi seriju iz rezultata.",
        "delete_no_path": "Ova serija nema lokalnu putanju koju mogu obrisati.",
        "delete_folder_action": "Trajno će se obrisati ovaj folder i sav njegov sadržaj:",
        "delete_files_action": "Trajno će se obrisati {count} lokalnih datoteka ove serije:",
        "delete_confirm_msg": "{action}\n\n{target}\n\nOva akcija se ne može poništiti iz programa. Nastaviti?",
        "delete_extra_title": "Dodatna potvrda",
        "delete_extra_msg": "Za konačno brisanje serije '{name}' upiši: IZBRISI",
        "delete_cancelled": "Brisanje je otkazano.",
        "delete_cancelled_confirm": "Brisanje je otkazano jer dodatna potvrda nije unesena.",
        "delete_failed_title": "Brisanje nije dovršeno",
        "delete_failed_status": "Brisanje nije dovršeno. Provjeri poruku greške.",
        "deleted_status": "Serija je obrisana s diska: {name}",
        "more_files": "... i još {count} datoteka",
        "file_status_have": "Imam",
        "file_status_unknown": "Ne poznaje",
        "file_status_missing": "Nedostaje",
        "file_overview_title": "Pregled datoteka",
        "unknown": "Ne poznaje",
        "file_summary": "{name}{year} | Imam: {have} | Nedostaje: {missing} | Ne poznaje: {unknown}",
        "episode": "Epizoda",
        "file_episode": "Datoteka / epizoda",
        "path": "Putanja",
        "not_on_disk": "nije na disku",
        "file_overview_hint": "Dvoklik na lokalnu datoteku otvara je u file manageru.",
        "select_local_file": "Odaberi lokalnu datoteku.",
        "missing_no_local_file": "Missing epizoda nema lokalnu datoteku na disku.",
        "opened_file_manager": "Otvoreno u file manageru.",
        "open_file_manager_error": "Ne mogu otvoriti u file manageru:\n{error}",
        "no_local_path": "Ova serija nema lokalnu putanju.",
        "opened_series_folder": "Otvoren folder serije.",
        "open_folder_error": "Ne mogu otvoriti folder:\n{error}",
        "open_selected": "Otvori odabrano",
        "open_web_status": "Otvoren link serije u browseru.",
        "open_search_status": "Otvorena pretraga u browseru.",
        "link_copied": "Link kopiran u clipboard.",
        "folder_opened_manager": "Otvoren folder serije u file manageru.",
        "language_locked_scanning": "Jezik možeš promijeniti nakon što trenutni scan završi.",
        "report_date": "Datum",
        "report_series": "Serija u izvještaju",
        "report_local_files": "Lokalnih video datoteka",
        "report_local_episodes": "Lokalno prepoznatih epizoda",
        "report_expected": "Online očekivanih epizoda",
        "report_total_missing": "Ukupno missing epizoda",
        "report_ok_series": "OK serija",
        "report_missing_series": "Serija s missing epizodama",
        "report_unmatched": "Neuspjelo online matchanje / prazna baza",
        "report_unparsed": "Neprepoznati video fileovi",
        "report_match_query": "Pokušaj upita",
        "report_match_reason": "Razlog matcha",
        "report_local_folder": "Lokalni folder",
        "report_local_file_count": "Lokalnih datoteka",
        "report_episode_summary": "Sažetak epizoda",
        "report_i_have": "imam",
        "report_missing_word": "nedostaje",
        "report_local_have": "lokalno imam",
        "report_online_unavailable": "online očekivano nije dostupno",
        "report_seasons": "Sezone",
        "report_local": "Lokalno",
        "report_expected_word": "Očekivano",
        "report_missing_label": "Nedostaje",
        "report_local_seasons": "Lokalne sezone",
        "report_unparsed_heading": "NEPREPOZNATI VIDEO FILEOVI",
    },
}


def normalize_language(value: str | None) -> str:
    value = (value or "").strip()
    if value in TRANSLATIONS:
        return value
    return LANGUAGE_CODE_BY_LABEL.get(value, DEFAULT_LANGUAGE)


def translate(key: str, language: str = DEFAULT_LANGUAGE, **kwargs) -> str:
    language = normalize_language(language)
    text = TRANSLATIONS.get(language, {}).get(key, TRANSLATIONS[DEFAULT_LANGUAGE].get(key, key))
    if kwargs:
        try:
            return text.format(**kwargs)
        except Exception:
            return text
    return text


def is_all_sources_filter(value: str) -> bool:
    return value in {
        translate("all_sources", "en"),
        translate("all_sources", "hr"),
        "Svi izvori",
    }


@dataclass
class EpisodeInventory:
    show_name: str
    year: int | None = None
    episodes: dict[int, set[int]] = field(default_factory=lambda: defaultdict(set))
    files: list[str] = field(default_factory=list)
    guesses: list[str] = field(default_factory=list)
    year_guesses: list[int] = field(default_factory=list)
    title_candidates: list[dict] = field(default_factory=list)


@dataclass
class ShowResult:
    local_name: str
    local_year: int | None = None
    official_name: str = ""
    official_year: int | None = None
    status: str = "UNMATCHED"
    source: str = ""
    match_score: int = 0
    match_reason: str = ""
    matched_query: str = ""
    source_url: str = ""
    seasons_local: dict[int, list[int]] = field(default_factory=dict)
    seasons_expected: dict[int, list[int]] = field(default_factory=dict)
    missing: dict[int, list[int]] = field(default_factory=dict)
    files: list[str] = field(default_factory=list)

    @property
    def missing_count(self) -> int:
        return sum(len(v) for v in self.missing.values())

    @property
    def season_count(self) -> int:
        return len(self.seasons_expected) if self.seasons_expected else len(self.seasons_local)

    @property
    def browser_url(self) -> str:
        return self.source_url or ""


@dataclass
class ScanSummary:
    root: str = ""
    created_at: str = ""
    ok_count: int = 0
    missing_count: int = 0
    unmatched_count: int = 0
    unparsed_count: int = 0
    results: list[ShowResult] = field(default_factory=list)
    unparsed: list[str] = field(default_factory=list)


@dataclass
class ManualMatchCandidate:
    source: str
    name: str
    year: int | None
    status: str
    missing_count: int
    score: int
    reason: str
    matched_query: str
    source_url: str
    show_json: dict


class TVDBAuthError(RuntimeError):
    pass


@dataclass
class FileOverviewItem:
    status: str
    status_label: str
    episode_label: str
    name: str
    path: str
    season: int | None = None
    episode: int | None = None


@dataclass
class SeriesDeleteTarget:
    kind: str
    paths: list[Path]


class TVMazeClient:
    BASE = "https://api.tvmaze.com"
    HEADERS = {"User-Agent": "TVMissingChecker/4.0"}

    def _get_json(self, url: str):
        req = urllib.request.Request(url, headers=self.HEADERS)
        try:
            with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT_SECONDS) as resp:
                if resp.status != 200:
                    return None
                return json.loads(resp.read().decode("utf-8"))
        except Exception:
            return None

    def search_shows(self, query: str) -> list[dict]:
        params = urllib.parse.urlencode({"q": query})
        data = self._get_json(f"{self.BASE}/search/shows?{params}")
        return data if isinstance(data, list) else []

    def fetch_show_with_episodes_by_id(self, show_id: int) -> dict | None:
        data = self._get_json(f"{self.BASE}/shows/{show_id}?embed=episodes")
        return data if isinstance(data, dict) else None




class IMDbClient:
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    }

    def _get_text(self, url: str) -> str:
        req = urllib.request.Request(url, headers=self.HEADERS)
        try:
            with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT_SECONDS) as resp:
                if resp.status != 200:
                    return ""
                raw = resp.read()
                charset = resp.headers.get_content_charset() or "utf-8"
                return raw.decode(charset, errors="replace")
        except Exception:
            return ""

    def search_shows(self, query: str) -> list[dict]:
        query = (query or "").strip()
        if not query:
            return []

        # Try IMDb search page first.
        url = f"https://www.imdb.com/find/?q={urllib.parse.quote(query)}&s=tt&ttype=tv&ref_=fn_tv"
        html_text = self._get_text(url)
        results = []
        seen = set()

        # Common search result links.
        for imdb_id, title_text, year_text in re.findall(
            r'href="/title/(tt\d+)/[^"]*"[^>]*>(.*?)</a>(?:.*?<span[^>]*>\(?((?:19|20)\d{2})[^<]*</span>)?',
            html_text,
            flags=re.IGNORECASE | re.DOTALL,
        ):
            title = clean_html_text(title_text)
            year = extract_year(year_text or "")
            if imdb_id in seen or not title:
                continue
            seen.add(imdb_id)
            results.append({"id": imdb_id, "title": title, "year": year})
            if len(results) >= 10:
                return results

        # Fallback: suggestion endpoint that often works without auth.
        first = normalize_name(query)[:1] or "x"
        sugg_url = f"https://v2.sg.media-imdb.com/suggestion/{first}/{urllib.parse.quote(query)}.json"
        sugg_text = self._get_text(sugg_url)
        if sugg_text:
            try:
                data = json.loads(sugg_text)
                for row in data.get("d") or []:
                    imdb_id = row.get("id")
                    title = (row.get("l") or "").strip()
                    qtype = (row.get("qid") or row.get("q") or "").lower()
                    if not imdb_id or not title:
                        continue
                    if qtype and "tv" not in qtype and "series" not in qtype and "episode" in qtype:
                        continue
                    if imdb_id in seen:
                        continue
                    seen.add(imdb_id)
                    results.append({"id": imdb_id, "title": title, "year": safe_year(row.get("y"))})
                    if len(results) >= 10:
                        break
            except Exception:
                pass

        return results[:10]

    def fetch_show_with_episodes(self, imdb_id: str) -> dict | None:
        imdb_id = (imdb_id or "").strip()
        if not re.fullmatch(r"tt\d{5,12}", imdb_id):
            return None

        main_url = f"https://www.imdb.com/title/{imdb_id}/episodes/"
        main_html = self._get_text(main_url)
        if not main_html:
            return None

        title = ""
        title_m = re.search(r'<title>(.*?)</title>', main_html, flags=re.IGNORECASE | re.DOTALL)
        if title_m:
            title = clean_html_text(title_m.group(1))
            title = re.sub(r'\s*-\s*Episode list.*$', '', title, flags=re.IGNORECASE).strip()

        year = None
        year_m = re.search(r'(?:TV Series|TV Mini Series|Series)\s*(?:\(|)(\d{4})', main_html, flags=re.IGNORECASE)
        if year_m:
            year = safe_year(year_m.group(1))
        if not year:
            year = extract_year(main_html)

        season_numbers = set(int(n) for n in re.findall(r'episodes/\?season=(\d{1,3})', main_html, flags=re.IGNORECASE))
        if not season_numbers:
            season_numbers = set(int(n) for n in re.findall(r'Season\s*(\d{1,3})', clean_html_text(main_html), flags=re.IGNORECASE))
        if not season_numbers:
            season_numbers = {1}

        seasons = []
        for season_no in sorted(season_numbers):
            season_url = f"https://www.imdb.com/title/{imdb_id}/episodes/?season={season_no}"
            season_html = self._get_text(season_url)
            if not season_html:
                continue
            episodes = parse_imdb_episodes_from_html(season_html, season_no)
            if episodes:
                seasons.append({"season_number": season_no, "episodes": episodes})

        return {
            "id": imdb_id,
            "name": title or "Unknown",
            "first_air_date": f"{year}-01-01" if year else "",
            "url": f"https://www.imdb.com/title/{imdb_id}/episodes/",
            "_season_details": seasons,
        }
class TMDbClient:
    BASE = "https://api.themoviedb.org/3"

    def __init__(self, api_key: str = "", token: str = ""):
        self.api_key = (api_key or "").strip()
        self.token = (token or "").strip()

    @property
    def enabled(self) -> bool:
        return bool(self.api_key or self.token)

    def _request(self, path: str, params: dict | None = None):
        if not self.enabled:
            return None
        params = dict(params or {})
        if self.api_key:
            params["api_key"] = self.api_key
        query = urllib.parse.urlencode(params)
        url = f"{self.BASE}{path}"
        if query:
            url = f"{url}?{query}"
        headers = {"User-Agent": "TVMissingChecker/4.0", "Accept": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT_SECONDS) as resp:
                if resp.status != 200:
                    return None
                return json.loads(resp.read().decode("utf-8"))
        except Exception:
            return None

    def search_tv(self, query: str, year: int | None = None) -> list[dict]:
        params = {"query": query, "include_adult": "false", "language": "en-US"}
        if year:
            params["first_air_date_year"] = year
        data = self._request("/search/tv", params)
        results = data.get("results") if isinstance(data, dict) else None
        return results if isinstance(results, list) else []

    def fetch_tv_with_episodes(self, tmdb_id: int) -> dict | None:
        data = self._request(f"/tv/{tmdb_id}", {"language": "en-US"})
        if not isinstance(data, dict):
            return None
        seasons = []
        for season in data.get("seasons") or []:
            season_no = season.get("season_number")
            if not isinstance(season_no, int) or season_no <= 0:
                continue
            season_detail = self._request(f"/tv/{tmdb_id}/season/{season_no}", {"language": "en-US"})
            if season_detail:
                seasons.append(season_detail)
        data["_season_details"] = seasons
        return data


    def fetch_show_with_episodes(self, query: str, local_eps: dict[int, set[int]] | None = None, year: int | None = None):
        best_show = None
        best_score = -1
        best_reason = "Nema kandidata"

        for candidate in self.search_tv(query, year=year):
            tmdb_id = candidate.get("id")
            if not isinstance(tmdb_id, int):
                continue

            show_json = self.fetch_tv_with_episodes(tmdb_id)
            if not show_json:
                continue

            official_name, official_year, expected_eps, _url = build_expected_map_tmdb(show_json, aired_only=True)
            if not expected_eps:
                continue

            score, reason = score_candidate(
                query,
                year,
                official_name,
                official_year,
                local_eps or {},
                expected_eps,
            )

            if score > best_score:
                best_show = show_json
                best_score = score
                best_reason = reason

        return best_show, best_score, best_reason



class TVDBClient:
    BASE = "https://api4.thetvdb.com/v4"

    def __init__(self, api_key: str = "", token: str = "", token_created_at: str = ""):
        self.api_key = (api_key or "").strip()
        self.token = (token or "").strip()
        self.token_created_at = (token_created_at or "").strip()
        self.auth_message = ""
        self.token_refreshed = False

    @property
    def enabled(self) -> bool:
        return bool(self.api_key or self.token)

    def token_expired(self) -> bool:
        if not self.token or not self.token_created_at:
            return True
        try:
            created = datetime.strptime(self.token_created_at, "%Y-%m-%d %H:%M:%S")
        except Exception:
            return True
        return datetime.now() - created >= timedelta(days=TVDB_TOKEN_TTL_DAYS)

    def _login(self):
        if not self.api_key:
            raise TVDBAuthError("TheTVDB token je istekao, a API key nije unesen.")

        payload = json.dumps({"apikey": self.api_key}).encode("utf-8")
        req = urllib.request.Request(
            f"{self.BASE}/login",
            data=payload,
            headers={
                "User-Agent": "TVMissingChecker/4.0",
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT_SECONDS) as resp:
                if resp.status not in {200, 201}:
                    raise TVDBAuthError("TheTVDB API key je istekao ili nije valjan.")
                data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code in {401, 403}:
                raise TVDBAuthError("TheTVDB API key je istekao ili nije valjan.") from e
            raise

        token = ((data.get("data") or {}).get("token") or "").strip() if isinstance(data, dict) else ""
        if not token:
            raise TVDBAuthError("TheTVDB login nije vratio token.")
        self.token = token
        self.token_created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.token_refreshed = True
        self.auth_message = f"TheTVDB token je osvježen. Lokalno vrijedi {TVDB_TOKEN_TTL_DAYS} dana."

    def ensure_token(self):
        if not self.enabled:
            return
        if self.token_expired():
            self.auth_message = f"TheTVDB token je istekao nakon {TVDB_TOKEN_TTL_DAYS} dana; pokušavam novi login."
            self._login()

    def _request(self, path: str, params: dict | None = None):
        self.ensure_token()
        params = dict(params or {})
        query = urllib.parse.urlencode(params)
        url = f"{self.BASE}{path}"
        if query:
            url = f"{url}?{query}"
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "TVMissingChecker/4.0",
                "Accept": "application/json",
                "Authorization": f"Bearer {self.token}",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT_SECONDS) as resp:
                if resp.status != 200:
                    return None
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code in {401, 403}:
                raise TVDBAuthError("TheTVDB token je istekao ili API key više nije valjan.") from e
            return None
        except Exception:
            return None

    def search_series(self, query: str, year: int | None = None) -> list[dict]:
        if not self.enabled or not query:
            return []
        params = {"query": query, "type": "series", "limit": 10}
        if year:
            params["year"] = year
        data = self._request("/search", params)
        rows = data.get("data") if isinstance(data, dict) else None
        return rows if isinstance(rows, list) else []

    def fetch_series_with_episodes(self, series_id: int) -> dict | None:
        if not self.enabled:
            return None
        base_data = self._request(f"/series/{series_id}/extended", {"short": "true"})
        series = base_data.get("data") if isinstance(base_data, dict) else None
        if not isinstance(series, dict):
            return None

        episodes: list[dict] = []
        for page in range(0, 200):
            page_data = self._request(f"/series/{series_id}/episodes/default", {"page": page})
            data = page_data.get("data") if isinstance(page_data, dict) else None
            if not isinstance(data, dict):
                break
            page_eps = data.get("episodes") or []
            if not page_eps:
                break
            episodes.extend(ep for ep in page_eps if isinstance(ep, dict))

        series["_episodes"] = episodes
        return series




def clean_html_text(value: str) -> str:
    value = html.unescape(value or "")
    value = re.sub(r"<br\s*/?>", " ", value, flags=re.IGNORECASE)
    value = re.sub(r"<[^>]+>", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def parse_imdb_episodes_from_html(page_html: str, season_no: int) -> list[dict]:
    cleaned = clean_html_text(page_html)
    lines = [line.strip() for line in cleaned.split("  ") if line.strip()]
    joined = " ".join(lines)
    episodes = []
    seen = set()

    patterns = [
        rf"S{season_no}\.E(\d{{1,3}})\s*[·\-–:]\s*([^\n]+?)(?=\s+S{season_no}\.E\d{{1,3}}\b|\s+Contribute to this page\b|\s+Back\b|$)",
        rf"S{season_no}\.E(\d{{1,3}})\s+([^\n]+?)(?=\s+S{season_no}\.E\d{{1,3}}\b|\s+Contribute to this page\b|\s+Back\b|$)",
    ]
    for pat in patterns:
        for ep_no_s, title in re.findall(pat, joined, flags=re.IGNORECASE):
            ep_no = int(ep_no_s)
            title = clean_html_text(title)
            title = re.sub(r"\s+(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun),\s+[A-Z][a-z]{2}\s+\d{1,2},\s+\d{4}.*$", "", title)
            title = re.sub(r"\s+Rate.*$", "", title)
            title = re.sub(r"\s+Add a plot.*$", "", title)
            title = re.sub(r"\s+Director.*$", "", title)
            title = re.sub(r"\s+Stars.*$", "", title)
            title = re.sub(r"\s+Episode rated.*$", "", title)
            title = re.sub(r"\s+", " ", title).strip(" -·.:")
            if not title or (season_no, ep_no) in seen:
                continue
            seen.add((season_no, ep_no))
            episodes.append({
                "season": season_no,
                "number": ep_no,
                "name": title,
                "airdate": "",
            })
    episodes.sort(key=lambda x: x["number"])
    return episodes
def safe_year(value) -> int | None:
    try:
        value = int(value)
        if 1900 <= value <= 2100:
            return value
    except Exception:
        pass
    return None


def extract_year(text: str) -> int | None:
    if not text:
        return None
    years = [safe_year(m.group(1)) for m in YEAR_ANYWHERE.finditer(text)]
    years = [y for y in years if y]
    return years[0] if years else None


def infer_season_from_path(file_path: Path, root: Path | None = None) -> int | None:
    parts = []
    try:
        if root is not None:
            parts = list(file_path.relative_to(root).parts[:-1])
    except Exception:
        parts = []
    if not parts:
        parts = list(file_path.parent.parts)

    for raw in reversed(parts):
        if not raw:
            continue
        m = SEASON_FOLDER_RE.search(raw)
        if m:
            try:
                season = int(m.group(1))
                if season > 0:
                    return season
            except Exception:
                pass
        m2 = STANDALONE_SEASON_RE.match(raw.strip())
        if m2:
            try:
                season = int(m2.group(1))
                if season > 0:
                    return season
            except Exception:
                pass
    return None


def looks_like_season_folder(text: str) -> bool:
    text = (text or "").strip()
    return bool(SEASON_FOLDER_RE.search(text) or STANDALONE_SEASON_RE.match(text))


def extract_episode_title_candidate(file_path: Path, root: Path | None = None) -> str:
    title = file_path.stem
    title = YEAR_IN_PARENS.sub(" ", title)
    title = NOISE_TOKENS.sub(" ", title)
    title = EPISODE_TOKEN_CLEANUP_RE.sub(' ', title)

    try:
        guesses, _years = infer_show_guesses(file_path, root or file_path.parent)
    except Exception:
        guesses = []

    variants = [file_path.parent.name]
    variants.extend(guesses[:4])
    for guess in variants:
        if not guess:
            continue
        pattern = re.escape(guess).replace(r'\ ', r'[ ._\-:]+')
        title = re.sub(pattern, ' ', title, flags=re.IGNORECASE)

    title = re.sub(r'^[\W_]+', ' ', title)
    title = re.sub(r'(?i)^(?:episode|ep|chapter|capitulo|capítulo|part)\s+', lambda m: m.group(0).strip() + ' ', title)
    title = re.sub(r'[._]+', ' ', title)
    title = re.sub(r'[-]+', ' ', title)
    title = re.sub(r'\s+', ' ', title).strip(" -._:")
    return title


def is_video(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() in VIDEO_EXTS



def parse_episode_tokens(name: str) -> tuple[int, list[int]] | None:
    for pat in SEASON_EP_PATTERNS:
        m = pat.search(name)
        if not m:
            continue
        season = int(m.group("season"))
        episodes = []
        for key in ("ep1", "ep2", "ep3", "ep4"):
            val = m.groupdict().get(key)
            if val:
                episodes.append(int(val))
        if not episodes:
            continue
        matched_text = m.group(0)
        if (
            len(episodes) == 2
            and episodes[1] > episodes[0] + 1
            and re.search(r'[-\u2013\u2014]\s*E?\d{1,3}\b', matched_text, flags=re.IGNORECASE)
        ):
            episodes = list(range(episodes[0], episodes[1] + 1))
        return season, sorted(set(episodes))
    return None



def clean_show_name(text: str) -> str:
    text = YEAR_IN_PARENS.sub("", text)
    text = NOISE_TOKENS.sub("", text)
    text = EPISODE_TOKEN_CLEANUP_RE.sub('', text)
    text = re.sub(r'\[[^\]]+\]', ' ', text)
    text = re.sub(r'\([^\)]*\)', ' ', text)
    text = re.sub(r'[._]+', ' ', text)
    text = re.sub(r'[-]+', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip(" -._")
    return text.strip()



def normalize_name(text: str) -> str:
    text = clean_show_name(text).lower()
    text = YEAR_ANYWHERE.sub("", text)
    text = re.sub(r'[^a-z0-9 ]+', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text



def token_set(text: str) -> set[str]:
    return {t for t in normalize_name(text).split() if t and t not in STOP_WORDS}



def infer_show_guesses(file_path: Path, root: Path) -> tuple[list[str], list[int]]:
    guesses: list[str] = []
    year_guesses: list[int] = []
    try:
        rel = file_path.relative_to(root)
        parts = rel.parts
    except Exception:
        parts = file_path.parts

    raw_candidates = []
    if len(parts) >= 2:
        if looks_like_season_folder(parts[0]) and root.name:
            raw_candidates.append(root.name)
        else:
            raw_candidates.append(parts[0])
        raw_candidates.append(file_path.parent.name)
    else:
        cleaned_stem = clean_show_name(file_path.stem)
        if cleaned_stem:
            raw_candidates.append(file_path.stem)
        raw_candidates.append(file_path.parent.name)
    raw_candidates.append(file_path.stem)

    for raw in raw_candidates:
        year = extract_year(raw)
        if year:
            year_guesses.append(year)
        cleaned = clean_show_name(raw)
        if cleaned and not re.search(r'(?i)^(?:season|part|book|s)\s*\d+$', cleaned):
            guesses.append(cleaned)
            no_year = YEAR_ANYWHERE.sub("", cleaned).strip()
            if no_year and no_year != cleaned:
                guesses.append(no_year)

    variants: list[str] = []
    for g in guesses:
        variants.append(g)
        alt = re.sub(r'(?i)\b(us|uk)\b', '', g)
        alt = re.sub(r'\s+', ' ', alt).strip()
        if alt and alt != g:
            variants.append(alt)

    unique = []
    seen = set()
    for v in variants:
        key = normalize_name(v)
        if key and key not in seen:
            seen.add(key)
            unique.append(v)

    years_unique = []
    seen_years = set()
    for year in year_guesses:
        if year and year not in seen_years:
            seen_years.add(year)
            years_unique.append(year)

    return unique or ["Unknown Show"], years_unique



def extract_year_from_text(text: str) -> int | None:
    years = [int(m.group(0)) for m in YEAR_ANYWHERE.finditer(text or "")]
    for y in years:
        if 1900 <= y <= 2100:
            return y
    return None


def infer_year_from_files(paths: list[str]) -> int | None:
    for path in paths:
        year = extract_year_from_text(path)
        if year:
            return year
    return None


def scan_library(root: Path) -> tuple[dict[str, EpisodeInventory], list[str]]:
    shows: dict[str, EpisodeInventory] = {}
    unparsed: list[str] = []

    for path in root.rglob("*"):
        if not is_video(path):
            continue

        guesses, years = infer_show_guesses(path, root)
        key = guesses[0]
        inv = shows.setdefault(key, EpisodeInventory(show_name=key, year=years[0] if years else None))
        inv.files.append(str(path))
        for g in guesses:
            if g not in inv.guesses:
                inv.guesses.append(g)
        for y in years:
            if y not in inv.year_guesses:
                inv.year_guesses.append(y)
        if inv.year is None and inv.year_guesses:
            inv.year = inv.year_guesses[0]

        parsed = parse_episode_tokens(path.name)
        if parsed:
            season, episodes = parsed
        else:
            season_hint = infer_season_from_path(path, root)
            title_hint = extract_episode_title_candidate(path, root)
            if season_hint and title_hint:
                inv.title_candidates.append({"path": str(path), "title": title_hint, "season_hint": season_hint})
            elif title_hint:
                inv.title_candidates.append({"path": str(path), "title": title_hint, "season_hint": None})
            unparsed.append(str(path))
            continue

        if season <= 0:
            continue
        for ep in episodes:
            inv.episodes[season].add(ep)

    return shows, sorted(unparsed)



def build_expected_map_tvmaze(show_json: dict, aired_only: bool = True) -> tuple[str, int | None, dict[int, set[int]], str]:
    show_name = show_json.get("name") or "Unknown"
    premiered = show_json.get("premiered") or ""
    show_year = extract_year(premiered)
    eps = (show_json.get("_embedded") or {}).get("episodes") or []
    expected: dict[int, set[int]] = defaultdict(set)
    today = date.today()

    for ep in eps:
        season = ep.get("season")
        number = ep.get("number")
        airdate = ep.get("airdate")
        if not isinstance(season, int) or not isinstance(number, int) or season <= 0:
            continue
        if aired_only and airdate:
            try:
                d = datetime.strptime(airdate, "%Y-%m-%d").date()
                if d > today:
                    continue
            except Exception:
                pass
        expected[season].add(number)
    return show_name, show_year, expected, show_json.get("url") or ""



def build_expected_map_tmdb(show_json: dict, aired_only: bool = True) -> tuple[str, int | None, dict[int, set[int]], str]:
    show_name = show_json.get("name") or show_json.get("original_name") or "Unknown"
    show_year = extract_year(show_json.get("first_air_date") or "")
    expected: dict[int, set[int]] = defaultdict(set)
    today = date.today()

    for season_detail in show_json.get("_season_details") or []:
        season = season_detail.get("season_number")
        if not isinstance(season, int) or season <= 0:
            continue
        for ep in season_detail.get("episodes") or []:
            number = ep.get("episode_number")
            airdate = ep.get("air_date")
            if not isinstance(number, int):
                continue
            if aired_only and airdate:
                try:
                    d = datetime.strptime(airdate, "%Y-%m-%d").date()
                    if d > today:
                        continue
                except Exception:
                    pass
            expected[season].add(number)
    source_url = ""
    if show_json.get("id"):
        source_url = f"https://www.themoviedb.org/tv/{show_json['id']}"
    return show_name, show_year, expected, source_url


def build_expected_map_imdb(show_json: dict, aired_only: bool = True) -> tuple[str, int | None, dict[int, set[int]], str]:
    show_name = show_json.get("name") or "Unknown"
    show_year = extract_year(show_json.get("first_air_date") or "")
    expected: dict[int, set[int]] = defaultdict(set)
    today = date.today()

    for season_detail in show_json.get("_season_details") or []:
        season = season_detail.get("season_number")
        if not isinstance(season, int) or season <= 0:
            continue
        for ep in season_detail.get("episodes") or []:
            number = ep.get("number")
            airdate = ep.get("airdate") or ep.get("air_date")
            if not isinstance(number, int):
                continue
            if aired_only and airdate:
                try:
                    d = datetime.strptime(airdate, "%Y-%m-%d").date()
                    if d > today:
                        continue
                except Exception:
                    pass
            expected[season].add(number)

    source_url = show_json.get("url") or ""
    imdb_id = str(show_json.get("id") or "")
    if not source_url and re.fullmatch(r"tt\d{5,12}", imdb_id):
        source_url = f"https://www.imdb.com/title/{imdb_id}/episodes/"
    return show_name, show_year, expected, source_url



def build_expected_map_tvdb(show_json: dict, aired_only: bool = True) -> tuple[str, int | None, dict[int, set[int]], str]:
    show_name = show_json.get("name") or "Unknown"
    show_year = safe_year(show_json.get("year")) or extract_year(show_json.get("firstAired") or "")
    expected: dict[int, set[int]] = defaultdict(set)
    today = date.today()

    for ep in show_json.get("_episodes") or show_json.get("episodes") or []:
        season = ep.get("seasonNumber")
        number = ep.get("number")
        airdate = ep.get("aired") or ""
        if not isinstance(season, int) or not isinstance(number, int) or season <= 0:
            continue
        if aired_only and airdate:
            try:
                d = datetime.strptime(airdate[:10], "%Y-%m-%d").date()
                if d > today:
                    continue
            except Exception:
                pass
        expected[season].add(number)

    source_url = ""
    tvdb_id = show_json.get("id")
    slug = show_json.get("slug")
    if slug:
        source_url = f"https://thetvdb.com/series/{slug}"
    elif tvdb_id:
        source_url = f"https://thetvdb.com/dereferrer/series/{tvdb_id}"
    return show_name, show_year, expected, source_url


def build_expected_map(show_json: dict, source: str, aired_only: bool = True) -> tuple[str, int | None, dict[int, set[int]], str]:
    if source == "TMDb":
        return build_expected_map_tmdb(show_json, aired_only=aired_only)
    if source == "IMDb":
        return build_expected_map_imdb(show_json, aired_only=aired_only)
    if source == "TVDB":
        return build_expected_map_tvdb(show_json, aired_only=aired_only)
    return build_expected_map_tvmaze(show_json, aired_only=aired_only)


def build_episode_title_map(show_json: dict, source: str, aired_only: bool = True) -> dict[int, dict[int, str]]:
    today = date.today()
    result: dict[int, dict[int, str]] = defaultdict(dict)

    if source in {"TMDb", "IMDb"}:
        for season_detail in show_json.get("_season_details") or []:
            season = season_detail.get("season_number")
            if not isinstance(season, int) or season <= 0:
                continue
            for ep in season_detail.get("episodes") or []:
                number = ep.get("episode_number")
                if not isinstance(number, int):
                    number = ep.get("number")
                title = (ep.get("name") or "").strip()
                airdate = ep.get("air_date") or ep.get("airdate")
                if not isinstance(number, int) or not title:
                    continue
                if aired_only and airdate:
                    try:
                        d = datetime.strptime(airdate, "%Y-%m-%d").date()
                        if d > today:
                            continue
                    except Exception:
                        pass
                result[season][number] = title
        return dict(result)

    if source == "TVDB":
        for ep in show_json.get("_episodes") or show_json.get("episodes") or []:
            season = ep.get("seasonNumber")
            number = ep.get("number")
            title = (ep.get("name") or "").strip()
            airdate = ep.get("aired") or ""
            if not isinstance(season, int) or not isinstance(number, int) or season <= 0 or not title:
                continue
            if aired_only and airdate:
                try:
                    d = datetime.strptime(airdate[:10], "%Y-%m-%d").date()
                    if d > today:
                        continue
                except Exception:
                    pass
            result[season][number] = title
        return dict(result)

    for ep in (show_json.get("_embedded") or {}).get("episodes") or []:
        season = ep.get("season")
        number = ep.get("number")
        title = (ep.get("name") or "").strip()
        airdate = ep.get("airdate")
        if not isinstance(season, int) or not isinstance(number, int) or season <= 0 or not title:
            continue
        if aired_only and airdate:
            try:
                d = datetime.strptime(airdate, "%Y-%m-%d").date()
                if d > today:
                    continue
            except Exception:
                pass
        result[season][number] = title
    return dict(result)


def match_title_candidates(local_eps: dict[int, set[int]], title_candidates: list[dict], expected_title_map: dict[int, dict[int, str]]) -> dict[int, set[int]]:
    merged = defaultdict(set, {season: set(eps) for season, eps in local_eps.items()})
    if not title_candidates or not expected_title_map:
        return merged

    # build normalized title index
    official_entries = []
    for season, ep_map in expected_title_map.items():
        for ep_no, title in ep_map.items():
            norm = normalize_name(title)
            tokens = token_set(title)
            if norm:
                official_entries.append((season, ep_no, title, norm, tokens))

    used = set((s, e) for s, eps in merged.items() for e in eps)

    for cand in title_candidates:
        cand_title = (cand.get("title") or "").strip()
        if not cand_title:
            continue
        cand_norm = normalize_name(cand_title)
        if not cand_norm:
            continue
        cand_tokens = token_set(cand_title)
        season_hint = cand.get("season_hint")

        best = None
        best_score = 0.0
        for season, ep_no, title, norm, tokens in official_entries:
            if (season, ep_no) in used:
                continue
            if season_hint and season != season_hint:
                continue

            score = 0.0
            if cand_norm == norm:
                score = 1.0
            elif cand_norm in norm or norm in cand_norm:
                score = 0.96
            else:
                overlap = len(cand_tokens & tokens)
                union = max(len(cand_tokens | tokens), 1)
                token_ratio = overlap / union
                seq = SequenceMatcher(None, cand_norm, norm).ratio()
                if overlap >= 2 and seq >= 0.86:
                    score = 0.65 * seq + 0.35 * token_ratio

            if score > best_score:
                best_score = score
                best = (season, ep_no)

        if best and best_score >= 0.90:
            merged[best[0]].add(best[1])
            used.add(best)

    return merged


def find_missing(local_eps: dict[int, set[int]], expected_eps: dict[int, set[int]]) -> dict[int, list[int]]:
    missing: dict[int, list[int]] = {}
    for season in sorted(expected_eps):
        diff = sorted(expected_eps.get(season, set()) - local_eps.get(season, set()))
        if diff:
            missing[season] = diff
    return missing



def format_ep_ranges(ep_numbers: list[int]) -> str:
    if not ep_numbers:
        return "-"
    ranges = []
    start = prev = ep_numbers[0]
    for n in ep_numbers[1:]:
        if n == prev + 1:
            prev = n
            continue
        ranges.append((start, prev))
        start = prev = n
    ranges.append((start, prev))
    out = []
    for a, b in ranges:
        out.append(f"E{a:02d}" if a == b else f"E{a:02d}-E{b:02d}")
    return ", ".join(out)



def summarize_missing(missing: dict[int, list[int]]) -> str:
    if not missing:
        return "OK"
    chunks = []
    for season, eps in sorted(missing.items()):
        chunks.append(f"S{season:02d} ({len(eps)}): {format_ep_ranges(eps)}")
    return " | ".join(chunks)


def count_episode_map(episodes_by_season: dict[int, list[int]]) -> int:
    return sum(len(episodes) for episodes in episodes_by_season.values())


def format_report_episode_list(episodes: list[int]) -> str:
    return format_ep_ranges(sorted(episodes)) if episodes else "-"


def summarize_local_folder(files: list[str]) -> str:
    if not files:
        return ""
    try:
        parents = [str(Path(path).expanduser().parent) for path in files if path]
        if not parents:
            return ""
        if len(set(parents)) == 1:
            return parents[0]
        return os.path.commonpath(parents)
    except Exception:
        try:
            return str(Path(files[0]).expanduser().parent)
        except Exception:
            return ""


def mark_result_as_manually_ok(result: ShowResult):
    result.status = "OK"
    result.missing = {}
    result.match_reason = "Ručno označeno kao OK."


def path_is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def normalized_abs_path(path: str | Path) -> Path:
    return Path(path).expanduser().resolve(strict=False)


def unique_paths(paths: list[Path]) -> list[Path]:
    result = []
    seen = set()
    for path in paths:
        key = str(path)
        if key in seen:
            continue
        seen.add(key)
        result.append(path)
    return result


def resolve_series_delete_target(result: ShowResult, scan_root: str | Path | None = None,
                                 total_results: int = 1) -> SeriesDeleteTarget | None:
    paths = unique_paths([normalized_abs_path(path) for path in result.files if path])
    paths = [path for path in paths if path.exists()]
    if not paths:
        return None

    root = normalized_abs_path(scan_root) if scan_root else None
    if root and all(path_is_relative_to(path, root) for path in paths):
        rels = [path.relative_to(root) for path in paths]

        if total_results <= 1 and normalize_name(root.name) == normalize_name(result.local_name):
            return SeriesDeleteTarget(kind="folder", paths=[root])

        top_parts = {rel.parts[0] for rel in rels if len(rel.parts) >= 2}
        direct_files = [rel for rel in rels if len(rel.parts) == 1]
        if len(top_parts) == 1 and not direct_files:
            top_folder = root / next(iter(top_parts))
            if top_folder.exists() and top_folder.is_dir() and not looks_like_season_folder(top_folder.name):
                return SeriesDeleteTarget(kind="folder", paths=[top_folder])

    parents = {path.parent for path in paths}
    if len(parents) == 1:
        folder = next(iter(parents))
        if (not root or folder != root) and not looks_like_season_folder(folder.name):
            return SeriesDeleteTarget(kind="folder", paths=[folder])

    return SeriesDeleteTarget(kind="files", paths=paths)


def build_file_overview_items(result: ShowResult, language: str = DEFAULT_LANGUAGE) -> list[FileOverviewItem]:
    items: list[FileOverviewItem] = []

    for path_text in sorted(result.files, key=lambda p: str(p).lower()):
        path = Path(path_text)
        parsed = parse_episode_tokens(path.name)
        if parsed:
            season, episodes = parsed
            episode_label = f"S{season:02d}: {format_ep_ranges(episodes)}"
            first_ep = min(episodes) if episodes else None
            items.append(FileOverviewItem(
                status="HAVE",
                status_label=translate("file_status_have", language),
                episode_label=episode_label,
                name=path.name,
                path=path_text,
                season=season,
                episode=first_ep,
            ))
            continue

        season_hint = infer_season_from_path(path)
        items.append(FileOverviewItem(
            status="UNKNOWN",
            status_label=translate("file_status_unknown", language),
            episode_label=f"S{season_hint:02d}: ?" if season_hint else "-",
            name=path.name,
            path=path_text,
            season=season_hint,
            episode=None,
        ))

    for season, episodes in sorted(result.missing.items()):
        for episode in sorted(episodes):
            episode_label = f"S{season:02d}E{episode:02d}"
            items.append(FileOverviewItem(
                status="MISSING",
                status_label=translate("file_status_missing", language),
                episode_label=episode_label,
                name=f"{result.local_name} {episode_label}",
                path="",
                season=season,
                episode=episode,
            ))

    status_order = {"HAVE": 0, "MISSING": 1, "UNKNOWN": 2}
    items.sort(key=lambda item: (
        item.season if item.season is not None else 9999,
        item.episode if item.episode is not None else 9999,
        status_order.get(item.status, 9),
        item.name.lower(),
    ))
    return items


def open_path_in_file_manager(path: str | Path):
    target = Path(path)
    folder = target if target.is_dir() else target.parent

    if sys.platform.startswith("win"):
        if target.is_file():
            subprocess.Popen(["explorer", f"/select,{target}"])
        else:
            subprocess.Popen(["explorer", str(folder)])
        return

    if sys.platform == "darwin":
        if target.is_file():
            subprocess.Popen(["open", "-R", str(target)])
        else:
            subprocess.Popen(["open", str(folder)])
        return

    commands = [
        ("xdg-open", [str(folder)]),
        ("gio", ["open", str(folder)]),
        ("kde-open5", [str(folder)]),
        ("kde-open", [str(folder)]),
        ("kioclient5", ["exec", str(folder)]),
        ("kioclient", ["exec", str(folder)]),
    ]
    for command, args in commands:
        exe = shutil.which(command)
        if exe:
            subprocess.Popen([exe, *args])
            return

    raise RuntimeError("Nije pronađen file manager command za Linux (xdg-open/gio/kde-open).")



def format_local_year(local_year: int | None) -> str:
    return f" ({local_year})" if local_year else ""



def score_candidate(local_name: str, local_year: int | None, candidate_name: str, candidate_year: int | None,
                    local_eps: dict[int, set[int]], expected_eps: dict[int, set[int]]) -> tuple[int, str]:
    local_norm = normalize_name(local_name)
    cand_norm = normalize_name(candidate_name)
    seq_ratio = SequenceMatcher(None, local_norm, cand_norm).ratio()
    local_tokens = token_set(local_name)
    cand_tokens = token_set(candidate_name)
    overlap = len(local_tokens & cand_tokens)
    union = max(len(local_tokens | cand_tokens), 1)
    token_ratio = overlap / union
    local_seasons = set(local_eps)
    expected_seasons = set(expected_eps)
    season_ratio = len(local_seasons & expected_seasons) / max(len(local_seasons), 1)

    year_points = 0
    year_cap = 100
    year_reason = "godina=n/a"
    if local_year and candidate_year:
        diff = abs(local_year - candidate_year)
        if diff == 0:
            year_points = 20
            year_reason = f"godina={local_year}/{candidate_year} exact"
        elif diff == 1:
            year_points = 12
            year_cap = 92
            year_reason = f"godina={local_year}/{candidate_year} +/-1"
        elif diff == 2:
            year_points = 4
            year_cap = 72
            year_reason = f"godina={local_year}/{candidate_year} +/-2"
        else:
            year_points = -30
            year_cap = 40
            year_reason = f"godina={local_year}/{candidate_year} mismatch"
    elif local_year and not candidate_year:
        year_points = -5
        year_cap = 78
        year_reason = f"godina={local_year}/?"

    score = int(seq_ratio * 40 + token_ratio * 25 + season_ratio * 15 + year_points)
    score = max(0, min(year_cap, score))
    reason = f"ime={seq_ratio:.2f}, tokeni={token_ratio:.2f}, sezone={season_ratio:.2f}, {year_reason}"
    return score, reason


def build_text_search_queries(guess: str, years: list[int]) -> list[str]:
    queries = []
    for year in years[:2]:
        if str(year) not in guess:
            queries.append(f"{guess} {year}")
    queries.append(guess)
    unique = []
    seen = set()
    for query in queries:
        key = query.strip().lower()
        if key and key not in seen:
            seen.add(key)
            unique.append(query.strip())
    return unique



def choose_best_show_match(tvmaze: TVMazeClient, tmdb: TMDbClient, tvdb: TVDBClient, imdb: IMDbClient, inv: EpisodeInventory,
                           aired_only: bool = True) -> tuple[dict | None, str, int, str, str]:
    years = inv.year_guesses[:2] if inv.year_guesses else ([inv.year] if inv.year else [])
    local_year = inv.year or (years[0] if years else None)
    threshold = 42 if tmdb.enabled else 46
    fast_accept_threshold = 82 if years else 72

    best_show = None
    best_query = ""
    best_score = -1
    best_reason = ""
    best_source = ""
    seen: set[tuple[str, str]] = set()

    def best_tuple():
        return best_show, best_query, best_score, best_reason, best_source

    def consider(show: dict, query: str, source: str):
        nonlocal best_show, best_query, best_score, best_reason, best_source
        official_name, official_year, expected, _source_url = build_expected_map(show, source, aired_only=aired_only)
        if not expected and source == "TMDb":
            return
        score, reason = score_candidate(inv.show_name, local_year, official_name, official_year, inv.episodes, expected)
        if score > best_score:
            best_show = show
            best_query = query
            best_score = score
            best_reason = reason
            best_source = source

    for guess in inv.guesses[:MAX_GUESSES_PER_SHOW]:
        for text_query in build_text_search_queries(guess, years):
            for row in tvmaze.search_shows(text_query)[:MAX_TVMAZE_CANDIDATES]:
                show = row.get("show") or {}
                show_id = show.get("id")
                if not show_id:
                    continue
                key = ("TVMaze", str(int(show_id)))
                if key in seen:
                    continue
                seen.add(key)
                detailed = tvmaze.fetch_show_with_episodes_by_id(int(show_id))
                if detailed:
                    consider(detailed, text_query, "TVMaze")
                    if best_score >= fast_accept_threshold:
                        return best_tuple()

        if tmdb.enabled:
            search_years = years or [None]
            for year in search_years:
                for show in tmdb.search_tv(guess, year=year)[:MAX_TMDB_CANDIDATES]:
                    show_id = show.get("id")
                    if not show_id:
                        continue
                    key = ("TMDb", str(int(show_id)))
                    if key in seen:
                        continue
                    seen.add(key)
                    detailed = tmdb.fetch_tv_with_episodes(int(show_id))
                    if detailed:
                        consider(detailed, guess, "TMDb")
                        if best_score >= fast_accept_threshold:
                            return best_tuple()

        if tvdb.enabled:
            search_years = years or [None]
            for year in search_years:
                for show in tvdb.search_series(guess, year=year)[:MAX_TVDB_CANDIDATES]:
                    raw_id = show.get("tvdb_id") or show.get("id")
                    try:
                        show_id = int(raw_id)
                    except Exception:
                        continue
                    key = ("TVDB", str(show_id))
                    if key in seen:
                        continue
                    seen.add(key)
                    detailed = tvdb.fetch_series_with_episodes(show_id)
                    if detailed:
                        consider(detailed, guess, "TVDB")
                        if best_score >= fast_accept_threshold:
                            return best_tuple()

    if best_score >= fast_accept_threshold:
        return best_tuple()

    for guess in inv.guesses[:MAX_GUESSES_PER_SHOW]:
        for text_query in build_text_search_queries(guess, years):
            for row in imdb.search_shows(text_query)[:MAX_IMDB_CANDIDATES]:
                imdb_id = row.get("id")
                if not imdb_id:
                    continue
                key = ("IMDb", str(imdb_id))
                if key in seen:
                    continue
                seen.add(key)
                detailed = imdb.fetch_show_with_episodes(str(imdb_id))
                if detailed:
                    consider(detailed, text_query, "IMDb")
                    if best_score >= fast_accept_threshold:
                        return best_tuple()

    if best_score < threshold:
        return None, best_query, best_score, best_reason, best_source
    return best_tuple()



def make_show_result(inv: EpisodeInventory, show_json: dict | None, source: str, aired_only: bool,
                     matched_query: str = "", match_score: int = 0, match_reason: str = "") -> ShowResult:
    base_local_eps = {season: set(eps) for season, eps in inv.episodes.items()}
    local_seasons = {k: sorted(v) for k, v in sorted(base_local_eps.items())}
    if not show_json:
        return ShowResult(
            local_name=inv.show_name,
            local_year=inv.year,
            status="UNMATCHED",
            source=source,
            match_score=max(match_score, 0),
            match_reason=match_reason or "Nije pronađen dovoljno dobar kandidat",
            matched_query=matched_query,
            seasons_local=local_seasons,
            files=inv.files,
        )

    official_name, official_year, expected, source_url = build_expected_map(show_json, source, aired_only=aired_only)
    expected_title_map = build_episode_title_map(show_json, source, aired_only=aired_only)
    merged_local_eps = match_title_candidates(base_local_eps, inv.title_candidates, expected_title_map)
    local_seasons = {k: sorted(v) for k, v in sorted(merged_local_eps.items())}
    expected_sorted = {k: sorted(v) for k, v in sorted(expected.items())}
    missing = find_missing(merged_local_eps, expected)

    if not expected:
        status = "EMPTY_DB"
    elif missing:
        status = "MISSING"
    else:
        status = "OK"

    return ShowResult(
        local_name=inv.show_name,
        local_year=inv.year,
        official_name=official_name,
        official_year=official_year,
        status=status,
        source=source,
        match_score=max(match_score, 0),
        match_reason=match_reason,
        matched_query=matched_query,
        source_url=source_url,
        seasons_local=local_seasons,
        seasons_expected=expected_sorted,
        missing=missing,
        files=inv.files,
    )



def create_report(summary: ScanSummary, include_ok: bool = True, include_unparsed: bool = True,
                  language: str = DEFAULT_LANGUAGE) -> str:
    def tr(key: str, **kwargs) -> str:
        return translate(key, language, **kwargs)

    report_items = [item for item in summary.results if include_ok or item.status != "OK"]
    total_results = len(report_items)
    total_local_episodes = sum(count_episode_map(item.seasons_local) for item in report_items)
    total_expected_episodes = sum(count_episode_map(item.seasons_expected) for item in report_items)
    total_missing_episodes = sum(item.missing_count for item in report_items)
    total_files = sum(len(item.files) for item in report_items)

    lines = [
        f"Scan root: {summary.root}",
        f"{tr('report_date')}: {summary.created_at}",
        "",
        f"{tr('report_series')}: {total_results}",
        f"{tr('report_local_files')}: {total_files}",
        f"{tr('report_local_episodes')}: {total_local_episodes}",
        f"{tr('report_expected')}: {total_expected_episodes}",
        f"{tr('report_total_missing')}: {total_missing_episodes}",
        "",
        f"{tr('report_ok_series')}: {summary.ok_count}",
        f"{tr('report_missing_series')}: {summary.missing_count}",
        f"{tr('report_unmatched')}: {summary.unmatched_count}",
        f"{tr('report_unparsed')}: {summary.unparsed_count}",
        "",
    ]

    for item in report_items:
        lines.append(f"=== {item.local_name}{format_local_year(item.local_year)} ===")
        lines.append(f"Status: {item.status}")
        if item.official_name:
            title = item.official_name + (f" ({item.official_year})" if item.official_year else "")
            lines.append(f"Matched as: {title}")
        if item.source:
            lines.append(f"{tr('source')}: {item.source}")
        if item.matched_query:
            lines.append(f"{tr('report_match_query')}: {item.matched_query}")
        if item.match_score or item.match_reason:
            lines.append(f"Match score: {item.match_score}")
        if item.match_reason:
            lines.append(f"{tr('report_match_reason')}: {item.match_reason}")
        if item.source_url:
            lines.append(f"Link: {item.source_url}")

        local_count = count_episode_map(item.seasons_local)
        expected_count = count_episode_map(item.seasons_expected)
        folder = summarize_local_folder(item.files)
        if folder:
            lines.append(f"{tr('report_local_folder')}: {folder}")
        lines.append(f"{tr('report_local_file_count')}: {len(item.files)}")
        if item.seasons_expected:
            lines.append(
                f"{tr('report_episode_summary')}: {tr('report_i_have')} "
                f"{local_count}/{expected_count} | {tr('report_missing_word')} {item.missing_count}"
            )
        else:
            lines.append(
                f"{tr('report_episode_summary')}: {tr('report_local_have')} "
                f"{local_count} | {tr('report_online_unavailable')}"
            )

        if item.seasons_expected:
            lines.append(f"{tr('report_seasons')}:")
            for season in sorted(item.seasons_expected):
                local_eps = item.seasons_local.get(season, [])
                expected_eps = item.seasons_expected.get(season, [])
                missing_eps = item.missing.get(season, [])
                have = len(local_eps)
                total = len(expected_eps)
                lines.append(f"  Season {season:02d}:")
                lines.append(f"    {tr('report_local')}: {have} {tr('episodes')} ({format_report_episode_list(local_eps)})")
                lines.append(f"    {tr('report_expected_word')}: {total} {tr('episodes')} ({format_report_episode_list(expected_eps)})")
                if season in item.missing:
                    lines.append(f"    {tr('report_missing_label')}: {format_ep_ranges(missing_eps)}")
                else:
                    lines.append(f"    {tr('report_missing_label')}: {tr('missing_none')}")
        else:
            lines.append(f"{tr('report_local_seasons')}:")
            for season in sorted(item.seasons_local):
                local_eps = item.seasons_local[season]
                lines.append(f"  Season {season:02d}: {len(local_eps)} {tr('episodes')} ({format_report_episode_list(local_eps)})")
        lines.append("")

    if include_unparsed and summary.unparsed:
        lines.append(f"=== {tr('report_unparsed_heading')} ===")
        lines.extend(summary.unparsed)
        lines.append("")
    return "\n".join(lines)


def check_show_online(inv: EpisodeInventory, tmdb_api_key: str, tmdb_token: str, tvdb_api_key: str,
                      tvdb_token: str, tvdb_token_created_at: str, aired_only: bool) -> ShowResult:
    tvmaze = TVMazeClient()
    tmdb = TMDbClient(tmdb_api_key, tmdb_token)
    tvdb = TVDBClient(tvdb_api_key, tvdb_token, tvdb_token_created_at)
    imdb = IMDbClient()
    best_show, matched_query, score, reason, source = choose_best_show_match(tvmaze, tmdb, tvdb, imdb, inv, aired_only=aired_only)
    return make_show_result(inv, best_show, source, aired_only, matched_query, score, reason)


def inventory_from_result(item: ShowResult) -> EpisodeInventory:
    inv = EpisodeInventory(show_name=item.local_name, year=item.local_year or infer_year_from_files(item.files))
    inv.files = list(item.files)
    inv.episodes = defaultdict(set, {int(season): set(eps) for season, eps in item.seasons_local.items()})
    inv.guesses = [item.local_name]
    if item.official_name and item.official_name != item.local_name:
        inv.guesses.append(item.official_name)
    if inv.year:
        inv.year_guesses = [inv.year]
    return inv


def make_manual_candidate(inv: EpisodeInventory, show_json: dict, source: str, matched_query: str,
                          aired_only: bool) -> ManualMatchCandidate | None:
    official_name, official_year, expected, source_url = build_expected_map(show_json, source, aired_only=aired_only)
    if not official_name:
        return None
    local_year = inv.year or (inv.year_guesses[0] if inv.year_guesses else None)
    score, reason = score_candidate(inv.show_name, local_year, official_name, official_year, inv.episodes, expected)
    preview = make_show_result(
        inv,
        show_json,
        source,
        aired_only=aired_only,
        matched_query=matched_query,
        match_score=score,
        match_reason=reason,
    )
    return ManualMatchCandidate(
        source=source,
        name=official_name,
        year=official_year,
        status=preview.status,
        missing_count=preview.missing_count,
        score=score,
        reason=reason,
        matched_query=matched_query,
        source_url=source_url,
        show_json=show_json,
    )


def extract_manual_ids(query: str, source: str) -> list[str]:
    query = (query or "").strip()
    if not query:
        return []
    if source == "IMDb":
        return list(dict.fromkeys(re.findall(r"tt\d{5,12}", query, flags=re.IGNORECASE)))
    if source == "TVMaze":
        ids = re.findall(r"tvmaze\.com/shows/(\d+)", query, flags=re.IGNORECASE)
        if query.isdigit():
            ids.append(query)
        return list(dict.fromkeys(ids))
    if source == "TMDb":
        ids = re.findall(r"themoviedb\.org/tv/(\d+)", query, flags=re.IGNORECASE)
        if query.isdigit():
            ids.append(query)
        return list(dict.fromkeys(ids))
    if source == "TVDB":
        ids = re.findall(r"thetvdb\.com/(?:series/[^/\s]+|dereferrer/series)/(\d+)", query, flags=re.IGNORECASE)
        ids.extend(re.findall(r"thetvdb\.com/dereferrer/series/(\d+)", query, flags=re.IGNORECASE))
        if query.isdigit():
            ids.append(query)
        return list(dict.fromkeys(ids))
    return []


def search_manual_candidates(inv: EpisodeInventory, query: str, source_filter: str, tmdb_api_key: str,
                             tmdb_token: str, tvdb_api_key: str, tvdb_token: str,
                             tvdb_token_created_at: str, aired_only: bool) -> list[ManualMatchCandidate]:
    query = (query or "").strip()
    if not query:
        return []

    candidates: list[ManualMatchCandidate] = []
    seen: set[tuple[str, str]] = set()
    sources = ["TVMaze", "TMDb", "TVDB", "IMDb"] if is_all_sources_filter(source_filter) else [source_filter]

    def add(show_json: dict | None, source: str, matched_query: str, key_value: str):
        if not show_json:
            return
        key = (source, str(key_value))
        if key in seen:
            return
        seen.add(key)
        candidate = make_manual_candidate(inv, show_json, source, matched_query, aired_only)
        if candidate:
            candidates.append(candidate)

    if "TVMaze" in sources:
        tvmaze = TVMazeClient()
        for tvmaze_id in extract_manual_ids(query, "TVMaze"):
            add(tvmaze.fetch_show_with_episodes_by_id(int(tvmaze_id)), "TVMaze", query, tvmaze_id)
        years = inv.year_guesses[:2] or ([inv.year] if inv.year else [])
        for text_query in build_text_search_queries(query, years):
            for row in tvmaze.search_shows(text_query)[:10]:
                show = row.get("show") or {}
                show_id = show.get("id")
                if show_id:
                    add(tvmaze.fetch_show_with_episodes_by_id(int(show_id)), "TVMaze", text_query, str(show_id))

    if "TMDb" in sources:
        tmdb = TMDbClient(tmdb_api_key, tmdb_token)
        if tmdb.enabled:
            for tmdb_id in extract_manual_ids(query, "TMDb"):
                add(tmdb.fetch_tv_with_episodes(int(tmdb_id)), "TMDb", query, tmdb_id)
            search_years = inv.year_guesses[:2] or ([inv.year] if inv.year else [None])
            for year in search_years:
                for show in tmdb.search_tv(query, year=year)[:8]:
                    show_id = show.get("id")
                    if show_id:
                        add(tmdb.fetch_tv_with_episodes(int(show_id)), "TMDb", query, str(show_id))

    if "TVDB" in sources:
        tvdb = TVDBClient(tvdb_api_key, tvdb_token, tvdb_token_created_at)
        if tvdb.enabled:
            for tvdb_id in extract_manual_ids(query, "TVDB"):
                add(tvdb.fetch_series_with_episodes(int(tvdb_id)), "TVDB", query, tvdb_id)
            search_years = inv.year_guesses[:2] or ([inv.year] if inv.year else [None])
            for year in search_years:
                for show in tvdb.search_series(query, year=year)[:8]:
                    raw_id = show.get("tvdb_id") or show.get("id")
                    try:
                        show_id = int(raw_id)
                    except Exception:
                        continue
                    add(tvdb.fetch_series_with_episodes(show_id), "TVDB", query, str(show_id))

    if "IMDb" in sources:
        imdb = IMDbClient()
        for imdb_id in extract_manual_ids(query, "IMDb"):
            add(imdb.fetch_show_with_episodes(imdb_id), "IMDb", query, imdb_id)
        years = inv.year_guesses[:2] or ([inv.year] if inv.year else [])
        for text_query in build_text_search_queries(query, years):
            for row in imdb.search_shows(text_query)[:8]:
                imdb_id = row.get("id")
                if imdb_id:
                    add(imdb.fetch_show_with_episodes(str(imdb_id)), "IMDb", text_query, str(imdb_id))

    status_rank = {"OK": 0, "MISSING": 1, "EMPTY_DB": 2, "UNMATCHED": 3}
    candidates.sort(key=lambda c: (-c.score, status_rank.get(c.status, 9), c.missing_count, c.name.lower()))
    return candidates



def load_config() -> dict:
    if not CONFIG_PATH.exists():
        return {}
    try:
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}



def save_config(data: dict):
    try:
        CONFIG_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"TV Missing Checker v{APP_VERSION}")
        self.geometry("1620x960")
        self.minsize(1280, 760)
        self.configure(bg="#0a0f1c")

        cfg = load_config()
        self.language = normalize_language(cfg.get("language", DEFAULT_LANGUAGE))
        self.title(f"{self.tr('app_title')} v{APP_VERSION}")
        self.language_var = tk.StringVar(value=LANGUAGE_LABEL_BY_CODE.get(self.language, "English"))
        self.folder_var = tk.StringVar(value=cfg.get("last_folder", ""))
        self.filter_var = tk.StringVar()
        self.tmdb_api_key_var = tk.StringVar(value=cfg.get("tmdb_api_key", ""))
        self.tmdb_token_var = tk.StringVar(value=cfg.get("tmdb_token", ""))
        self.tvdb_api_key_var = tk.StringVar(value=cfg.get("tvdb_api_key", DEFAULT_TVDB_API_KEY))
        self.tvdb_token = cfg.get("tvdb_token", "")
        self.tvdb_token_created_at = cfg.get("tvdb_token_created_at", "")
        self.status_var = tk.StringVar(value=self.tr("status_choose_folder"))
        self.progress_label_var = tk.StringVar(value=self.tr("progress", done=0, total=0))
        self.percent_var = tk.StringVar(value="0%")
        self.displayed_var = tk.StringVar(value="0")
        self.missing_var = tk.StringVar(value="0")
        self.unmatched_var = tk.StringVar(value="0")
        self.ok_var = tk.StringVar(value="0")
        self.aired_only_var = tk.BooleanVar(value=True)
        self.unparsed_var = tk.BooleanVar(value=True)
        self.hide_ok_var = tk.BooleanVar(value=False)
        self.only_missing_var = tk.BooleanVar(value=False)
        self.only_unmatched_var = tk.BooleanVar(value=False)
        self.only_ok_var = tk.BooleanVar(value=False)
        self.remove_ok_from_report_var = tk.BooleanVar(value=False)

        self.summary: ScanSummary | None = None
        self.display_results: list[ShowResult] = []
        self.tmdb_api_key = ""
        self.tmdb_bearer_token = ""
        self.result_map: dict[str, ShowResult] = {}
        self.queue: queue.Queue = queue.Queue()
        self.is_scanning = False
        self.scan_button: ttk.Button | None = None
        self.update_button: ttk.Button | None = None
        self.update_check_running = False
        self.total_shows = 0
        self.done_shows = 0
        self._last_context_popup = {"kind": "", "time": 0, "x": 0, "y": 0}

        self._configure_style()
        self._build_ui()
        self._bind_context_menu()
        self.after(120, self._process_queue)

    def tr(self, key: str, **kwargs) -> str:
        return translate(key, self.language, **kwargs)

    def version_tuple(self, value: str) -> tuple[int, int, int]:
        parts = [int(part) for part in re.findall(r"\d+", str(value).lstrip("v"))[:3]]
        while len(parts) < 3:
            parts.append(0)
        return tuple(parts)

    def is_newer_version(self, latest: str, current: str) -> bool:
        return self.version_tuple(latest) > self.version_tuple(current)

    def open_donate(self):
        webbrowser.open(PAYPAL_DONATE_URL, new=2)

    def check_for_updates(self):
        if self.update_check_running:
            messagebox.showinfo(self.tr("update_in_progress_title"), self.tr("update_in_progress_msg"))
            return
        self.update_check_running = True
        if self.update_button is not None:
            self.update_button.config(state=tk.DISABLED)
        self.status_var.set(self.tr("checking_updates"))
        threading.Thread(target=self.update_worker, daemon=True).start()

    def update_worker(self):
        release = None
        error = None
        try:
            request = urllib.request.Request(
                GITHUB_RELEASES_API,
                headers={
                    "Accept": "application/vnd.github+json",
                    "User-Agent": f"TV-Missing-Checker/{APP_VERSION}",
                },
            )
            with urllib.request.urlopen(request, timeout=8) as response:
                data = json.loads(response.read().decode("utf-8"))
            if not data.get("draft") and not data.get("prerelease"):
                release = {
                    "tag": str(data.get("tag_name", "")).strip(),
                    "url": data.get("html_url") or GITHUB_RELEASES_URL,
                }
        except (OSError, TimeoutError, urllib.error.URLError, ValueError) as exc:
            error = exc

        try:
            self.after(0, lambda: self.handle_update_result(release, error))
        except tk.TclError:
            pass

    def handle_update_result(self, release: dict | None, error: Exception | None):
        self.update_check_running = False
        if self.update_button is not None:
            self.update_button.config(state=tk.NORMAL)
        if error is not None or not release or not release.get("tag"):
            self.status_var.set(self.tr("status_choose_folder"))
            messagebox.showwarning(self.tr("update_failed_title"), self.tr("update_failed_msg"))
            return

        latest = release["tag"]
        if not self.is_newer_version(latest, APP_VERSION):
            self.status_var.set(self.tr("update_current_msg", current=APP_VERSION))
            messagebox.showinfo(self.tr("update_current_title"), self.tr("update_current_msg", current=APP_VERSION))
            return

        self.status_var.set(self.tr("update_available_title"))
        message = self.tr("update_available_msg", current=APP_VERSION, latest=latest)
        if messagebox.askyesno(self.tr("update_available_title"), message):
            webbrowser.open(release["url"], new=2)

    def _change_language(self, _event=None):
        new_language = normalize_language(self.language_var.get())
        if new_language == self.language:
            return
        if self.is_scanning:
            self.language_var.set(LANGUAGE_LABEL_BY_CODE.get(self.language, "English"))
            self.status_var.set(self.tr("language_locked_scanning"))
            return
        self.language = new_language
        self.title(f"{self.tr('app_title')} v{APP_VERSION}")
        self._save_settings()
        self.status_var.set(self.tr("status_choose_folder"))
        self.progress_label_var.set(self.tr("progress", done=self.done_shows, total=self.total_shows))
        for child in self.winfo_children():
            child.destroy()
        self._build_ui()
        self._bind_context_menu()
        self.refresh_views()

    def _configure_style(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except Exception:
            pass

        bg = "#0a0f1c"
        surface = "#101827"
        surface2 = "#162033"
        surface3 = "#1d293d"
        border = "#26364f"
        text = "#edf3fb"
        muted = "#98a6ba"
        accent = "#38bdf8"
        accent2 = "#0ea5e9"
        green = "#34d399"
        amber = "#fbbf24"
        red = "#fb7185"

        self.option_add("*Font", ("Segoe UI", 10))
        self.option_add("*Menu.background", surface)
        self.option_add("*Menu.foreground", text)
        self.option_add("*Menu.activeBackground", accent2)
        self.option_add("*Menu.activeForeground", "#06101f")

        style.configure("TFrame", background=bg)
        style.configure("Surface.TFrame", background=surface)
        style.configure("Elevated.TFrame", background=surface2)
        style.configure("Toolbar.TFrame", background=bg)
        style.configure("Card.TFrame", background=surface2, relief="flat")

        style.configure("TLabelframe", background=surface, foreground=text, borderwidth=1, relief="solid")
        style.configure("TLabelframe.Label", background=surface, foreground=text, font=("Segoe UI", 10, "bold"))
        style.configure("Panel.TLabelframe", background=surface, foreground=text, bordercolor=border, lightcolor=border, darkcolor=border)

        style.configure("TLabel", background=bg, foreground=text, font=("Segoe UI", 10))
        style.configure("Surface.TLabel", background=surface, foreground=text, font=("Segoe UI", 10))
        style.configure("SurfaceMuted.TLabel", background=surface, foreground=muted, font=("Segoe UI", 9))
        style.configure("Muted.TLabel", background=bg, foreground=muted, font=("Segoe UI", 9))
        style.configure("Title.TLabel", background=bg, foreground=text, font=("Segoe UI", 17, "bold"))
        style.configure("Section.TLabel", background=surface, foreground="#dbeafe", font=("Segoe UI", 10, "bold"))
        style.configure("Small.TLabel", background=bg, foreground=muted, font=("Segoe UI", 9))

        style.configure("TButton", font=("Segoe UI", 9, "bold"), padding=(12, 8), background=surface3, foreground=text, bordercolor=border, focusthickness=0)
        style.map("TButton", background=[("active", "#26364f"), ("disabled", "#111827")], foreground=[("disabled", "#64748b")])
        style.configure("Accent.TButton", background=accent2, foreground="#06101f", bordercolor=accent2, padding=(14, 9), font=("Segoe UI", 10, "bold"))
        style.map("Accent.TButton", background=[("active", accent), ("disabled", "#164e63")], foreground=[("disabled", "#94a3b8")])
        style.configure("Ghost.TButton", background=surface, foreground=text, bordercolor=border, padding=(10, 7), font=("Segoe UI", 9))
        style.map("Ghost.TButton", background=[("active", surface3), ("disabled", surface)])
        style.configure("Compact.TButton", background=surface3, foreground=text, bordercolor=border, padding=(8, 6), font=("Segoe UI", 9, "bold"))
        style.map("Compact.TButton", background=[("active", "#334155"), ("disabled", "#111827")])
        style.configure("Danger.TButton", background="#7f1d1d", foreground="#fee2e2", bordercolor="#ef4444", padding=(10, 7), font=("Segoe UI", 9, "bold"))
        style.map("Danger.TButton", background=[("active", "#991b1b"), ("disabled", "#111827")], foreground=[("disabled", "#64748b")])

        style.configure("TCheckbutton", background=surface, foreground=text, font=("Segoe UI", 9))
        style.map("TCheckbutton", background=[("active", surface)], foreground=[("active", text), ("disabled", "#64748b")])

        style.configure("TEntry", fieldbackground="#070c16", foreground=text, insertcolor=text, bordercolor=border, lightcolor=border, darkcolor=border, padding=(8, 6))
        style.configure("Treeview", background="#080d18", foreground=text, fieldbackground="#080d18", rowheight=31, bordercolor=border, lightcolor=border, darkcolor=border, font=("Segoe UI", 10))
        style.configure("Treeview.Heading", background=surface3, foreground="#dbeafe", font=("Segoe UI", 9, "bold"), relief="flat")
        style.map("Treeview", background=[("selected", accent2)], foreground=[("selected", "#06101f")])
        style.configure("Horizontal.TProgressbar", troughcolor="#070c16", background=accent2, bordercolor=border, lightcolor=accent2, darkcolor=accent2)

        style.configure("TNotebook", background=surface, borderwidth=0)
        style.configure("TNotebook.Tab", background=surface2, foreground=muted, padding=(16, 8), font=("Segoe UI", 9, "bold"))
        style.map("TNotebook.Tab", background=[("selected", accent2)], foreground=[("selected", "#06101f")])

        style.configure("StatTitle.TLabel", background=surface2, foreground=muted, font=("Segoe UI", 9, "bold"))
        style.configure("StatValue.TLabel", background=surface2, foreground=text, font=("Segoe UI", 22, "bold"))
        style.configure("StatOk.TLabel", background=surface2, foreground=green, font=("Segoe UI", 22, "bold"))
        style.configure("StatWarn.TLabel", background=surface2, foreground=amber, font=("Segoe UI", 22, "bold"))
        style.configure("StatBad.TLabel", background=surface2, foreground=red, font=("Segoe UI", 22, "bold"))

    def _build_ui(self):
        outer = ttk.Frame(self, padding=14)
        outer.pack(fill="both", expand=True)
        outer.columnconfigure(0, weight=1)
        outer.rowconfigure(1, weight=1)

        header = ttk.Frame(outer, style="Toolbar.TFrame")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        header.columnconfigure(0, weight=1)
        ttk.Label(header, text=f"{self.tr('app_title')} v{APP_VERSION}", style="Title.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(
            header,
            text=f"{self.tr('version_label', version=APP_VERSION)} | {self.tr('subtitle')}",
            style="Muted.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(2, 0))

        header_tools = ttk.Frame(header, style="Toolbar.TFrame")
        header_tools.grid(row=0, column=1, rowspan=2, sticky="e", padx=(12, 0))
        self.update_button = ttk.Button(header_tools, text=self.tr("check_updates"), command=self.check_for_updates, style="Ghost.TButton")
        self.update_button.grid(row=0, column=0, sticky="e", padx=(0, 8))
        ttk.Button(header_tools, text=self.tr("donate"), command=self.open_donate, style="Ghost.TButton").grid(row=0, column=1, sticky="e", padx=(0, 12))
        ttk.Label(header_tools, text=self.tr("language"), style="Muted.TLabel").grid(row=0, column=2, sticky="e")
        language_box = ttk.Combobox(
            header_tools,
            textvariable=self.language_var,
            values=[label for _code, label in LANGUAGE_CHOICES],
            state="readonly",
            width=12,
        )
        language_box.grid(row=1, column=2, sticky="e", pady=(2, 0))
        language_box.bind("<<ComboboxSelected>>", self._change_language)

        body = ttk.Frame(outer)
        body.grid(row=1, column=0, sticky="nsew")
        body.columnconfigure(0, weight=0, minsize=330)
        body.columnconfigure(1, weight=7)
        body.columnconfigure(2, weight=4)
        body.rowconfigure(0, weight=1)

        sidebar = ttk.Frame(body, style="Surface.TFrame", padding=14, width=330)
        sidebar.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        sidebar.grid_propagate(False)
        sidebar.columnconfigure(0, weight=1)

        ttk.Label(sidebar, text=self.tr("library"), style="Section.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(sidebar, text=self.tr("main_folder"), style="SurfaceMuted.TLabel").grid(row=1, column=0, sticky="w", pady=(8, 4))
        ttk.Entry(sidebar, textvariable=self.folder_var).grid(row=2, column=0, sticky="ew")
        folder_buttons = ttk.Frame(sidebar, style="Surface.TFrame")
        folder_buttons.grid(row=3, column=0, sticky="ew", pady=(8, 14))
        folder_buttons.columnconfigure(0, weight=1)
        folder_buttons.columnconfigure(1, weight=1)
        ttk.Button(folder_buttons, text=self.tr("choose_folder"), command=self.pick_folder, style="Ghost.TButton").grid(row=0, column=0, sticky="ew", padx=(0, 6))
        self.scan_button = ttk.Button(folder_buttons, text=self.tr("start_scan"), command=self.start_scan, style="Accent.TButton")
        self.scan_button.grid(row=0, column=1, sticky="ew", padx=(6, 0))

        ttk.Separator(sidebar).grid(row=4, column=0, sticky="ew", pady=(0, 14))
        ttk.Label(sidebar, text=self.tr("online_sources"), style="Section.TLabel").grid(row=5, column=0, sticky="w")
        ttk.Label(sidebar, text="TMDb API key", style="SurfaceMuted.TLabel").grid(row=6, column=0, sticky="w", pady=(8, 4))
        ttk.Entry(sidebar, textvariable=self.tmdb_api_key_var, show="•").grid(row=7, column=0, sticky="ew")
        ttk.Label(sidebar, text="TMDb token", style="SurfaceMuted.TLabel").grid(row=8, column=0, sticky="w", pady=(8, 4))
        ttk.Entry(sidebar, textvariable=self.tmdb_token_var, show="•").grid(row=9, column=0, sticky="ew")
        ttk.Label(sidebar, text="TheTVDB API key", style="SurfaceMuted.TLabel").grid(row=10, column=0, sticky="w", pady=(8, 4))
        ttk.Entry(sidebar, textvariable=self.tvdb_api_key_var, show="•").grid(row=11, column=0, sticky="ew")

        ttk.Separator(sidebar).grid(row=12, column=0, sticky="ew", pady=14)
        ttk.Label(sidebar, text=self.tr("scan_settings"), style="Section.TLabel").grid(row=13, column=0, sticky="w")
        ttk.Checkbutton(sidebar, text=self.tr("aired_only"), variable=self.aired_only_var).grid(row=14, column=0, sticky="w", pady=(8, 2))
        ttk.Checkbutton(sidebar, text=self.tr("include_unparsed"), variable=self.unparsed_var).grid(row=15, column=0, sticky="w", pady=2)
        ttk.Checkbutton(sidebar, text=self.tr("exclude_ok_report"), variable=self.remove_ok_from_report_var, command=self.refresh_views).grid(row=16, column=0, sticky="w", pady=2)

        ttk.Separator(sidebar).grid(row=17, column=0, sticky="ew", pady=14)
        ttk.Label(sidebar, text=self.tr("status"), style="Section.TLabel").grid(row=18, column=0, sticky="w")
        ttk.Label(sidebar, textvariable=self.status_var, style="SurfaceMuted.TLabel", wraplength=292).grid(row=19, column=0, sticky="ew", pady=(8, 8))
        self.progress = ttk.Progressbar(sidebar, mode="determinate", maximum=100)
        self.progress.grid(row=20, column=0, sticky="ew")
        progress_line = ttk.Frame(sidebar, style="Surface.TFrame")
        progress_line.grid(row=21, column=0, sticky="ew", pady=(6, 14))
        progress_line.columnconfigure(0, weight=1)
        ttk.Label(progress_line, textvariable=self.progress_label_var, style="SurfaceMuted.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(progress_line, textvariable=self.percent_var, style="SurfaceMuted.TLabel").grid(row=0, column=1, sticky="e")

        ttk.Label(sidebar, text=self.tr("status_filter"), style="Section.TLabel").grid(row=22, column=0, sticky="w")
        filt = ttk.Frame(sidebar, style="Surface.TFrame")
        filt.grid(row=23, column=0, sticky="ew", pady=(8, 0))
        for i in range(2):
            filt.columnconfigure(i, weight=1)
        ttk.Button(filt, text=self.tr("all"), command=self.reset_filters, style="Compact.TButton").grid(row=0, column=0, sticky="ew", padx=(0, 5), pady=(0, 8))
        ttk.Button(filt, text=self.tr("missing"), command=lambda: self.set_status_filter("missing"), style="Compact.TButton").grid(row=0, column=1, sticky="ew", padx=(5, 0), pady=(0, 8))
        ttk.Button(filt, text=self.tr("unmatched"), command=lambda: self.set_status_filter("unmatched"), style="Compact.TButton").grid(row=1, column=0, sticky="ew", padx=(0, 5))
        ttk.Button(filt, text="OK", command=lambda: self.set_status_filter("ok"), style="Compact.TButton").grid(row=1, column=1, sticky="ew", padx=(5, 0))
        ttk.Checkbutton(sidebar, text=self.tr("hide_ok"), variable=self.hide_ok_var, command=self.refresh_views).grid(row=24, column=0, sticky="w", pady=(12, 0))

        content = ttk.Frame(body)
        content.grid(row=0, column=1, sticky="nsew", padx=(0, 12))
        content.columnconfigure(0, weight=1)
        content.rowconfigure(2, weight=1)

        stats = ttk.Frame(content)
        stats.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        for i in range(4):
            stats.columnconfigure(i, weight=1)
        self._make_stat(stats, 0, self.tr("displayed"), self.displayed_var, "StatValue.TLabel")
        self._make_stat(stats, 1, self.tr("missing"), self.missing_var, "StatBad.TLabel")
        self._make_stat(stats, 2, self.tr("unmatched"), self.unmatched_var, "StatWarn.TLabel")
        self._make_stat(stats, 3, "OK", self.ok_var, "StatOk.TLabel")

        toolbar = ttk.Frame(content, style="Toolbar.TFrame")
        toolbar.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        toolbar.columnconfigure(1, weight=1)
        ttk.Label(toolbar, text=self.tr("results"), style="Title.TLabel").grid(row=0, column=0, sticky="w", padx=(0, 18))
        search = ttk.Entry(toolbar, textvariable=self.filter_var)
        search.grid(row=0, column=1, sticky="ew", padx=(0, 8))
        search.bind("<KeyRelease>", lambda _e: self.refresh_views())
        ttk.Button(toolbar, text=self.tr("clear"), command=self.clear_filter, style="Ghost.TButton").grid(row=0, column=2, padx=(0, 8))
        ttk.Button(toolbar, text=self.tr("remove_ok"), command=self.remove_ok_from_view, style="Ghost.TButton").grid(row=0, column=3)

        results_box = ttk.Frame(content, style="Surface.TFrame", padding=10)
        results_box.grid(row=2, column=0, sticky="nsew")
        results_box.rowconfigure(0, weight=1)
        results_box.columnconfigure(0, weight=1)

        cols = ("series", "year", "status", "source", "matched", "missing_count", "missing")
        self.tree = ttk.Treeview(results_box, columns=cols, show="headings")
        self.tree.heading("series", text=self.tr("series"))
        self.tree.heading("year", text=self.tr("year_short"))
        self.tree.heading("status", text=self.tr("status"))
        self.tree.heading("source", text=self.tr("source"))
        self.tree.heading("matched", text=self.tr("matched_as"))
        self.tree.heading("missing_count", text=self.tr("missing_count"))
        self.tree.heading("missing", text=self.tr("missing"))
        self.tree.column("series", width=230, anchor="w")
        self.tree.column("year", width=60, anchor="center")
        self.tree.column("status", width=100, anchor="center")
        self.tree.column("source", width=80, anchor="center")
        self.tree.column("matched", width=230, anchor="w")
        self.tree.column("missing_count", width=82, anchor="center")
        self.tree.column("missing", width=340, anchor="w")
        self.tree.grid(row=0, column=0, sticky="nsew")
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)
        yscroll = ttk.Scrollbar(results_box, orient="vertical", command=self.tree.yview)
        yscroll.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=yscroll.set)

        right = ttk.Frame(body, style="Surface.TFrame", padding=12)
        right.grid(row=0, column=2, sticky="nsew")
        right.rowconfigure(0, weight=1)
        right.columnconfigure(0, weight=1)

        tabs = ttk.Notebook(right)
        tabs.grid(row=0, column=0, sticky="nsew")

        details_tab = ttk.Frame(tabs)
        missing_tab = ttk.Frame(tabs)
        report_tab = ttk.Frame(tabs)
        tabs.add(details_tab, text=self.tr("details"))
        tabs.add(missing_tab, text=self.tr("missing_overview"))
        tabs.add(report_tab, text=self.tr("txt_report"))

        text_opts = {
            "wrap": "word",
            "bg": "#080d18",
            "fg": "#edf3fb",
            "insertbackground": "#edf3fb",
            "selectbackground": "#0ea5e9",
            "selectforeground": "#06101f",
            "relief": "flat",
            "font": ("Consolas", 10),
            "padx": 10,
            "pady": 10,
            "highlightthickness": 1,
            "highlightbackground": "#26364f",
        }
        self.detail_text = tk.Text(details_tab, **text_opts)
        self.detail_text.pack(fill="both", expand=True)
        self.missing_text = tk.Text(missing_tab, **text_opts)
        self.missing_text.pack(fill="both", expand=True)
        self.report_box = tk.Text(report_tab, **text_opts)
        self.report_box.pack(fill="both", expand=True)

        actions = ttk.LabelFrame(right, text=self.tr("selected_actions"), style="Panel.TLabelframe", padding=10)
        actions.grid(row=1, column=0, sticky="ew", pady=(12, 0))
        for i in range(3):
            actions.columnconfigure(i, weight=1)
        ttk.Button(actions, text=self.tr("manual_match"), command=self.open_manual_match_dialog, style="Accent.TButton").grid(row=0, column=0, sticky="ew", padx=(0, 6), pady=(0, 8))
        ttk.Button(actions, text=self.tr("files"), command=self.open_file_overview, style="Ghost.TButton").grid(row=0, column=1, sticky="ew", padx=6, pady=(0, 8))
        ttk.Button(actions, text=self.tr("open_web"), command=self.open_selected_in_browser, style="Ghost.TButton").grid(row=0, column=2, sticky="ew", padx=(6, 0), pady=(0, 8))
        ttk.Button(actions, text=self.tr("mark_ok"), command=self.mark_selected_series_ok, style="Ghost.TButton").grid(row=1, column=0, sticky="ew", padx=(0, 6))
        ttk.Button(actions, text=self.tr("open_folder"), command=self.open_selected_folder, style="Ghost.TButton").grid(row=1, column=1, sticky="ew", padx=6)
        ttk.Button(actions, text=self.tr("save_txt"), command=self.save_txt, style="Ghost.TButton").grid(row=1, column=2, sticky="ew", padx=(6, 0))
        ttk.Button(actions, text=self.tr("save_json"), command=self.save_json, style="Ghost.TButton").grid(row=2, column=0, sticky="ew", padx=(0, 6), pady=(8, 0))
        ttk.Button(actions, text=self.tr("copy_missing"), command=self.copy_missing, style="Ghost.TButton").grid(row=2, column=1, sticky="ew", padx=6, pady=(8, 0))
        ttk.Button(actions, text=self.tr("copy_unmatched"), command=self.copy_unmatched, style="Ghost.TButton").grid(row=2, column=2, sticky="ew", padx=(6, 0), pady=(8, 0))
        ttk.Button(actions, text=self.tr("delete_disk"), command=self.delete_selected_series_from_disk, style="Danger.TButton").grid(row=3, column=2, sticky="ew", padx=(6, 0), pady=(8, 0))

    def _bind_context_menu(self):
        self.context_menu = tk.Menu(
            self,
            tearoff=0,
            bg="#101827",
            fg="#edf3fb",
            activebackground="#38bdf8",
            activeforeground="#06101f",
        )
        self.context_menu.add_command(label=self.tr("open_browser"), command=self.open_selected_in_browser)
        self.context_menu.add_command(label=self.tr("open_series_folder"), command=self.open_selected_folder)
        self.context_menu.add_command(label=self.tr("file_overview"), command=self.open_file_overview)
        self.context_menu.add_command(label=self.tr("check_tmdb"), command=self.check_selected_with_tmdb)
        self.context_menu.add_command(label=self.tr("manual_match"), command=self.open_manual_match_dialog)
        self.context_menu.add_command(label=self.tr("mark_series_ok"), command=self.mark_selected_series_ok)
        self.context_menu.add_separator()
        self.context_menu.add_command(label=self.tr("copy_link"), command=self.copy_selected_link)
        self.context_menu.add_separator()
        self.context_menu.add_command(label=self.tr("delete_series_disk"), command=self.delete_selected_series_from_disk)

        self.text_context_menu = tk.Menu(
            self,
            tearoff=0,
            bg="#101827",
            fg="#edf3fb",
            activebackground="#38bdf8",
            activeforeground="#06101f",
        )
        self.text_context_menu.add_command(label=self.tr("copy"), command=self.copy_selected_widget_text)
        self._text_context_widget = None

        # Open context menus after the button release. Posting them on press can
        # consume the following click/release sequence before a menu command runs.
        self.tree.bind("<ButtonRelease-3>", self._show_context_menu, add="+")
        self.tree.bind("<Control-ButtonRelease-1>", self._show_context_menu, add="+")
        for widget in (self.detail_text, self.missing_text, self.report_box):
            widget.bind("<ButtonRelease-3>", self._show_text_context_menu, add="+")
            widget.bind("<Control-ButtonRelease-1>", self._show_text_context_menu, add="+")

    def _show_context_menu(self, event):
        if self._is_duplicate_context_popup(event, "tree"):
            return "break"
        self._hide_context_menus()
        row = self.tree.identify_row(event.y)
        if not row:
            row = self.tree.focus()
        if row:
            self.tree.selection_set(row)
            self.tree.focus(row)
            self.on_tree_select()
            try:
                self.context_menu.tk_popup(event.x_root, event.y_root)
            finally:
                self.context_menu.grab_release()
            self._remember_context_popup(event, "tree")
        return "break"

    def _is_duplicate_context_popup(self, event, kind: str) -> bool:
        event_time = int(getattr(event, "time", 0) or 0)
        last = self._last_context_popup
        if last.get("kind") != kind:
            return False
        close_position = abs(int(event.x_root) - int(last.get("x", 0))) <= 3 and abs(int(event.y_root) - int(last.get("y", 0))) <= 3
        if not close_position:
            return False
        last_time = int(last.get("time", 0) or 0)
        return bool(event_time and last_time and 0 <= event_time - last_time <= 400)

    def _remember_context_popup(self, event, kind: str):
        self._last_context_popup = {
            "kind": kind,
            "time": int(getattr(event, "time", 0) or 0),
            "x": int(event.x_root),
            "y": int(event.y_root),
        }

    def _hide_context_menus(self, _event=None):
        for menu_name in ("context_menu", "text_context_menu"):
            menu = getattr(self, menu_name, None)
            if menu:
                try:
                    menu.unpost()
                except tk.TclError:
                    pass

    def _get_widget_selected_text(self, widget) -> str:
        try:
            return widget.get("sel.first", "sel.last")
        except tk.TclError:
            return ""

    def _show_text_context_menu(self, event):
        if self._is_duplicate_context_popup(event, "text"):
            return "break"
        self._hide_context_menus()
        widget = event.widget
        self._text_context_widget = widget
        state = "normal" if self._get_widget_selected_text(widget) else "disabled"
        self.text_context_menu.entryconfigure(0, state=state)
        try:
            self.text_context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.text_context_menu.grab_release()
        self._remember_context_popup(event, "text")
        return "break"

    def copy_selected_widget_text(self):
        widget = self._text_context_widget
        if widget is None:
            return
        text = self._get_widget_selected_text(widget)
        if not text:
            return
        self.clipboard_clear()
        self.clipboard_append(text)
        self.status_var.set(self.tr("selected_text_copied"))

    def _make_stat(self, parent, col, title, variable, value_style="StatValue.TLabel"):
        card = ttk.Frame(parent, style="Card.TFrame", padding=12)
        card.grid(row=0, column=col, sticky="nsew", padx=(0 if col == 0 else 8, 0))
        ttk.Label(card, text=title, style="StatTitle.TLabel").pack(anchor="w")
        ttk.Label(card, textvariable=variable, style=value_style).pack(anchor="w", pady=(4, 0))

    def pick_folder(self):
        folder = ""

        # Na KDE/Plasma koristi nativni KDE file picker (isti Places/Remote kao Dolphin),
        # pa se vide NAS lokacije koje si dodao u Dolphin.
        start_dir = self.folder_var.get().strip() or str(Path.home())
        try:
            result = subprocess.run(
                ["kdialog", "--getexistingdirectory", start_dir],
                text=True,
                capture_output=True,
                check=False,
            )
            if result.returncode == 0:
                folder = (result.stdout or "").strip()
        except FileNotFoundError:
            # kdialog nije instaliran; koristimo Tkinter fallback.
            folder = ""
        except Exception:
            folder = ""

        # Ako KDE vrati file:// URL, pretvori ga u običan lokalni path.
        # SMB/NAS lokacije koje su otvorene preko kio-fuse obično dođu kao lokalni path
        # npr. /run/user/1000/kio-fuse-... i tada ih Python može skenirati.
        if folder.startswith("file://"):
            folder = urllib.parse.unquote(urllib.parse.urlparse(folder).path)

        # Fallback za sustave bez kdialoga.
        if not folder:
            folder = filedialog.askdirectory(title=self.tr("missing_folder_msg"))

        if folder:
            self.folder_var.set(folder)
            self._save_settings()

    def _save_settings(self):
        save_config({
            "language": self.language,
            "last_folder": self.folder_var.get().strip(),
            "tmdb_api_key": self.tmdb_api_key_var.get().strip(),
            "tmdb_token": self.tmdb_token_var.get().strip(),
            "tvdb_api_key": self.tvdb_api_key_var.get().strip(),
            "tvdb_token": self.tvdb_token,
            "tvdb_token_created_at": self.tvdb_token_created_at,
        })

    def _save_tvdb_token(self, token: str, created_at: str, message: str = ""):
        self.tvdb_token = token
        self.tvdb_token_created_at = created_at
        self._save_settings()
        if message:
            self.status_var.set(message)

    def reset_filters(self):
        self.hide_ok_var.set(False)
        self.only_missing_var.set(False)
        self.only_unmatched_var.set(False)
        self.only_ok_var.set(False)
        self.refresh_views()

    def set_status_filter(self, status: str):
        self.hide_ok_var.set(False)
        self.only_missing_var.set(status == "missing")
        self.only_unmatched_var.set(status == "unmatched")
        self.only_ok_var.set(status == "ok")
        self.refresh_views()

    def clear_filter(self):
        self.filter_var.set("")
        self.refresh_views()

    def start_scan(self):
        if self.is_scanning:
            return
        folder = self.folder_var.get().strip()
        if not folder:
            messagebox.showwarning(self.tr("missing_folder_title"), self.tr("missing_folder_msg"))
            return
        root = Path(folder)
        if not root.exists() or not root.is_dir():
            messagebox.showwarning(self.tr("invalid_folder_title"), self.tr("invalid_folder_msg"))
            return

        self._save_settings()
        self.is_scanning = True
        if self.scan_button:
            self.scan_button.configure(state="disabled")
        self.summary = ScanSummary(root=str(root), created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        self.result_map.clear()
        self.display_results = []
        self.total_shows = 0
        self.done_shows = 0
        self.progress["value"] = 0
        self.progress_label_var.set(self.tr("progress", done=0, total=0))
        self.percent_var.set("0%")
        self.status_var.set(self.tr("scanning_library"))
        self.detail_text.delete("1.0", "end")
        self.missing_text.delete("1.0", "end")
        self.report_box.delete("1.0", "end")
        for item in self.tree.get_children():
            self.tree.delete(item)
        self._update_stats([])

        tmdb_api_key = self.tmdb_api_key_var.get().strip()
        tmdb_token = self.tmdb_token_var.get().strip()
        tvdb_api_key = self.tvdb_api_key_var.get().strip()
        tvdb_token = self.tvdb_token
        tvdb_token_created_at = self.tvdb_token_created_at
        aired_only = self.aired_only_var.get()
        threading.Thread(
            target=self._scan_worker,
            args=(root, tmdb_api_key, tmdb_token, tvdb_api_key, tvdb_token, tvdb_token_created_at, aired_only),
            daemon=True,
        ).start()

    def _scan_worker(self, root: Path, tmdb_api_key: str, tmdb_token: str, tvdb_api_key: str,
                     tvdb_token: str, tvdb_token_created_at: str, aired_only: bool):
        try:
            tmdb_probe = TMDbClient(tmdb_api_key, tmdb_token)
            tvdb_probe = TVDBClient(tvdb_api_key, tvdb_token, tvdb_token_created_at)
            tvdb_enabled = tvdb_probe.enabled
            tvdb_auth_message = ""
            if tvdb_enabled:
                try:
                    tvdb_probe.ensure_token()
                    tvdb_token = tvdb_probe.token
                    tvdb_token_created_at = tvdb_probe.token_created_at
                    tvdb_auth_message = tvdb_probe.auth_message
                    if tvdb_probe.token_refreshed:
                        self.queue.put(("tvdb_token", {
                            "token": tvdb_token,
                            "created_at": tvdb_token_created_at,
                            "message": tvdb_auth_message,
                        }))
                except TVDBAuthError as e:
                    tvdb_enabled = False
                    tvdb_token = ""
                    tvdb_token_created_at = ""
                    tvdb_auth_message = str(e)
                    self.queue.put(("notice", {"message": tvdb_auth_message}))
            shows, unparsed = scan_library(root)
            show_items = [(show_name, shows[show_name]) for show_name in sorted(shows)]
            worker_count = min(MAX_SCAN_WORKERS, len(show_items)) if show_items else 0
            video_count = sum(len(inv.files) for inv in shows.values())
            self.queue.put(("scan_started", {
                "total": len(shows),
                "video_count": video_count,
                "unparsed": unparsed,
                "tmdb_enabled": tmdb_probe.enabled,
                "tvdb_enabled": tvdb_enabled,
                "tvdb_auth_message": tvdb_auth_message,
                "workers": worker_count,
            }))
            if not shows:
                self.queue.put(("done", {"message_key": "no_video_files"}))
                return

            def run_one(show_name: str, inv: EpisodeInventory) -> ShowResult:
                self.queue.put(("checking", {"total": len(show_items), "show": show_name, "workers": worker_count}))
                return check_show_online(
                    inv,
                    tmdb_api_key,
                    tmdb_token,
                    tvdb_api_key if tvdb_enabled else "",
                    tvdb_token if tvdb_enabled else "",
                    tvdb_token_created_at if tvdb_enabled else "",
                    aired_only,
                )

            completed = 0
            if worker_count <= 1:
                for show_name, inv in show_items:
                    result = run_one(show_name, inv)
                    completed += 1
                    self.queue.put(("result", {"result": result, "index": completed, "total": len(show_items), "show": show_name}))
            else:
                with ThreadPoolExecutor(max_workers=worker_count) as executor:
                    future_to_show = {
                        executor.submit(run_one, show_name, inv): show_name
                        for show_name, inv in show_items
                    }
                    for future in as_completed(future_to_show):
                        show_name = future_to_show[future]
                        result = future.result()
                        completed += 1
                        self.queue.put(("result", {"result": result, "index": completed, "total": len(show_items), "show": show_name}))

            self.queue.put(("done", {}))
        except Exception as e:
            self.queue.put(("error", {"error": f"{e}\n\n{traceback.format_exc()}"}))

    def _process_queue(self):
        try:
            while True:
                kind, payload = self.queue.get_nowait()
                if kind == "scan_started":
                    unparsed = payload["unparsed"]
                    self.total_shows = payload["total"]
                    video_count = payload.get("video_count", 0)
                    if self.summary:
                        self.summary.unparsed = unparsed if self.unparsed_var.get() else []
                        self.summary.unparsed_count = len(unparsed)
                    src_parts = ["TVMaze"]
                    if payload.get("tmdb_enabled"):
                        src_parts.append("TMDb")
                    if payload.get("tvdb_enabled"):
                        src_parts.append("TVDB")
                    src_parts.append("IMDb")
                    src = " + ".join(src_parts)
                    workers = payload.get("workers", 0)
                    parallel_text = self.tr("parallel", workers=workers) if workers > 1 else ""
                    if self.total_shows:
                        self.status_var.set(self.tr("found_summary", shows=self.total_shows, videos=video_count, sources=src, parallel=parallel_text))
                    else:
                        self.status_var.set(self.tr("no_video_files"))
                    self.progress_label_var.set(self.tr("progress", done=0, total=self.total_shows))
                    if payload.get("tvdb_auth_message"):
                        self.status_var.set(payload["tvdb_auth_message"])
                elif kind == "tvdb_token":
                    self._save_tvdb_token(
                        payload.get("token", ""),
                        payload.get("created_at", ""),
                        payload.get("message", ""),
                    )
                elif kind == "notice":
                    self.status_var.set(payload.get("message", ""))
                elif kind == "checking":
                    show = payload["show"]
                    workers = payload.get("workers", 1)
                    suffix = self.tr("checking_suffix", workers=workers) if workers > 1 else ""
                    self.status_var.set(self.tr("checking", show=show, suffix=suffix))
                elif kind == "progress":
                    total = payload["total"]
                    index = payload["index"]
                    show = payload["show"]
                    percent = int((index / total) * 100) if total else 0
                    self.progress["value"] = percent
                    self.progress_label_var.set(self.tr("progress", done=index, total=total))
                    self.percent_var.set(f"{percent}%")
                    self.status_var.set(f"[{index + 1}/{total}] {self.tr('checking', show=show, suffix='')}")
                elif kind == "result":
                    result: ShowResult = payload["result"]
                    self.done_shows = payload["index"]
                    if self.summary:
                        self.summary.results.append(result)
                        self.summary.results.sort(key=lambda r: (0 if r.status == "MISSING" else 1 if r.status in {"UNMATCHED", "EMPTY_DB"} else 2, r.local_name.lower()))
                        self.summary.ok_count = sum(1 for r in self.summary.results if r.status == "OK")
                        self.summary.missing_count = sum(1 for r in self.summary.results if r.status == "MISSING")
                        self.summary.unmatched_count = sum(1 for r in self.summary.results if r.status in {"UNMATCHED", "EMPTY_DB"})
                    self.result_map[result.local_name] = result
                    percent = int((self.done_shows / payload["total"]) * 100) if payload["total"] else 0
                    self.progress["value"] = percent
                    self.progress_label_var.set(self.tr("progress", done=self.done_shows, total=payload["total"]))
                    self.percent_var.set(f"{percent}%")
                    self.refresh_views()
                elif kind == "done":
                    self.is_scanning = False
                    if self.scan_button:
                        self.scan_button.configure(state="normal")
                    self.progress["value"] = 100 if self.total_shows else 0
                    self.progress_label_var.set(self.tr("progress", done=self.done_shows, total=self.total_shows))
                    self.percent_var.set("100%" if self.total_shows else "0%")
                    message = self.tr(payload["message_key"]) if payload.get("message_key") else payload.get("message")
                    self.status_var.set(message or self.tr("done"))
                    self.refresh_views()
                elif kind == "error":
                    self.is_scanning = False
                    if self.scan_button:
                        self.scan_button.configure(state="normal")
                    self.status_var.set(self.tr("error"))
                    self.detail_text.delete("1.0", "end")
                    self.detail_text.insert("1.0", payload["error"])
                    messagebox.showerror(self.tr("error"), payload["error"])
        except queue.Empty:
            pass
        self.after(120, self._process_queue)

    def refresh_views(self):
        if not self.summary:
            self._update_stats([])
            return

        text_filter = self.filter_var.get().strip().lower()
        filtered = []
        for r in self.summary.results:
            if self.hide_ok_var.get() and r.status == "OK":
                continue
            if self.only_missing_var.get() and r.status != "MISSING":
                continue
            if self.only_unmatched_var.get() and r.status not in {"UNMATCHED", "EMPTY_DB"}:
                continue
            if self.only_ok_var.get() and r.status != "OK":
                continue
            hay = " ".join([
                r.local_name,
                r.official_name,
                r.matched_query,
                r.status,
                r.source,
                str(r.local_year or ""),
                str(r.official_year or ""),
                summarize_missing(r.missing),
            ]).lower()
            if text_filter and text_filter not in hay:
                continue
            filtered.append(r)

        self.display_results = filtered
        self._reload_tree(use_current_display=True)
        report = create_report(
            self.summary,
            include_ok=not self.remove_ok_from_report_var.get(),
            include_unparsed=self.unparsed_var.get(),
            language=self.language,
        )
        self.report_box.delete("1.0", "end")
        self.report_box.insert("1.0", report)
        self._update_stats(filtered)

    def _reload_tree(self, use_current_display=False):
        items = self.display_results if use_current_display else []
        selected = None
        current = self.tree.selection()
        if current:
            vals = self.tree.item(current[0], "values")
            if vals:
                selected = vals[0]
        for iid in self.tree.get_children():
            self.tree.delete(iid)
        for r in items:
            matched = r.official_name + (f" ({r.official_year})" if r.official_year else "") if r.official_name else "-"
            self.tree.insert(
                "",
                "end",
                iid=r.local_name,
                values=(
                    r.local_name,
                    r.local_year or "-",
                    r.status,
                    r.source or "-",
                    matched,
                    r.missing_count if r.status == "MISSING" else (0 if r.status == "OK" else "-"),
                    summarize_missing(r.missing) if r.status == "MISSING" else ("OK" if r.status == "OK" else "-"),
                ),
                tags=(r.status,),
            )
        self.tree.tag_configure("MISSING", background="#1f2937", foreground="#fde68a")
        self.tree.tag_configure("OK", background="#0b1324", foreground="#86efac")
        self.tree.tag_configure("UNMATCHED", background="#1f1720", foreground="#fda4af")
        self.tree.tag_configure("EMPTY_DB", background="#1f1720", foreground="#fca5a5")

        if selected and self.tree.exists(selected):
            self.tree.selection_set(selected)
            self.on_tree_select()
        elif items:
            first = items[0].local_name
            if self.tree.exists(first):
                self.tree.selection_set(first)
                self.on_tree_select()
        else:
            self.detail_text.delete("1.0", "end")
            self.missing_text.delete("1.0", "end")

    def _update_stats(self, filtered: list[ShowResult]):
        self.displayed_var.set(str(len(filtered)))
        self.missing_var.set(str(sum(1 for r in filtered if r.status == "MISSING")))
        self.unmatched_var.set(str(sum(1 for r in filtered if r.status in {"UNMATCHED", "EMPTY_DB"})))
        self.ok_var.set(str(sum(1 for r in filtered if r.status == "OK")))

    def on_tree_select(self, _event=None):
        sel = self.tree.selection()
        if not sel:
            return
        key = sel[0]
        result = self.result_map.get(key)
        if not result:
            return

        detail_lines = [
            f"{self.tr('series_label')}: {result.local_name}{format_local_year(result.local_year)}",
            f"{self.tr('status')}: {result.status}",
            f"{self.tr('source')}: {result.source or '-'}",
        ]
        if result.official_name:
            detail_lines.append(f"{self.tr('matched_as')}: {result.official_name}{format_local_year(result.official_year)}")
        if result.matched_query:
            detail_lines.append(f"{self.tr('query')}: {result.matched_query}")
        if result.match_score:
            detail_lines.append(f"{self.tr('score')}: {result.match_score}")
        if result.match_reason:
            detail_lines.append(f"{self.tr('reason')}: {result.match_reason}")
        if result.source_url:
            detail_lines.append(f"Link: {result.source_url}")
        detail_lines.append("")
        detail_lines.append(f"{self.tr('local_seasons')}:")
        for season, eps in sorted(result.seasons_local.items()):
            detail_lines.append(f"  Season {season:02d}: {len(eps)} {self.tr('episodes')}")
        if result.seasons_expected:
            detail_lines.append("")
            detail_lines.append(f"{self.tr('online_expected')}:")
            for season, eps in sorted(result.seasons_expected.items()):
                have = len(result.seasons_local.get(season, []))
                detail_lines.append(f"  Season {season:02d}: {self.tr('report_i_have')} {have}/{len(eps)}")
        detail_lines.append("")
        detail_lines.append(f"{self.tr('files')}:")
        for f in result.files[:150]:
            detail_lines.append(f"  {f}")
        self.detail_text.delete("1.0", "end")
        self.detail_text.insert("1.0", "\n".join(detail_lines))

        missing_lines = [
            f"{self.tr('missing_for')}: {result.local_name}",
            "=" * 72,
            "",
        ]
        if result.status == "MISSING":
            total_missing = result.missing_count
            missing_lines.append(f"{self.tr('total_missing_episodes')}: {total_missing}")
            missing_lines.append(f"{self.tr('seasons_with_missing')}: {len(result.missing)}")
            missing_lines.append("")
            for season in sorted(result.seasons_expected):
                expected = result.seasons_expected.get(season, [])
                local = result.seasons_local.get(season, [])
                missing = result.missing.get(season, [])
                have = len(local)
                total = len(expected)
                missing_lines.append(f"Season {season:02d}")
                missing_lines.append(f"  {self.tr('have')}: {have}/{total}")
                if missing:
                    missing_lines.append(f"  {self.tr('report_missing_label')} ({len(missing)}): {format_ep_ranges(missing)}")
                else:
                    missing_lines.append(f"  {self.tr('report_missing_label')}: {self.tr('missing_none')}")
                missing_lines.append("")
        elif result.status == "OK":
            missing_lines.append(self.tr("series_complete"))
        else:
            missing_lines.append(self.tr("missing_no_data"))

        self.missing_text.delete("1.0", "end")
        self.missing_text.insert("1.0", "\n".join(missing_lines))

    def get_selected_result(self) -> ShowResult | None:
        return self._get_selected_result()

    def on_tree_right_click(self, event):
        self._show_context_menu(event)

    def open_manual_match_dialog(self):
        item = self.get_selected_result()
        if not item:
            messagebox.showinfo(self.tr("manual_match_title"), self.tr("select_series_first"))
            return

        win = tk.Toplevel(self)
        win.title(f"{self.tr('manual_match')}: {item.local_name}")
        win.geometry("1040x620")
        win.minsize(900, 520)
        win.transient(self)
        win.configure(bg="#0a0f1c")

        query_var = tk.StringVar(value=item.official_name or item.local_name)
        source_var = tk.StringVar(value=self.tr("all_sources"))
        id_var = tk.StringVar()
        id_source_var = tk.StringVar(value="IMDb")
        status_var = tk.StringVar(value=self.tr("manual_search_hint"))
        state = {"running": False, "candidates": [], "after_id": None, "queued": None}

        outer = ttk.Frame(win, padding=12)
        outer.pack(fill="both", expand=True)
        outer.columnconfigure(0, weight=1)
        outer.rowconfigure(2, weight=1)

        ttk.Label(outer, text=f"{self.tr('local_series')}: {item.local_name}{format_local_year(item.local_year)}").grid(row=0, column=0, sticky="w", pady=(0, 8))

        search_bar = ttk.Frame(outer)
        search_bar.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        search_bar.columnconfigure(1, weight=1)
        ttk.Label(search_bar, text=f"{self.tr('name')}:").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=(0, 6))
        query_entry = ttk.Entry(search_bar, textvariable=query_var)
        query_entry.grid(row=0, column=1, sticky="ew", padx=(0, 8), pady=(0, 6))
        source_box = ttk.Combobox(search_bar, textvariable=source_var, values=(self.tr("all_sources"), "TVMaze", "TMDb", "TVDB", "IMDb"), state="readonly", width=12)
        source_box.grid(row=0, column=2, sticky="e", padx=(0, 8), pady=(0, 6))

        ttk.Label(search_bar, text=f"{self.tr('id_link')}:").grid(row=1, column=0, sticky="w", padx=(0, 8))
        id_entry = ttk.Entry(search_bar, textvariable=id_var)
        id_entry.grid(row=1, column=1, sticky="ew", padx=(0, 8))
        id_source_box = ttk.Combobox(search_bar, textvariable=id_source_var, values=("IMDb", "TVDB", "TVMaze", "TMDb"), state="readonly", width=12)
        id_source_box.grid(row=1, column=2, sticky="e", padx=(0, 8))

        cols = ("source", "name", "year", "status", "missing", "score", "reason")
        result_tree = ttk.Treeview(outer, columns=cols, show="headings", height=14)
        result_tree.heading("source", text=self.tr("source"))
        result_tree.heading("name", text=self.tr("name"))
        result_tree.heading("year", text=self.tr("year_short"))
        result_tree.heading("status", text=self.tr("status"))
        result_tree.heading("missing", text=self.tr("missing"))
        result_tree.heading("score", text=self.tr("score"))
        result_tree.heading("reason", text=self.tr("reason"))
        result_tree.column("source", width=80, anchor="center")
        result_tree.column("name", width=260, anchor="w")
        result_tree.column("year", width=70, anchor="center")
        result_tree.column("status", width=90, anchor="center")
        result_tree.column("missing", width=80, anchor="center")
        result_tree.column("score", width=70, anchor="center")
        result_tree.column("reason", width=300, anchor="w")
        result_tree.grid(row=2, column=0, sticky="nsew")
        yscroll = ttk.Scrollbar(outer, orient="vertical", command=result_tree.yview)
        yscroll.grid(row=2, column=1, sticky="ns")
        result_tree.configure(yscrollcommand=yscroll.set)

        bottom = ttk.Frame(outer)
        bottom.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        ttk.Label(bottom, textvariable=status_var).pack(side="left")

        buttons = ttk.Frame(outer)
        buttons.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        close_btn = ttk.Button(buttons, text=self.tr("close"), command=win.destroy)
        close_btn.pack(side="right")

        def selected_candidate() -> ManualMatchCandidate | None:
            sel = result_tree.selection()
            if not sel:
                return None
            try:
                return state["candidates"][int(sel[0])]
            except Exception:
                return None

        def open_selected_link():
            candidate = selected_candidate()
            if candidate and candidate.source_url:
                webbrowser.open(candidate.source_url)

        def apply_selected():
            candidate = selected_candidate()
            if not candidate:
                messagebox.showinfo(self.tr("manual_match_title"), self.tr("select_candidate"))
                return
            inv = inventory_from_result(item)
            updated = make_show_result(
                inv,
                candidate.show_json,
                candidate.source,
                aired_only=self.aired_only_var.get(),
                matched_query=candidate.matched_query,
                match_score=candidate.score,
                match_reason=candidate.reason,
            )
            self._apply_result_update(item, updated, self.tr("matched_manually", local=item.local_name, name=candidate.name))
            win.destroy()

        link_btn = ttk.Button(buttons, text=self.tr("open_link"), command=open_selected_link)
        link_btn.pack(side="right", padx=(0, 8))
        apply_btn = ttk.Button(buttons, text=self.tr("apply_selected"), command=apply_selected)
        apply_btn.pack(side="right", padx=(0, 8))

        def set_busy(is_busy: bool):
            state["running"] = is_busy
            button_state = "disabled" if is_busy else "normal"
            search_btn.configure(state=button_state)
            id_btn.configure(state=button_state)
            apply_btn.configure(state=button_state)
            link_btn.configure(state=button_state)

        def finish_search(candidates: list[ManualMatchCandidate] | None = None, error: str = ""):
            if not win.winfo_exists():
                return
            set_busy(False)
            for iid in result_tree.get_children():
                result_tree.delete(iid)
            if error:
                status_var.set(error)
                return
            state["candidates"] = candidates or []
            for idx, candidate in enumerate(state["candidates"]):
                result_tree.insert(
                    "",
                    "end",
                    iid=str(idx),
                    values=(
                        candidate.source,
                        candidate.name,
                        candidate.year or "-",
                        candidate.status,
                        candidate.missing_count if candidate.status == "MISSING" else (0 if candidate.status == "OK" else "-"),
                        candidate.score,
                        candidate.reason,
                    ),
                )
            if state["candidates"]:
                result_tree.selection_set("0")
                status_var.set(self.tr("found_candidates", count=len(state["candidates"])))
            else:
                status_var.set(self.tr("no_candidates"))
            queued = state.get("queued")
            state["queued"] = None
            if queued:
                win.after(50, lambda: run_search(query=queued[0], source=queued[1], label=queued[2]))

        def run_search(_event=None, query: str | None = None, source: str | None = None, label: str | None = None):
            if state.get("after_id"):
                try:
                    win.after_cancel(state["after_id"])
                except Exception:
                    pass
                state["after_id"] = None
            if state["running"]:
                state["queued"] = (query if query is not None else query_var.get().strip(), source if source is not None else source_var.get(), label)
                status_var.set(self.tr("previous_search_wait"))
                return
            search_query = (query if query is not None else query_var.get()).strip()
            search_source = source if source is not None else source_var.get()
            if not search_query:
                status_var.set(self.tr("enter_name_id"))
                return
            if search_source == "TMDb" and not (self.tmdb_api_key_var.get().strip() or self.tmdb_token_var.get().strip()):
                if not self._ensure_tmdb_credentials():
                    status_var.set(self.tr("tmdb_missing"))
                    return
            if search_source == "TVDB" and not self.tvdb_api_key_var.get().strip():
                status_var.set(self.tr("tvdb_missing"))
                return
            inv = inventory_from_result(item)
            tmdb_api_key = self.tmdb_api_key_var.get().strip()
            tmdb_token = self.tmdb_token_var.get().strip()
            tvdb_api_key = self.tvdb_api_key_var.get().strip()
            tvdb_token = self.tvdb_token
            tvdb_token_created_at = self.tvdb_token_created_at
            aired_only = self.aired_only_var.get()
            set_busy(True)
            status_var.set(label or self.tr("searching_candidates"))

            def worker():
                try:
                    tvdb = TVDBClient(tvdb_api_key, tvdb_token, tvdb_token_created_at)
                    if (is_all_sources_filter(search_source) or search_source == "TVDB") and tvdb.enabled:
                        tvdb.ensure_token()
                        if tvdb.token_refreshed:
                            self.after(0, lambda token=tvdb.token, created=tvdb.token_created_at: self._save_tvdb_token(token, created))
                    found = search_manual_candidates(
                        inv,
                        search_query,
                        search_source,
                        tmdb_api_key,
                        tmdb_token,
                        tvdb_api_key,
                        tvdb.token if tvdb.enabled else "",
                        tvdb.token_created_at if tvdb.enabled else "",
                        aired_only,
                    )
                    self.after(0, lambda: finish_search(found))
                except TVDBAuthError as e:
                    err = str(e)
                    self.after(0, lambda: finish_search(None, err))
                except Exception as e:
                    err = self.tr("error") + f" {e}"
                    self.after(0, lambda: finish_search(None, err))

            threading.Thread(target=worker, daemon=True).start()

        def schedule_live_search(_event=None):
            if state.get("after_id"):
                try:
                    win.after_cancel(state["after_id"])
                except Exception:
                    pass
            query = query_var.get().strip()
            if len(query) < 3:
                status_var.set(self.tr("live_min_chars"))
                return
            state["after_id"] = win.after(
                700,
                lambda: run_search(query=query, source=source_var.get(), label=self.tr("live_searching")),
            )

        def run_id_search(_event=None):
            query = id_var.get().strip()
            if not query:
                status_var.set(self.tr("enter_id_link"))
                return
            run_search(query=query, source=id_source_var.get(), label=self.tr("loading_id"))

        search_btn = ttk.Button(search_bar, text=self.tr("search"), command=run_search)
        search_btn.grid(row=0, column=3, sticky="e")
        id_btn = ttk.Button(search_bar, text=self.tr("load_id"), command=run_id_search)
        id_btn.grid(row=1, column=3, sticky="e")
        query_entry.bind("<KeyRelease>", schedule_live_search)
        source_box.bind("<<ComboboxSelected>>", schedule_live_search)
        query_entry.bind("<Return>", lambda _e: run_search(label=self.tr("searching_candidates")))
        id_entry.bind("<Return>", run_id_search)
        result_tree.bind("<Double-1>", lambda _e: apply_selected())
        query_entry.focus_set()
        query_entry.selection_range(0, "end")

    def _ensure_tmdb_credentials(self) -> bool:
        current_api_key = self.tmdb_api_key_var.get().strip()
        current_token = self.tmdb_token_var.get().strip()
        if current_api_key or current_token:
            return True

        token = simpledialog.askstring(
            self.tr("tmdb_token_prompt_title"),
            self.tr("tmdb_token_prompt"),
            show="*",
            parent=self,
        )
        if token:
            self.tmdb_token_var.set(token.strip())
            self._save_settings()
            return True

        api_key = simpledialog.askstring(
            self.tr("tmdb_api_key_prompt_title"),
            self.tr("tmdb_api_key_prompt"),
            parent=self,
        )
        if api_key:
            self.tmdb_api_key_var.set(api_key.strip())
            self._save_settings()
            return True
        return False

    def check_selected_with_tmdb(self):
        item = self.get_selected_result()
        if not item:
            return
        if not self._ensure_tmdb_credentials():
            self.status_var.set(self.tr("tmdb_missing"))
            return
        tmdb_api_key = self.tmdb_api_key_var.get().strip()
        tmdb_token = self.tmdb_token_var.get().strip()
        aired_only = self.aired_only_var.get()
        self.status_var.set(self.tr("tmdb_check", name=item.local_name))
        threading.Thread(target=self._tmdb_check_worker, args=(item, tmdb_api_key, tmdb_token, aired_only), daemon=True).start()

    def _tmdb_check_worker(self, item: ShowResult, tmdb_api_key: str, tmdb_token: str, aired_only: bool):
        try:
            client = TMDbClient(api_key=tmdb_api_key, token=tmdb_token)
            year = item.local_year or infer_year_from_files(item.files)
            inv = EpisodeInventory(show_name=item.local_name, year=year)
            inv.files = list(item.files)
            inv.episodes = defaultdict(set, {int(s): set(v) for s, v in item.seasons_local.items()})
            inv.guesses = [item.local_name]
            if item.official_name and item.official_name != item.local_name:
                inv.guesses.append(item.official_name)
            if year:
                inv.year_guesses = [year]

            best_show = None
            best_score = -1
            best_reason = ""
            best_query = ""

            for guess in inv.guesses:
                show_json, score, reason = client.fetch_show_with_episodes(guess, local_eps=inv.episodes, year=year)
                if show_json and score > best_score:
                    best_show = show_json
                    best_score = score
                    best_reason = reason
                    best_query = guess

            if not best_show or best_score < 42:
                local_name = item.local_name
                self.after(0, lambda: messagebox.showinfo("TMDb", self.tr("tmdb_no_match", name=local_name)))
                self.after(0, lambda: self.status_var.set(self.tr("tmdb_no_match_status")))
                return

            updated = make_show_result(
                inv,
                best_show,
                "TMDb",
                aired_only=aired_only,
                matched_query=best_query,
                match_score=best_score,
                match_reason=best_reason,
            )

            self.after(0, lambda: self._apply_tmdb_update(item, updated))
        except Exception as e:
            err = self.tr("tmdb_error", error=e)
            status = self.tr("tmdb_error", error=e).replace("\n", " ")
            self.after(0, lambda err=err: messagebox.showerror("TMDb", err))
            self.after(0, lambda status=status: self.status_var.set(status))

    def _apply_tmdb_update(self, item: ShowResult, updated: ShowResult):
        self._apply_result_update(item, updated, self.tr("tmdb_done", name=item.local_name))

    def _recalculate_summary_counts(self):
        if not self.summary:
            return
        self.summary.results.sort(key=lambda r: (0 if r.status == "MISSING" else 1 if r.status in {"UNMATCHED", "EMPTY_DB"} else 2, r.local_name.lower()))
        self.summary.ok_count = sum(1 for r in self.summary.results if r.status == "OK")
        self.summary.missing_count = sum(1 for r in self.summary.results if r.status == "MISSING")
        self.summary.unmatched_count = sum(1 for r in self.summary.results if r.status in {"UNMATCHED", "EMPTY_DB"})

    def _apply_result_update(self, item: ShowResult, updated: ShowResult, status_message: str):
        item.official_name = updated.official_name
        item.official_year = updated.official_year
        item.status = updated.status
        item.source = updated.source
        item.match_score = updated.match_score
        item.match_reason = updated.match_reason
        item.seasons_local = updated.seasons_local
        item.seasons_expected = updated.seasons_expected
        item.missing = updated.missing
        item.matched_query = updated.matched_query
        item.source_url = updated.source_url
        item.files = updated.files

        self.result_map[item.local_name] = item
        self._recalculate_summary_counts()
        self.refresh_views()
        self.status_var.set(status_message)

    def remove_ok_from_view(self):
        self.hide_ok_var.set(True)
        self.refresh_views()

    def save_txt(self):
        if not self.summary:
            messagebox.showinfo(self.tr("no_results_title"), self.tr("run_scan_first"))
            return
        path = filedialog.asksaveasfilename(title=self.tr("save_txt_title"), defaultextension=".txt", filetypes=[("Text", "*.txt"), ("All files", "*.*")])
        if not path:
            return
        content = self.report_box.get("1.0", "end").strip()
        Path(path).write_text(content + "\n", encoding="utf-8")
        self.status_var.set(self.tr("saved", path=path))

    def save_json(self):
        if not self.summary:
            messagebox.showinfo(self.tr("no_results_title"), self.tr("run_scan_first"))
            return
        path = filedialog.asksaveasfilename(title=self.tr("save_json_title"), defaultextension=".json", filetypes=[("JSON", "*.json"), ("All files", "*.*")])
        if not path:
            return
        data = asdict(self.summary)
        if self.remove_ok_from_report_var.get():
            data["results"] = [r for r in data["results"] if r["status"] != "OK"]
        if not self.unparsed_var.get():
            data["unparsed"] = []
        Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        self.status_var.set(self.tr("saved", path=path))

    def copy_missing(self):
        if not self.summary:
            return
        lines = []
        for r in self.summary.results:
            if r.status == "MISSING":
                lines.append(f"{r.local_name}{format_local_year(r.local_year)} -> {summarize_missing(r.missing)}")
        self.clipboard_clear()
        self.clipboard_append("\n".join(lines) if lines else self.tr("no_missing_series"))
        self.status_var.set(self.tr("missing_copied"))

    def copy_unmatched(self):
        if not self.summary:
            return
        lines = [f"{r.local_name}{format_local_year(r.local_year)}" for r in self.summary.results if r.status in {"UNMATCHED", "EMPTY_DB"}]
        self.clipboard_clear()
        self.clipboard_append("\n".join(lines) if lines else self.tr("no_unmatched_series"))
        self.status_var.set(self.tr("unmatched_copied"))

    def mark_selected_series_ok(self):
        result = self._get_selected_result()
        if not result:
            messagebox.showinfo(self.tr("mark_ok"), self.tr("select_series_first"))
            return
        mark_result_as_manually_ok(result)
        self.result_map[result.local_name] = result
        self._recalculate_summary_counts()
        self.refresh_views()
        self.status_var.set(self.tr("marked_ok_status", name=result.local_name))

    def _get_selected_result(self) -> ShowResult | None:
        sel = self.tree.selection()
        if not sel:
            return None
        return self.result_map.get(sel[0])

    def _delete_target_for_result(self, result: ShowResult) -> SeriesDeleteTarget | None:
        scan_root = self.summary.root if self.summary and self.summary.root else self.folder_var.get().strip()
        total_results = len(self.summary.results) if self.summary else 1
        return resolve_series_delete_target(result, scan_root, total_results)

    def _format_delete_target(self, target: SeriesDeleteTarget) -> str:
        if target.kind == "folder":
            return str(target.paths[0])
        preview = [str(path) for path in target.paths[:8]]
        if len(target.paths) > len(preview):
            preview.append(self.tr("more_files", count=len(target.paths) - len(preview)))
        return "\n".join(preview)

    def _remove_deleted_result_from_summary(self, result: ShowResult, target: SeriesDeleteTarget):
        if not self.summary:
            self.result_map.pop(result.local_name, None)
            self.refresh_views()
            return

        target_paths = [normalized_abs_path(path) for path in target.paths]

        def is_deleted_path(path_text: str) -> bool:
            try:
                path = normalized_abs_path(path_text)
            except Exception:
                return False
            for target_path in target_paths:
                if path == target_path or path_is_relative_to(path, target_path):
                    return True
            return False

        self.summary.results = [item for item in self.summary.results if item.local_name != result.local_name]
        self.summary.unparsed = [path for path in self.summary.unparsed if not is_deleted_path(path)]
        self.summary.unparsed_count = len(self.summary.unparsed)
        self.result_map.pop(result.local_name, None)
        self._recalculate_summary_counts()
        self.refresh_views()

    def delete_selected_series_from_disk(self):
        if self.is_scanning:
            messagebox.showinfo(self.tr("delete_active_title"), self.tr("delete_active_msg"))
            return

        result = self._get_selected_result()
        if not result:
            messagebox.showinfo(self.tr("delete_title"), self.tr("delete_select_msg"))
            return

        target = self._delete_target_for_result(result)
        if not target or not target.paths:
            messagebox.showinfo(self.tr("delete_title"), self.tr("delete_no_path"))
            return

        target_text = self._format_delete_target(target)
        if target.kind == "folder":
            action_text = self.tr("delete_folder_action")
        else:
            action_text = self.tr("delete_files_action", count=len(target.paths))

        first_ok = messagebox.askyesno(
            self.tr("delete_title"),
            self.tr("delete_confirm_msg", action=action_text, target=target_text),
            icon="warning",
            parent=self,
        )
        if not first_ok:
            self.status_var.set(self.tr("delete_cancelled"))
            return

        expected_confirmation = "DELETE" if self.language == "en" else "IZBRISI"
        confirm = simpledialog.askstring(
            self.tr("delete_extra_title"),
            self.tr("delete_extra_msg", name=result.local_name),
            parent=self,
        )
        if confirm != expected_confirmation:
            self.status_var.set(self.tr("delete_cancelled_confirm"))
            return

        errors = []
        for path in target.paths:
            try:
                if not path.exists():
                    continue
                if path.is_dir() and not path.is_symlink():
                    shutil.rmtree(path)
                else:
                    path.unlink()
            except Exception as e:
                errors.append(f"{path}: {e}")

        if errors:
            messagebox.showerror(self.tr("delete_failed_title"), "\n".join(errors[:10]), parent=self)
            self.status_var.set(self.tr("delete_failed_status"))
            return

        self._remove_deleted_result_from_summary(result, target)
        self.status_var.set(self.tr("deleted_status", name=result.local_name))

    def open_file_overview(self):
        result = self._get_selected_result()
        if not result:
            messagebox.showinfo(self.tr("file_overview_title"), self.tr("select_series_first"))
            return

        items = build_file_overview_items(result, language=self.language)
        win = tk.Toplevel(self)
        win.title(f"{self.tr('file_overview_title')}: {result.local_name}")
        win.geometry("1180x680")
        win.minsize(920, 520)
        win.transient(self)
        win.configure(bg="#0a0f1c")

        have_count = sum(1 for item in items if item.status == "HAVE")
        missing_count = sum(1 for item in items if item.status == "MISSING")
        unknown_count = sum(1 for item in items if item.status == "UNKNOWN")

        outer = ttk.Frame(win, padding=12)
        outer.pack(fill="both", expand=True)
        outer.columnconfigure(0, weight=1)
        outer.rowconfigure(1, weight=1)

        header = ttk.Frame(outer)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        ttk.Label(
            header,
            text=self.tr(
                "file_summary",
                name=result.local_name,
                year=format_local_year(result.local_year),
                have=have_count,
                missing=missing_count,
                unknown=unknown_count,
            ),
        ).pack(side="left")

        cols = ("status", "episode", "name", "path")
        file_tree = ttk.Treeview(outer, columns=cols, show="headings")
        file_tree.heading("status", text=self.tr("status"))
        file_tree.heading("episode", text=self.tr("episode"))
        file_tree.heading("name", text=self.tr("file_episode"))
        file_tree.heading("path", text=self.tr("path"))
        file_tree.column("status", width=110, anchor="center")
        file_tree.column("episode", width=110, anchor="center")
        file_tree.column("name", width=340, anchor="w")
        file_tree.column("path", width=560, anchor="w")
        file_tree.grid(row=1, column=0, sticky="nsew")
        yscroll = ttk.Scrollbar(outer, orient="vertical", command=file_tree.yview)
        yscroll.grid(row=1, column=1, sticky="ns")
        file_tree.configure(yscrollcommand=yscroll.set)

        file_tree.tag_configure("HAVE", background="#052e16", foreground="#bbf7d0")
        file_tree.tag_configure("MISSING", background="#3f1215", foreground="#fecaca")
        file_tree.tag_configure("UNKNOWN", background="#3b2f0a", foreground="#fde68a")

        for idx, item in enumerate(items):
            file_tree.insert(
                "",
                "end",
                iid=str(idx),
                values=(item.status_label, item.episode_label, item.name, item.path or self.tr("not_on_disk")),
                tags=(item.status,),
            )

        status_var = tk.StringVar(value=self.tr("file_overview_hint"))
        footer = ttk.Frame(outer)
        footer.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        ttk.Label(footer, textvariable=status_var).pack(side="left")

        buttons = ttk.Frame(outer)
        buttons.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(10, 0))

        def selected_item() -> FileOverviewItem | None:
            sel = file_tree.selection()
            if not sel:
                return None
            try:
                return items[int(sel[0])]
            except Exception:
                return None

        def open_selected_path(_event=None):
            item = selected_item()
            if not item:
                status_var.set(self.tr("select_local_file"))
                return
            if not item.path:
                status_var.set(self.tr("missing_no_local_file"))
                return
            try:
                open_path_in_file_manager(item.path)
                status_var.set(self.tr("opened_file_manager"))
            except Exception as e:
                messagebox.showerror(self.tr("error"), self.tr("open_file_manager_error", error=e))

        def open_series_folder():
            if not result.files:
                status_var.set(self.tr("no_local_path"))
                return
            try:
                open_path_in_file_manager(Path(result.files[0]).parent)
                status_var.set(self.tr("opened_series_folder"))
            except Exception as e:
                messagebox.showerror(self.tr("error"), self.tr("open_folder_error", error=e))

        ttk.Button(buttons, text=self.tr("open_selected"), command=open_selected_path).pack(side="left")
        ttk.Button(buttons, text=self.tr("open_series_folder"), command=open_series_folder).pack(side="left", padx=8)
        ttk.Button(buttons, text=self.tr("close"), command=win.destroy).pack(side="right")
        file_tree.bind("<Double-1>", open_selected_path)

    def open_selected_in_browser(self):
        result = self._get_selected_result()
        if not result:
            return
        if result.browser_url:
            webbrowser.open(result.browser_url)
            self.status_var.set(self.tr("open_web_status"))
            return
        query = urllib.parse.quote(result.official_name or result.local_name)
        webbrowser.open(f"https://www.google.com/search?q={query}+tv+series")
        self.status_var.set(self.tr("open_search_status"))

    def copy_selected_link(self):
        result = self._get_selected_result()
        if not result or not result.browser_url:
            return
        self.clipboard_clear()
        self.clipboard_append(result.browser_url)
        self.status_var.set(self.tr("link_copied"))

    def open_selected_folder(self):
        result = self._get_selected_result()
        if not result or not result.files:
            return
        folder = Path(result.files[0]).parent
        try:
            open_path_in_file_manager(folder)
            self.status_var.set(self.tr("folder_opened_manager"))
        except Exception as e:
            messagebox.showerror(self.tr("error"), self.tr("open_folder_error", error=e))


if __name__ == "__main__":
    app = App()
    app.mainloop()
