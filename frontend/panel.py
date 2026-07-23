# panel.py — anchor keyboard + its callbacks: mode row, gear, and the morphing settings panel.
from __future__ import annotations
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from . import config, mode, panelmenu, registry

_STALE = "Essa mensagem é antiga demais — retoma a sessão com /resume."
_NO_EFFORT = "Esse modelo não expõe controle de esforço."
_SWITCH = "{name}: a próxima mensagem abre uma sessão NOVA nesse backend (modelo e esforço zerados)."
_SAME = "Já é {name}."
_KEYS = {"m": "modelo", "e": "esforço"}


def root_markup(session_id: str, current_mode: str) -> InlineKeyboardMarkup:
    """What an answer or a re-anchor carries: the mode row plus one button that opens the
    panel. Everything else lives behind that tap, so the bubble stays light (P2 D1)."""
    rows = [mode.toggle_row(session_id, current_mode)]
    label = panelmenu.summary(session_id)
    gear = InlineKeyboardButton(label, callback_data="p:menu")
    rows.append([gear])
    return InlineKeyboardMarkup(rows)


async def _show(query, sid: str, markup: InlineKeyboardMarkup) -> None:
    await query.answer()
    await query.edit_message_reply_markup(reply_markup=markup)


async def _back_to_root(query, sid: str) -> None:
    current = registry.mode_for(sid)
    markup = root_markup(sid, current)
    await query.edit_message_reply_markup(reply_markup=markup)


async def _set_mode(query, data: str) -> None:
    """Optimistic: answer + redraw before persisting, so the bracket moves at once instead of
    after the config write. The session id rides in the data here (pre-panel format, kept so
    anchors already sitting in the chat keep working)."""
    parts = data.split(":", 2)
    target = parts[1]
    sid = parts[2]
    await query.answer(f"modo: {target}")
    current = registry.mode_for(sid)
    if target != current:
        markup = root_markup(sid, target)
        await query.edit_message_reply_markup(reply_markup=markup)
        registry.set_mode(sid, target)


async def _dimension(query, sid: str, dim: str) -> None:
    if dim == "b":
        markup = panelmenu.backend_markup(sid)
    elif dim == "m":
        markup = panelmenu.model_markup(sid)
    else:
        values = panelmenu.efforts_for(sid)
        if not values:
            await query.answer(_NO_EFFORT, show_alert=True)
            return
        markup = panelmenu.effort_markup(sid, values)
    await _show(query, sid, markup)


def _drop_stale_effort(sid: str) -> None:
    """A model change can invalidate the effort: the vocabularies differ per model, so an
    effort the new model never declared would build an argv its CLI rejects."""
    current = registry.setting_for(sid, "effort")
    if current:
        values = panelmenu.efforts_for(sid)
        if current not in values:
            registry.set_setting(sid, "effort", None)


def _switch(sid: str, name: str) -> str:
    owner = registry.backend_for(sid)
    registry.switch_backend(sid, name)
    note = _SAME.format(name=name) if name == owner else _SWITCH.format(name=name)
    return note


def _apply(sid: str, dim: str, value: str) -> str:
    """Persist one panel choice and return the toast that explains it."""
    if dim == "b":
        note = _switch(sid, value)
    else:
        key = "model" if dim == "m" else "effort"
        registry.set_setting(sid, key, value)
        if dim == "m":
            _drop_stale_effort(sid)
        note = f"{_KEYS[dim]}: {value}"
    return note


async def _choose(query, sid: str, dim: str, value: str) -> None:
    note = _apply(sid, dim, value)
    alert = dim == "b"
    await query.answer(note, show_alert=alert)
    await _back_to_root(query, sid)


async def _group(query, sid: str, parts: list[str]) -> None:
    """`p:g` opens the provider list; `p:g:<provider>:<offset>` opens one page of its models."""
    if len(parts) < 4:
        markup = panelmenu.group_markup(sid)
    else:
        name = parts[2]
        offset = int(parts[3])
        markup = panelmenu.group_page_markup(sid, name, offset)
    await _show(query, sid, markup)


async def _route(query, sid: str, parts: list[str]) -> None:
    head = parts[1]
    if head == "menu":
        markup = panelmenu.menu_markup()
        await _show(query, sid, markup)
    elif head == "root":
        await query.answer()
        await _back_to_root(query, sid)
    elif head == "d":
        await _dimension(query, sid, parts[2])
    elif head == "s":
        await _choose(query, sid, parts[2], parts[3])
    elif head == "g":
        await _group(query, sid, parts)


async def handle_callback(update, context) -> None:
    """Panel taps carry no session id: the panel always edits the anchor message, whose id
    the reply map already resolves, leaving the whole 64-byte budget for values (P2 D4)."""
    query = update.callback_query
    if query is None or query.message is None:
        return
    if query.message.chat_id != config.allowed_chat_id():
        return
    data = query.data or ""
    if data.startswith("mode:"):
        await _set_mode(query, data)
        return
    sid = registry.session_for_reply(query.message.message_id)
    if sid is None:
        await query.answer(_STALE, show_alert=True)
        return
    parts = data.split(":", 3)
    await _route(query, sid, parts)
