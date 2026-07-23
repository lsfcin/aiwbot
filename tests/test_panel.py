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


def test_every_row_is_exactly_five_cells(store):
    """The whole geometry: Telegram divides a row evenly and has no colspan, so cells are only
    square — and only aligned between rows — if every row holds the same count."""
    markups = [panelmenu.root_markup("s1", "build"),
               panelmenu.menu_markup("s1"),
               panelmenu.menu_markup(registry.NEW),
               panelmenu.values_markup("m", _FAVS, None, extra=[panelmenu.all_button()]),
               panelmenu.values_markup("m", _FAVS, None, expanded=True),
               panelmenu.providers_markup("s1"),
               panelmenu.provider_markup("s1", "big", 0)]
    for markup in markups:
        for row in markup.inline_keyboard:
            assert len(row) == keyboard.COLS


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


def test_collapsed_picker_that_fits_offers_no_expander(store):
    markup = panelmenu.values_markup("e", ["low", "high", "max"], "high")
    assert "···" not in _texts(markup)
    assert "[ high ]" in _texts(markup)


def test_expander_and_collapser_share_the_same_cell(store):
    """`···` and `−` both sit in row 0's right chrome, so the control never moves under your
    thumb between the two states."""
    collapsed = panelmenu.values_markup("m", _FAVS, None)
    expanded = panelmenu.values_markup("m", _FAVS, None, expanded=True)
    assert collapsed.inline_keyboard[0][-1].text == "···"
    assert expanded.inline_keyboard[0][-1].text == "−"


def test_all_escape_rides_the_last_page_only(store):
    extra = [panelmenu.all_button()]
    first = _texts(panelmenu.values_markup("m", [f"m{i}" for i in range(20)], None,
                                           expanded=True, page=0, extra=extra))
    last = _texts(panelmenu.values_markup("m", [f"m{i}" for i in range(20)], None,
                                          expanded=True, page=2, extra=extra))
    assert "all" not in first
    assert "all" in last


def test_pager_arrows_sit_in_the_chrome_columns(store):
    markup = panelmenu.provider_markup("s1", "big", 1)
    rows = _labels(markup)
    assert rows[-1][0] == "‹"
    assert rows[-1][-1] == "›"
    assert rows[1][0] == "2/3"


def test_arrows_park_at_the_ends_of_the_range(store):
    first = _data(panelmenu.provider_markup("s1", "big", 0))
    last = _data(panelmenu.provider_markup("s1", "big", 2))
    assert "p:p:big:1" in first
    assert "p:p:big:-1" not in first
    assert "p:p:big:3" not in last


def test_filler_cells_are_inert(store):
    markup = panelmenu.menu_markup("s1")
    fillers = [b for row in markup.inline_keyboard for b in row if b.text == keyboard.BLANK]
    assert fillers
    for button in fillers:
        assert button.callback_data == keyboard.NOOP


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
