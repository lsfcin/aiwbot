# phrases.py — phrase banks (natural-language variants, picked at random per message) + help text.
from __future__ import annotations
import random

CAPTURE_ACKS = [
    "Guardado em brain/INBOX.md.",
    "Adicionado ao INBOX.md.",
    "Salvo em brain/INBOX.md.",
    "Enviado para o INBOX.md",
    "Registrado em brain/INBOX.md.",
]
WORKING_PHRASES = [
    "⏳ trabalhando…",
    "⏳ rodando…",
    "⏳ processando…",
    "⏳ um instante…",
    "⏳ pensando…",
]
NEW_EMPTY_PROMPT_PHRASES = [
    "Sessão nova — ajusta abaixo se quiser e responde essa mensagem com o prompt.",
    "Beleza: configura nos botões e responde aqui com o que a sessão deve fazer.",
    "Sessão nova. Os botões mudam harness/model/effort; responde essa mensagem com o prompt.",
]
ERROR_PHRASES = [
    "Deu erro: {e}",
    "Algo quebrou: {e}",
    "Erro ao rodar: {e}",
    "Falhou: {e}",
    "Rolou um erro: {e}",
]
UNKNOWN_CMD_PHRASES = [
    "Não conheço {cmd}. Manda /help pra ver os comandos.",
    "{cmd} não existe. Confere o /help.",
    "Comando {cmd} desconhecido — veja /help.",
    "Não entendi {cmd}. Tenta /help.",
    "{cmd}? Não conheço. /help lista o que dá pra fazer.",
]
SESSION_LIVE_ELSEWHERE_PHRASES = [
    "Essa sessão tá aberta ao vivo em outro lugar (VSCode?) agora — fecha lá e tenta de novo.",
    "Não consigo continuar: essa sessão já tá em uso em outro lugar. Fecha lá primeiro.",
    "Essa sessão parece estar aberta em outra janela — só dá pra seguir por aqui quando ela não estiver aberta em nenhum outro lugar.",
]
RESUME_EMPTY_PHRASES = [
    "Nenhuma sessão pra retomar ainda.",
    "Sem sessões no histórico — começa uma com /new.",
    "Ainda não tem sessão nenhuma pra retomar.",
]
RESUME_ANCHOR_PHRASES = [
    "Sessão retomada — responde aqui pra continuar.",
    "Pronto, essa é a ativa. Responde essa mensagem pra seguir.",
    "Retomei essa sessão. Manda a próxima como resposta a essa mensagem.",
]

HELP_TEXT = (
    "<b>Comandos</b>\n"
    "<code>/new</code> [--backend claude|opencode] &lt;prompt&gt; — inicia sessão nova, já fica selecionada\n"
    "<code>/resume</code> [busca] — lista sessões recentes pra retomar (filtra por título se você passar um termo)\n"
    "<code>/help</code> — essa mensagem\n\n"
    "Texto, foto, áudio ou documento mandado sem <code>/</code> vai direto pro brain/INBOX.md.\n\n"
    "Responder a qualquer mensagem de sessão continua aquela sessão — não precisa digitar id.\n\n"
    "O botão <code>+</code> embaixo de cada resposta abre model e effort da sessão. "
    "O harness (claude/opencode) só dá pra escolher em sessão nova — uma sessão não troca de "
    "harness, porque nenhum dos dois importa o contexto do outro.\n\n"
    "Sessão nova herda harness/model/effort da última interação."
)


def pick(bank: list[str], **kw) -> str:
    text = random.choice(bank)
    result = text
    if kw:
        result = text.format(**kw)
    return result
