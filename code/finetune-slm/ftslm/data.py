"""Synthetic helpline-message dataset: route a short message to one of six intents.

Everything is generated from templates and slot words with a fixed seed, so there is no licence question and
the data never has to be downloaded. The split is built to test generalisation, not memory:

  train    templates TRAIN_T,  slot words SLOTS_TRAIN
  test_iid templates TRAIN_T,  slot words SLOTS_TEST  (same phrasings, new crops, places, tools)
  test_ood templates TEST_T,   slot words SLOTS_TEST  (phrasings the model never saw during training)

A small share of messages gets a typo or lower-casing so the task is not purely clean text.
"""

import json
import random
from pathlib import Path

LABELS = ["weather", "price", "pest", "scheme", "repair", "other"]

SLOTS_TRAIN = {
    "crop": ["wheat", "rice", "onion", "cotton", "soybean", "tomato", "maize", "sugarcane"],
    "place": ["Pune", "Nashik", "Nagpur", "Satara", "Latur", "Solapur"],
    "tool": ["tractor", "water pump", "sprayer", "tiller"],
    "day": ["today", "tomorrow", "this week", "on Friday"],
    "scheme": ["crop insurance", "the farm loan scheme", "the drip irrigation subsidy", "the pension scheme"],
    "name": ["Ramesh", "Sunita", "Ganesh", "Meena", "Vijay", "Kavita"],
}
SLOTS_TEST = {
    "crop": ["jowar", "groundnut", "chilli", "banana", "turmeric", "grapes", "pomegranate", "bajra"],
    "place": ["Kolhapur", "Jalgaon", "Amravati", "Beed", "Dhule", "Sangli"],
    "tool": ["thresher", "harvester", "seed drill", "chaff cutter"],
    "day": ["this weekend", "next Monday", "tonight", "in two days"],
    "scheme": ["the solar pump subsidy", "the seed subsidy", "the kisan credit card", "the cold storage grant"],
    "name": ["Arjun", "Lata", "Mohan", "Pooja", "Santosh", "Rekha"],
}

# {intent: [templates]}. Placeholders: {crop} {place} {tool} {day} {scheme} {name}
TRAIN_T = {
    "weather": [
        "Will it rain in {place} {day}?",
        "What is the weather forecast for {place} {day}?",
        "Is a storm coming to {place} {day}?",
        "How hot will it be in {place} {day}?",
        "Should I irrigate my {crop} field, will it rain {day}?",
    ],
    "price": [
        "What is the price of {crop} in {place} market today?",
        "How much is {crop} selling for in {place}?",
        "What rate is the mandi giving for {crop}?",
        "Tell me today's {crop} rate at {place}.",
        "Is the {crop} price going up {day}?",
    ],
    "pest": [
        "My {crop} leaves have yellow spots, what disease is this?",
        "There are insects eating my {crop} plants, what should I spray?",
        "How do I stop worms in my {crop} crop?",
        "White powder on my {crop} leaves, what is it?",
        "My {crop} plants are wilting and the roots look rotten.",
    ],
    "scheme": [
        "How do I apply for {scheme}?",
        "Am I eligible for {scheme}?",
        "What documents do I need for {scheme}?",
        "Where is the form for {scheme}?",
        "When does the application for {scheme} close?",
    ],
    "repair": [
        "My {tool} will not start, what should I check?",
        "The {tool} is making a loud noise, who can repair it?",
        "How do I fix a leaking {tool}?",
        "Where can I get my {tool} serviced near {place}?",
        "My {tool} stopped working {day}, please help.",
    ],
    "other": [
        "Good morning, this is {name}.",
        "Thank you for your help, {name} here.",
        "{name} here, can you speak Marathi?",
        "Hi, I am {name}, what is the capital of India?",
        "This is {name}, please tell me a joke.",
        "{name} calling, what time does the office open?",
        "Who built this service? Regards, {name}.",
    ],
}

