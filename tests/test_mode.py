# test_mode.py — free unit test: plan↔build toggle button + sticky per-session mode state.
import pytest
from frontend import mode, registry, config


def test_toggle_markup_build_selected_brackets_build():
    markup = mode.toggle_markup("sid-x", "build")
    row = markup.inline_keyboard[0]
    assert [b.text for b in row] == ["[ BUILD ]", "PLAN"]
    assert [b.callback_data for b in row] == ["mode:build:sid-x", "mode:plan:sid-x"]


def test_toggle_markup_plan_selected_brackets_plan():
    markup = mode.toggle_markup("sid-y", "plan")
    row = markup.inline_keyboard[0]
    assert [b.text for b in row] == ["BUILD", "[ PLAN ]"]
    assert [b.callback_data for b in row] == ["mode:build:sid-y", "mode:plan:sid-y"]


@pytest.fixture
def mem_config(monkeypatch):
    store = {"sessions": {"sid-1": {"backend": "claude", "title": "t"}}}
    monkeypatch.setattr(config, "load_config", lambda: store)
    monkeypatch.setattr(config, "save_config", lambda **u: store.update(u) or store)
    return store


def test_mode_for_defaults_build_when_unset(mem_config):
    assert registry.mode_for("sid-1") == "build"


def test_set_mode_persists_and_is_read_back(mem_config):
    registry.set_mode("sid-1", "plan")
    assert registry.mode_for("sid-1") == "plan"


def test_set_mode_ignores_unknown_session(mem_config):
    registry.set_mode("ghost", "plan")
    assert "ghost" not in mem_config["sessions"]
