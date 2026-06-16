"""Triere editoriala optionala cu Gemini API.

Activata DOAR daca exista secretul GEMINI_API_KEY. Produce un brief editorial
scurt + conexiuni cross-sursa + unghiuri de investigatie.
"""
from __future__ import annotations

import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

from .config import env
from .models import Item
from .util import log

MODEL = "gemini-2.5-flash"

SYSTEM = (
    "Esti asistent de documentare pentru un editor de investigatii cu acoperire "
    "pe Republica Moldova. Primesti o lista de semnale brute agregate azi din "
    "surse internationale si presa de investigatie. Sarcina ta: separa semnalul "
    "de zgomot. Raspunde in romana, concis, fara floricele. Format:\n"
    "1) BRIEF (max 5 puncte): ce conteaza azi si DE CE.\n"
    "2) CONEXIUNI: nume/entitati care apar in mai multe surse simultan.\n"
    "3) UNGHIURI: 2-3 piste concrete de verificat, fiecare cu primul pas.\n"
    "Nu inventa. Daca un semnal e slab, spune-o."
)

def brief(items: list[Item], max_items: int = 30) -> str | None:
    api_key = env("GEMINI_API_KEY")
    if not api_key:
        return None

    top = sorted(items, key=lambda i: i.score, reverse=True)[:max_items]
    if not top:
        return None

    lines = []
    for it in top:
        ents = ", ".join(it.entities) if it.entities else "-"
        lines.append(
            f"[{it.source}] {it.title} | entitati: {ents} | "
            f"scor: {it.score} | {it.date} | {it.url}"
        )
    user = "Semnale de azi:\n\n" + "\n".join(lines)

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(MODEL, system_instruction=SYSTEM)
        response = model.generate_content(
            user,
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=1200,
            ),
            safety_settings={
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            }
        )
        text = response.text.strip()
        return text or None
    except Exception as exc:
        log.warning("  triage ESEC: %s", exc)
        return None
