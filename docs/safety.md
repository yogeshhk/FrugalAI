# Safety: health-related recipes

Applies to the ASHA-worker assistant and any other recipe whose output could influence a health decision.

## Position
The assistant is decision support for a trained community health worker. It is not a diagnosis tool, does
not replace a clinician, and is not deployed in the field until the steps below are done.

## Rules for any health recipe
1. **No diagnosis or dosing.** The assistant does not name a condition as a conclusion and does not state
   medicine doses.
2. **Escalate, do not reassure.** If the input suggests an emergency or danger sign, the reply is to refer
   the patient to a facility. The list of danger signs and the referral wording come from official
   guidance and a clinical reviewer, not from the model or from us.
3. **Say "I do not know".** When the supplied guidance does not cover the question, the assistant says so.
4. **Answer from supplied guidance only.** Use retrieval over reviewed, cited material (for example
   government health worker guidelines). Show the source with every answer.
5. **Language safety.** Marathi and Hindi quality is measured on an evaluation set before use. A model
   that fails the set is not used, however fluent it sounds.
6. **Data stays local.** No patient data leaves the device. Logs contain no personal data by default.
7. **Review before use.** A clinical reviewer signs off the guidance corpus, the evaluation set and the
   refusal behaviour. Record who reviewed what and when.

## Before any field use
- Check the legal and regulatory position for software that supports clinical decisions in India. This
  repository does not give legal advice, and the position has not been checked yet.
- Run a pilot with a partner organisation, with informed consent and a way to report problems.

## What this repository does today
Only documentation. The earlier ASHA-assistant stub (plan and evaluation format) was set aside and is not being
worked on. No health content has been written and no model has been evaluated for it.
