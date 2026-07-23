# panel.py — panel routing: which grid a tap opens, and which scope it writes to.
from __future__ import annotations
from . import choices, config, labels, msgmap, panelmenu, registry

_STALE = "Essa mensagem é antiga demais — retoma a sessão com /resume."
# One message per dimension. A single generic "sem controle de esforço" for any empty list is
# what made an unreachable opencode binary surface as an effort complaint on the model button.
_EMPTY = {"h": "Nenhum harness disponível.",
          "m": "Não consegui listar os modelos desse harness.",
          "e": "Esse modelo não expõe controle de esforço."}
# Harness stores as `backend` because that is the key the session registry has always used for
# "who owns this lineage"; the word on screen is harness (choices.LABELS).
_KEY = {"h": "backend", "m": "model", "e": "effort"}


async def _redraw(query, markup, state: str | None = None) -> None:
    """Every render records which state the message now shows, so a later selection knows where
    to return to (Lucas, 2026-07-23: a choice should step back one level, like `‹`)."""
    if state is not None:
        mid = query.message.message_id
        msgmap.remember_panel(mid, state)
    await query.edit_message_reply_markup(reply_markup=markup)


async def _to_root(query, scope: str) -> None:
    current = registry.mode_for(scope)
    markup = panelmenu.root_markup(scope, current)
    await _redraw(query, markup, "p:root")


async def _set_mode(query, scope: str, target: str) -> None:
    """Optimistic: answer + redraw before persisting, so the bracket moves at once instead of
    after the config write."""
    await query.answer(f"modo: {target}")
    current = registry.mode_for(scope)
    if target != current:
        markup = panelmenu.root_markup(scope, target)
        await _redraw(query, markup, "p:root")
        registry.set_mode(scope, target)


def _values_of(scope: str, dim: str) -> tuple[list[str], list]:
    """(values, extra buttons). Only the model picker carries an `all` escape into the provider
    drill-down, and only when the catalogue is bigger than the shortlist."""
    values, deep = choices.values_for(scope, dim)
    extra: list = []
    if deep:
        button = panelmenu.all_button()
        extra = [button]
    return values, extra


async def _dimension(query, scope: str, dim: str, expanded: bool, page: int) -> None:
    values, extra = _values_of(scope, dim)
    if not values:
        await query.answer(_EMPTY[dim], show_alert=True)
        return
    key = _KEY[dim]
    current = registry.setting_for(scope, key)
    await query.answer()
    markup = panelmenu.values_markup(dim, values, current, expanded=expanded,
                                     page=page, extra=extra)
    state = f"p:x:{dim}:{page}" if expanded else f"p:d:{dim}"
    await _redraw(query, markup, state)


def _drop_stale_effort(scope: str) -> None:
    """Changing model or harness can invalidate the effort: the vocabularies differ per model,
    so an effort the new one never declared would build an argv its CLI rejects."""
    current = registry.setting_for(scope, "effort")
    if current:
        values = choices.effort_values(scope)
        if current not in values:
            registry.set_setting(scope, "effort", None)


def apply(scope: str, dim: str, value: str) -> str:
    """Persist one choice and return the toast that explains it. Harness only ever reaches here
    in the NEW scope — a live session's menu does not offer it (SPECS AD-11)."""
    key = _KEY[dim]
    registry.set_setting(scope, key, value)
    if dim == "h":
        registry.set_setting(scope, "model", None)
    if dim in ("h", "m"):
        _drop_stale_effort(scope)
    shown = labels.model_label(value) if dim == "m" else value
    return f"{choices.LABELS[dim]}: {shown}"


async def _choose(query, scope: str, dim: str, value: str) -> None:
    """Apply, then redraw the state the tap came from — you see the bracket move without losing
    your place in the list. Only a harness change forces a step back, because it invalidates the
    model and effort the deeper states were showing."""
    note = apply(scope, dim, value)
    await query.answer(note)
    mid = query.message.message_id
    state = "p:menu" if dim == "h" else msgmap.panel_state(mid)
    parts = state.split(":", 3)
    await _route(query, scope, parts)


async def _open(query, markup, state: str) -> None:
    await query.answer()
    await _redraw(query, markup, state)


async def _route(query, scope: str, parts: list[str]) -> None:
    head = parts[1]
    if head == "menu":
        markup = panelmenu.menu_markup(scope)
        await _open(query, markup, "p:menu")
    elif head == "root":
        await query.answer()
        await _to_root(query, scope)
    elif head == "mode":
        await _set_mode(query, scope, parts[2])
    elif head == "d":
        await _dimension(query, scope, parts[2], False, 0)
    elif head == "x":
        page = int(parts[3])
        await _dimension(query, scope, parts[2], True, page)
    elif head == "s":
        await _choose(query, scope, parts[2], parts[3])
    elif head == "g":
        markup = panelmenu.providers_markup(scope)
        await _open(query, markup, "p:g")
    elif head == "p":
        page = int(parts[3])
        markup = panelmenu.provider_markup(scope, parts[2], page)
        await _open(query, markup, f"p:p:{parts[2]}:{page}")


async def handle_callback(update, context) -> None:
    """Panel taps carry no scope: the keyboard always sits on a message the bot remembers — an
    anchored session or a /new config bubble — so `scope_for_message` resolves it and the whole
    64-byte callback_data budget stays free for values (P2 D4)."""
    query = update.callback_query
    if query is None or query.message is None:
        return
    if query.message.chat_id != config.allowed_chat_id():
        return
    scope = msgmap.scope_for_message(query.message.message_id)
    if scope is None:
        await query.answer(_STALE, show_alert=True)
        return
    data = query.data or ""
    parts = data.split(":", 3)
    await _route(query, scope, parts)
