# test_panel.py — free unit test: panel effects — scopes, applying a choice, hidden dims.
from frontend import choices, keyboard, panel, panelmenu, registry
from .panelkit import FAVS as _FAVS, labels as _labels, texts as _texts, data as _data



def test_effort_disappears_when_the_model_declares_none(store):
    """A button whose only possible answer is "this model has none" is worse than no button."""
    registry.set_setting("s1", "model", None)
    assert choices.menu_dims("s1") == ["m"]
    assert "effort" not in _texts(panelmenu.menu_markup("s1"))
    registry.set_setting("s1", "model", "opencode/a")
    assert choices.menu_dims("s1") == ["m", "e"]

def test_root_is_plus_then_the_mode_segments(store):
    rows = _labels(panelmenu.root_markup("s1", "build"))
    assert rows[0][:3] == ["+", "[ BUILD ]", "PLAN"]
    assert len(rows) == 1

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
