# select
> The picker keyboards: what a scope may be offered, drawn as rows of buttons.
> spec: ../SPEC.md

<!-- routing:start -->
## Routing

| File | API | Description |
|------|-----|-------------|
| [`__init__.py`](__init__.py) | — | **facade** — __init__.py — facade: the picker keyboards: what a scope may be offered, drawn as rows of buttons. |
| [`choices.py`](choices.py) | `harness_values`, `model_values`, `groups`, `effort_values`, `preferred` | choices.py — what a scope may be offered: the backends' declarations, asked per dimension. |
| [`keyboard.py`](keyboard.py) | `per_row`, `cell`, `segment`, `chunk`, `framed` | keyboard.py — inline-keyboard primitives: rows of at most four, framed by the panel's controls. |
| [`labels.py`](labels.py) | `provider_short`, `model_label` | labels.py — fit a model id into a button: provider prefix, then compress only if it overflows. |
| [`panel.py`](panel.py) | `apply`, `handle_callback` | panel.py — panel routing: which grid a tap opens, and which scope it writes to. |
| [`panelmenu.py`](panelmenu.py) | `root_markup`, `menu_markup`, `values_markup`, `all_button`, `providers_markup` | panelmenu.py — the panel's states drawn as keyboards: mode row, dimension menu, value pickers. |
<!-- routing:end -->
