"""Build the evaluation vault (eval/vault/*.md) and its question file (eval/qa.json) from one table.

Every fact is made up. Each fact has a question that reuses the note's words ("lexical") and one that asks the
same thing in other words ("paraphrase", which word matching alone tends to miss). A few questions have no
answer in any note ("unanswerable"); the right behaviour there is to say so. Run from wiki-rag/:

    python eval/build_eval.py
"""

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent

# note file -> [(note sentence, lexical question, paraphrase question, expected answer text)]
FACTS = {
    "home": [
        ("The gas cylinder is booked every 45 days.", "How often is the gas cylinder booked?",
         "How frequently must I order cooking fuel?", "45"),
        ("The society maintenance of 3200 rupees is paid before the 10th of each month.",
         "When is the society maintenance paid?", "By which day of the month must the building dues be cleared?", "10th"),
        ("The wifi router password is stored in the blue diary.", "Where is the wifi router password stored?",
         "In what place do I look for the internet login secret?", "blue diary"),
        ("The geyser is serviced every June by Mr Kulkarni.", "Who services the geyser?",
         "Which person looks after the water heater each year?", "Kulkarni"),
    ],
    "garden": [
        ("Water the tulsi plant every morning with half a mug of water.", "How much water does the tulsi plant get?",
         "What quantity of liquid goes to the holy basil daily?", "half a mug"),
        ("Pruning of the rose bush is done in February.", "When is the rose bush pruned?",
         "In which month do I cut back the flower shrub?", "February"),
        ("The compost bin is turned every Sunday.", "When is the compost bin turned?",
         "On which day of the week do I stir the kitchen waste heap?", "Sunday"),
        ("The neem oil spray ratio is 5 ml per litre of water.", "What is the neem oil spray ratio?",
         "How much natural pesticide goes into each litre?", "5 ml"),
    ],
    "kitchen": [
        ("Idli batter ferments for 8 hours in summer and 12 hours in winter.",
         "How long does idli batter ferment in winter?", "How many hours should the rice and lentil mix rest when it is cold?", "12 hours"),
        ("Pressure cook the toor dal for 4 whistles.", "How many whistles for toor dal?",
         "For how long, counted in cooker sounds, should the pigeon pea lentils cook?", "4 whistles"),
        ("The spice box has 7 compartments and the hing is in the smallest one.", "Which compartment holds the hing?",
         "Where in the masala container is the asafoetida?", "smallest"),
        ("Ghee is made on the first Saturday of every month.", "When is ghee made?",
         "On which day do I clarify butter?", "first Saturday"),
    ],
    "finance": [
        ("The health insurance premium of 18500 rupees is due on 15 March.", "When is the health insurance premium due?",
         "By what date must I pay the medical cover renewal?", "15 March"),
        ("The credit card statement is generated on the 5th and paid in full by the 22nd.",
         "When is the credit card bill paid?", "By which day do I clear the plastic money dues?", "22nd"),
        ("Income tax advance instalments are due in June, September, December and March.",
         "When are the advance tax instalments due?", "In which months do I pay tax during the year in parts?", "June, September, December"),
        ("The recurring deposit of 5000 rupees matures in October 2027.", "When does the recurring deposit mature?",
         "When will my monthly savings plan at the bank end?", "October 2027"),
    ],
    "travel": [
        ("The Pune to Delhi train leaves at 16:35 from platform 3.", "At what time does the Pune to Delhi train leave?",
         "When does my rail journey to the capital begin?", "16:35"),
        ("Passport renewal is due before 12 August 2028.", "When is passport renewal due?",
         "By which date must my travel document be extended?", "12 August 2028"),
        ("The hotel booking in Jaipur is for 3 nights under the name Joshi.", "For how many nights is the Jaipur hotel booked?",
         "How long is my stay in the pink city?", "3 nights"),
        ("The luggage limit on the flight is 20 kg check-in.", "What is the check-in luggage limit?",
         "How heavy can my suitcase be at the airline counter?", "20 kg"),
    ],
    "study": [
        ("The thesis chapter draft goes to the guide by 30 November.", "When does the thesis chapter draft go to the guide?",
         "What is the deadline for sending my dissertation section to the supervisor?", "30 November"),
        ("Library books are returned every second Friday.", "When are library books returned?",
         "On which day of the fortnight do I give back borrowed volumes?", "second Friday"),
        ("The reading group meets in room 204 at 6 pm.", "Where does the reading group meet?",
         "Which place hosts the book discussion circle?", "room 204"),
        ("Flashcards are reviewed for 20 minutes after dinner.", "How long are flashcards reviewed?",
         "For how many minutes do I go through memory cards at night?", "20 minutes"),
    ],
    "devices": [
        ("The old laptop has 8 GB of RAM and runs the small model with 2 GB free.", "How much RAM does the old laptop have?",
         "What is the memory capacity of my ageing notebook computer?", "8 GB"),
        ("The phone backup runs every night at 2 am on wifi.", "When does the phone backup run?",
         "At what hour is the mobile data copied automatically?", "2 am"),
        ("The printer toner model is TN-2420.", "What is the printer toner model?",
         "Which cartridge code do I buy for the office printer?", "TN-2420"),
        ("The external hard disk is kept in the steel cupboard.", "Where is the external hard disk kept?",
         "In which storage place is the spare drive?", "steel cupboard"),
    ],
    "people": [
        ("Sunita's birthday is on 9 September.", "What date is Sunita's birthday?",
         "When does the annual celebration of Sunita's day of birth fall?", "9 September"),
        ("The plumber's name is Raju and he comes on Tuesdays.", "What is the plumber's name?",
         "Who do I call for leaking taps?", "Raju"),
        ("The anniversary dinner is booked at Spice Garden for 7:30 pm.", "Where is the anniversary dinner booked?",
         "Which restaurant will host our wedding-day meal?", "Spice Garden"),
        ("The school parent meeting is on the last Saturday of the month.", "When is the school parent meeting?",
         "Which weekend day do I visit the teachers each month?", "last Saturday"),
    ],
}

UNANSWERABLE = [
    "What is the phone number of the gas cylinder dealer?",
    "What is the wifi router password?",
    "Who won the cricket match yesterday?",
    "What is the balance in my savings account?",
    "How many whistles for chana dal?",
    "What time does the Mumbai train leave?",
    "In which room is the cooking class held?",
    "What is the name of the electrician?",
]


def build(folder: Path = HERE):
    vault = folder / "vault"
    vault.mkdir(parents=True, exist_ok=True)
    qa = []
    for note, rows in FACTS.items():
        body = [f"# {note.title()}", ""]
        body += [f"- {sentence}" for sentence, _, _, _ in rows]
        (vault / f"{note}.md").write_text("\n".join(body) + "\n", encoding="utf-8")
        for sentence, lexical, paraphrase, answer in rows:
            qa.append({"q": lexical, "source": f"{note}.md", "answer": answer, "kind": "lexical"})
            qa.append({"q": paraphrase, "source": f"{note}.md", "answer": answer, "kind": "paraphrase"})
    for q in UNANSWERABLE:
        qa.append({"q": q, "source": None, "answer": None, "kind": "unanswerable"})
    (folder / "qa.json").write_text(json.dumps(qa, indent=1), encoding="utf-8")
    return qa


if __name__ == "__main__":
    qa = build()
    print("wrote", len(FACTS), "notes and", len(qa), "questions to", HERE)
