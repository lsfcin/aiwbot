# test_f2_papercuts.py — the F2 batch: phrase tone, flat glyphs, the reply anchor, and the
# "bote" mishearing. Each choice below was made by Lucas against a live Telegram prototype
# (2026-07-26), so these tests pin decisions, not guesses.
from frontend import phrases
from frontend.startword import strip_prefix
from frontend.format import answer_block, CONTINUES

_BANKS = [phrases.CAPTURE_ACKS, phrases.WORKING_PHRASES, phrases.NEW_EMPTY_PROMPT_PHRASES,
          phrases.ERROR_PHRASES, phrases.UNKNOWN_CMD_PHRASES,
          phrases.SESSION_LIVE_ELSEWHERE_PHRASES, phrases.RESUME_EMPTY_PHRASES,
          phrases.RESUME_ANCHOR_PHRASES, phrases.TRANSCRIBE_FAIL_PHRASES]


# --- tone: lowercase, no trailing period (Lucas: "B") ---

def test_no_bank_phrase_ends_in_a_period():
    for bank in _BANKS:
        for phrase in bank:
            assert not phrase.endswith("."), phrase


def test_no_bank_phrase_starts_with_a_capital():
    """A chat ack is an aside, not a sentence. Placeholders like {cmd} are exempt — what
    they interpolate is a command name, not prose."""
    for bank in _BANKS:
        for phrase in bank:
            first = phrase[0]
            assert first == first.lower(), phrase


# --- glyphs: flat, not gradient emoji (Lucas: "B") ---

def test_status_phrases_carry_no_gradient_emoji():
    for phrase in phrases.WORKING_PHRASES:
        assert "⏳" not in phrase
        assert phrase.startswith("· ")


# --- the reply anchor leads, so Telegram's quote preview names the session (Lucas: "B") ---

def test_the_first_line_names_the_session_a_reply_continues():
    block = answer_block("corpo da resposta", "abc12345", "titulo da sessao")
    first = block.split("\n")[0]
    assert first.startswith(CONTINUES)
    assert "[ABC]" in first
    assert "TITULO DA SESSAO" in first


def test_the_session_is_named_once_not_twice():
    block = answer_block("corpo", "abc12345", "titulo", provider="claude")
    assert block.count("[ABC]") == 1


def test_an_answer_without_a_session_has_no_anchor_line():
    block = answer_block("corpo", None, None, provider="claude")
    assert CONTINUES not in block
    assert block.split("\n")[0] == "corpo"


# --- "bote": the mishearing that swallowed the session-start intent ---

def test_the_misheard_bote_starts_a_session_like_bot_does():
    assert strip_prefix("bote roda os testes") == "roda os testes"
    assert strip_prefix("bote, roda os testes") == "roda os testes"


def test_the_real_start_word_still_works():
    assert strip_prefix("bot roda os testes") == "roda os testes"
    assert strip_prefix("bot, roda os testes") == "roda os testes"
    assert strip_prefix("BOT roda") == "roda"


def test_a_word_merely_beginning_with_bot_is_not_a_start_word():
    assert strip_prefix("botar isso no inbox") is None
    assert strip_prefix("botequim amanha") is None
    assert strip_prefix("nada a ver") is None