TEST_T = {
    "weather": [
        "Any chance of showers around {place} {day}?",
        "Please give me the {place} temperature outlook for {day}.",
        "Heavy wind expected at {place} {day}, is that right?",
        "I want to spray the {crop}, will the sky stay clear {day}?",
    ],
    "price": [
        "Current market value of {crop} at {place}, please.",
        "What would a quintal of {crop} fetch at {place}?",
        "Are traders paying more for {crop} {day}?",
        "Cost per kilo of {crop} right now?",
    ],
    "pest": [
        "Something is attacking my {crop}, the leaves are curling and sticky.",
        "Small black bugs are all over my {crop}, which medicine works?",
        "Brown patches are spreading across my {crop} field.",
        "My {crop} fruit is rotting from inside, what is the cause?",
    ],
    "scheme": [
        "Can a small farmer get {scheme}?",
        "Tell me about the benefits of {scheme}.",
        "Who should I meet at the block office about {scheme}?",
        "How long does {scheme} take to get approved?",
    ],
    "repair": [
        "The engine of my {tool} keeps stalling, any advice?",
        "Belt on the {tool} has snapped, where do I buy a new one near {place}?",
        "Is it worth fixing an old {tool} or should I buy new?",
        "Smoke is coming from my {tool}, what now?",
    ],
    "other": [
        "Hello there, {name} speaking!",
        "Hi, is anyone free to chat? - {name}",
        "{name} wants something interesting to read.",
        "What is your name? Mine is {name}.",
        "Which languages do you support, asked {name}.",
        "Okay thanks, bye from {name}.",
    ],
}


def _noise(text: str, rng: random.Random) -> str:
    """Lower-case some messages and drop one letter from a long word in others."""
    r = rng.random()
    if r < 0.15:
        return text.lower()
    if r < 0.30:
        words = text.split()
        idx = [i for i, w in enumerate(words) if len(w) > 5 and w.isalpha()]
        if idx:
            i = rng.choice(idx)
            j = rng.randrange(1, len(words[i]) - 1)
            words[i] = words[i][:j] + words[i][j + 1:]
        return " ".join(words)
    return text


def _fill(template: str, slots: dict, rng: random.Random) -> str:
    return template.format(**{k: rng.choice(v) for k, v in slots.items()})


def make_split(templates: dict, slots: dict, n_per_label: int, seed: int) -> list:
    rng = random.Random(seed)
    rows, seen = [], set()
    for label in LABELS:
        tries = 0
        count = 0
        while count < n_per_label and tries < n_per_label * 50:
            tries += 1
            text = _noise(_fill(rng.choice(templates[label]), slots, rng), rng)
            if text in seen:
                continue
            seen.add(text)
            rows.append({"text": text, "label": label})
            count += 1
    rng.shuffle(rows)
    return rows


def build_all(n_train: int = 80, n_test: int = 25) -> dict:
    """n_train and n_test are messages per label (so 6x as many rows)."""
    return {
        "train": make_split(TRAIN_T, SLOTS_TRAIN, n_train, seed=1),
        "test_iid": make_split(TRAIN_T, SLOTS_TEST, n_test, seed=2),
        "test_ood": make_split(TEST_T, SLOTS_TEST, n_test, seed=3),
    }


def write_all(folder: Path, **kw) -> dict:
    folder.mkdir(parents=True, exist_ok=True)
    data = build_all(**kw)
    for name, rows in data.items():
        with open(folder / f"{name}.jsonl", "w", encoding="utf-8") as fh:
            for r in rows:
                fh.write(json.dumps(r) + "\n")
    return data


def read(folder: Path, name: str) -> list:
    with open(Path(folder) / f"{name}.jsonl", encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def leakage(data: dict) -> int:
    """Number of test messages that also appear verbatim in train (should be 0 for a fair test)."""
    train = {r["text"] for r in data["train"]}
    return sum(1 for k in ("test_iid", "test_ood") for r in data[k] if r["text"] in train)
