#!/usr/bin/env python3
import json
from pathlib import Path

path = Path(__file__).resolve().parents[1] / "werweiss" / "data" / "questions.json"
data = json.loads(path.read_text(encoding="utf-8"))
question = input("Frage: ").strip()
category = input("Kategorie: ").strip() or "Allgemein"
difficulty = input("Schwierigkeit easy/medium/hard: ").strip() or "easy"
answers = [input(f"Antwort {i+1}: ").strip() for i in range(4)]
correct = int(input("Richtige Antwort Nummer 1-4: ").strip()) - 1
data.append({"question": question, "answers": answers, "correct": correct, "category": category, "difficulty": difficulty})
path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
print("Gespeichert. Lösche ggf. ~/.local/share/werweiss/werweiss.db für Neuimport.")
