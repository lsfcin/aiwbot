# test_panel.py — free unit test: the 5-column panel grid — geometry, states, scopes.
import pytest
from backend import Capabilities
from frontend import config, keyboard, panel, panelmenu, registry

_FAVS = ["opencode/a", "opencode/b", "opencode/c", "opencode/d"]
_CAPS = Capabilities(modes=["build", "plan"], favourites=_FAVS,
                     groups={"opencode": _FAVS, "big": [f"big/m{i}" for i in range(20)]})


class _Fake:
    def capabilities(self):
        return _CAPS

    def efforts(self, model=None):
        return ["low", "high", "max"] if model else []


@pytest.fixture
def store(monkeypatch):
    data = {"sessions": {"s1": {"backend": "opencode", "title": "t"}}, "defaults": {}}
    monkeypatch.setattr(config, "load_config", lambda: data)
    monkeypatch.setattr(config, "save_config", lambda **u: data.update(u) or data)
    monkeypatch.setattr(panelmenu, "get_backend", lambda name: _Fake())
    return data


def _labels(markup):
    out = []
    for row in markup.inline_keyboard:
        line = [button.text for button in row]
        out.append(line)
    return out


def _texts(markup):
    flat = []
    for row in markup.inline_keyboard:
        for button in row:
            flat.append(button.text)
    return flat


def _data(markup):
    flat = []
    for row in markup.inline_keyboard:
        for button in row:
            flat.append(button.callback_data)
    return flat


def _states(scope="s1"):
    return [panelmenu.root_markup(scope, "build"),
            panelmenu.menu_markup(scope),
            panelmenu.menu_markup(registry.NEW),
            panelmenu.values_markup("m", _FAVS, None, extra=[panelmenu.all_button()]),
            panelmenu.values_markup("m", _FAVS, None, expanded=True),
            panelmenu.providers_markup(scope),
            panelmenu.provider_markup(scope, "big", 0)]


def test_no_row_exceeds_four_buttons(store):
    for markup in _states():
        for row in markup.inline_keyboard:
            assert 1 <= len(row) <= keyboard.MAX_PER_ROW


def test_first_button_opens_or_closes_and_last_expands_or_collapses(store):
    """The panel's one layout rule, so the two controls are always where the thumb expects."""
    for markup in _states():
        flat = _texts(markup)
        assert flat[0] in ("+", "x")
    for markup in _states()[3:]:
        assert _texts(markup)[-1] in ("···", "−")


def test_rows_split_evenly_rather_than_greedily(store):
    """Width is shared inside a row, so a greedy 4+1 would stretch the lone button across the
    whole bubble."""
    rows = keyboard.chunk([object()] * 5)
    assert [len(row) for row in rows] == [3, 2]


def test_root_is_plus_then_the_mode_segments(store):
    rows = _labels(panelmenu.root_markup("s1", "build"))
    assert rows[0][:3] == ["+", "[ BUILD ]", "PLAN"]
    assert len(rows) == 1


def test_collapsed_picker_is_always_one_row(store):
    """Four favourites plus an `all` escape still collapse to a single row — everything past
    the first three lives behind `···`."""
    markup = panelmenu.values_markup("m", _FAVS, None, extra=[panelmenu.all_button()])
    assert len(markup.inline_keyboard) == 1
    assert _texts(markup)[0] == "x"
    assert _texts(markup)[-1] == "···"


def test_collapsed_picker_that_fits_shows_three_and_no_expander(store):
    markup = panelmenu.values_markup("e", ["low", "high", "max"], "high")
    assert "···" not in _texts(markup)
    assert "[ high ]" in _texts(markup)
    assert len(markup.inline_keyboard[0]) == keyboard.MAX_PER_ROW


def test_the_selected_value_is_never_cut_off(store):
    """Collapsed shows two of five, so the selection is pinned first — a picker that hides what
    is currently set is worse than one that reorders."""
    markup = panelmenu.values_markup("e", ["low", "medium", "high", "xhigh", "max"], "max")
    assert "[ max ]" in _texts(markup)


def test_a_value_chosen_in_the_drill_down_still_shows_in_the_shortlist(store):
    """openrouter/... is not among the favourites, but it is what is set, so it leads the row."""
    markup = panelmenu.values_markup("m", _FAVS, "big/m7", extra=[panelmenu.all_button()])
    assert "[ m7 ]" in _texts(markup)


def test_expander_and_collapser_are_both_the_last_button(store):
    collapsed = panelmenu.values_markup("m", _FAVS, None)
    expanded = panelmenu.values_markup("m", _FAVS, None, expanded=True)
    assert _texts(collapsed)[-1] == "···"
    assert _texts(expanded)[-1] == "−"


def test_all_escape_rides_the_last_page_only(store):
    extra = [panelmenu.all_button()]
    values = [f"m{i}" for i in range(30)]
    first = _texts(panelmenu.values_markup("m", values, None, expanded=True, page=0, extra=extra))
    last = _texts(panelmenu.values_markup("m", values, None, expanded=True, page=2, extra=extra))
    assert "all" not in first
    assert "all" in last


def test_pager_is_its_own_row_so_the_collapser_stays_last(store):
    markup = panelmenu.provider_markup("s1", "big", 1)
    last = _labels(markup)[-1]
    assert last == ["‹", "2/2", "›", "−"]


def test_arrows_park_at_the_ends_of_the_range(store):
    first = _data(panelmenu.provider_markup("s1", "big", 0))
    last = _data(panelmenu.provider_markup("s1", "big", 1))
    assert "p:p:big:1" in first
    assert "p:p:big:-1" not in first
    assert "p:p:big:2" not in last


def test_session_menu_hides_harness_but_new_offers_it(store):
    """A running lineage cannot change harness — no CLI imports the other's transcript — so
    offering it would be a button that cannot mean anything (SPECS AD-11)."""
    assert "harness" not in _texts(panelmenu.menu_markup("s1"))
    assert "harness" in _texts(panelmenu.menu_markup(registry.NEW))


def test_new_scope_writes_defaults_not_a_session(store):
    panel.apply(registry.NEW, "h", "claude")
    panel.apply(registry.NEW, "m", "opus")
    assert store["defaults"]["backend"] == "claude"
    assert store["defaults"]["model"] == "opus"
    assert "model" not in store["sessions"]["s1"]


def test_choosing_a_harness_clears_the_model_it_cannot_mean(store):
    panel.apply(registry.NEW, "m", "opencode/a")
    panel.apply(registry.NEW, "h", "claude")
    assert registry.setting_for(registry.NEW, "model") is None


def test_a_model_change_drops_an_effort_the_new_model_never_declared(store):
    registry.set_setting("s1", "effort", "xhigh")
    panel.apply("s1", "m", "opencode/a")
    assert registry.setting_for("s1", "effort") is None


def test_an_effort_the_new_model_still_declares_survives(store):
    registry.set_setting("s1", "effort", "high")
    panel.apply("s1", "m", "opencode/a")
    assert registry.setting_for("s1", "effort") == "high"


def test_callback_data_never_spends_bytes_on_the_scope(store):
    """The keyboard always sits on a message the bot remembers, so the scope is resolved from
    the message id and all 64 bytes stay available for values."""
    markup = panelmenu.provider_markup("s1", "big", 0)
    for value in _data(markup):
        assert "s1" not in value
        assert len(value.encode()) <= 64


def test_provider_labels_drop_the_qualifier_nobody_reads(store):
    assert panelmenu._provider_label("alibaba-coding-plan") == "alibaba"
    assert panelmenu._provider_label("nvidia") == "nvidia"
