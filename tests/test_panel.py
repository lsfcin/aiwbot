# test_panel.py — free unit test: the morphing settings panel — states, labels, switch semantics.
import pytest
from backend import Capabilities
from frontend import config, panel, panelmenu, registry

_CAPS = Capabilities(modes=["build", "plan"],
                     favourites=["opencode/a", "opencode/b"],
                     groups={"opencode": ["opencode/a", "opencode/b"],
                             "big": [f"big/m{i}" for i in range(14)]})


class _Fake:
    def capabilities(self):
        return _CAPS

    def efforts(self, model=None):
        return ["low", "high"] if model else []


@pytest.fixture
def store(monkeypatch):
    data = {"sessions": {"s1": {"backend": "claude", "title": "t"}}}
    monkeypatch.setattr(config, "load_config", lambda: data)
    monkeypatch.setattr(config, "save_config", lambda **u: data.update(u) or data)
    monkeypatch.setattr(panelmenu, "get_backend", lambda name: _Fake())
    return data


def _labels(markup):
    labels = []
    for row in markup.inline_keyboard:
        for button in row:
            labels.append(button.text)
    return labels


def test_root_carries_the_mode_row_and_one_gear(store):
    markup = panel.root_markup("s1", "build")
    assert [b.text for b in markup.inline_keyboard[0]] == ["[ BUILD ]", "PLAN"]
    gear = markup.inline_keyboard[1][0]
    assert gear.text == "⚙ claude"
    assert gear.callback_data == "p:menu"


def test_gear_summarizes_the_target_not_the_lineage(store):
    registry.set_setting("s1", "next_backend", "opencode")
    registry.set_setting("s1", "model", "nvidia/z-ai/glm-5.2")
    registry.set_setting("s1", "effort", "high")
    assert panelmenu.summary("s1") == "⚙ opencode · glm-5.2 · high"


def test_model_state_shows_favourites_and_offers_the_drill_down(store):
    markup = panelmenu.model_markup("s1")
    labels = _labels(markup)
    assert labels[:2] == ["a", "b"]
    assert "mais…" in labels


def test_selected_model_is_bracketed(store):
    registry.set_setting("s1", "model", "opencode/b")
    labels = _labels(panelmenu.model_markup("s1"))
    assert "[ b ]" in labels


def test_drill_down_pages_a_big_provider(store):
    markup = panelmenu.group_page_markup("s1", "big", 0)
    labels = _labels(markup)
    assert "6 / 14" in labels
    values = [b.callback_data for row in markup.inline_keyboard for b in row]
    assert "p:s:m:big/m0" in values
    assert "p:s:m:big/m6" not in values


def test_paging_forward_then_the_arrow_parks_at_the_end(store):
    last = panelmenu.group_page_markup("s1", "big", 12)
    data = [b.callback_data for row in last.inline_keyboard for b in row]
    assert "noop:" in data          # › has nowhere left to go
    assert "p:g:big:6" in data      # ‹ still steps back


def test_callback_data_never_spends_bytes_on_a_session_id(store):
    markup = panelmenu.group_page_markup("s1", "big", 0)
    for row in markup.inline_keyboard:
        for button in row:
            assert "s1" not in button.callback_data
            assert len(button.callback_data.encode()) <= 64


def test_switching_backend_clears_the_provider_specific_knobs(store):
    registry.set_setting("s1", "model", "opus")
    registry.set_setting("s1", "effort", "max")
    registry.switch_backend("s1", "opencode")
    assert registry.target_backend("s1") == "opencode"
    assert registry.setting_for("s1", "model") is None
    assert registry.setting_for("s1", "effort") is None


def test_switching_back_to_the_owner_cancels_the_pending_switch(store):
    registry.switch_backend("s1", "opencode")
    registry.switch_backend("s1", "claude")
    assert registry.setting_for("s1", "next_backend") is None
    assert registry.target_backend("s1") == "claude"


def test_a_model_change_drops_an_effort_the_new_model_never_declared(store):
    registry.set_setting("s1", "effort", "max")
    panel._apply("s1", "m", "opencode/a")
    assert registry.setting_for("s1", "effort") is None


def test_an_effort_the_new_model_still_declares_survives(store):
    registry.set_setting("s1", "effort", "high")
    panel._apply("s1", "m", "opencode/a")
    assert registry.setting_for("s1", "effort") == "high"


def test_unknown_session_writes_nothing(store):
    registry.set_setting("ghost", "model", "opus")
    assert "ghost" not in store["sessions"]
