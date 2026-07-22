# test_mode.py — free unit test: plan↔build toggle button + sticky per-session mode state.
import pytest
from frontend import mode, sessions, config


def test_toggle_markup_build_shows_flip_to_plan():
    markup = mode.toggle_markup("sid-x", "build")
    button = markup.inline_keyboard[0][0]
    assert button.text == "🧭 → plan"
    assert button.callback_data == "mode:sid-x"


def test_toggle_markup_plan_shows_flip_to_build():
    markup = mode.toggle_markup("sid-y", "plan")
    button = markup.inline_keyboard[0][0]
    assert button.text == "🔨 → build"
    assert button.callback_data == "mode:sid-y"


@pytest.fixture
def mem_config(monkeypatch):
    store = {"sessions": {"sid-1": {"backend": "claude", "title": "t"}}}
    monkeypatch.setattr(config, "load_config", lambda: store)
    monkeypatch.setattr(config, "save_config", lambda **u: store.update(u) or store)
    return store


def test_mode_for_defaults_build_when_unset(mem_config):
    assert sessions.mode_for("sid-1") == "build"


def test_set_mode_persists_and_is_read_back(mem_config):
    sessions.set_mode("sid-1", "plan")
    assert sessions.mode_for("sid-1") == "plan"


def test_set_mode_ignores_unknown_session(mem_config):
    sessions.set_mode("ghost", "plan")
    assert "ghost" not in mem_config["sessions"]
