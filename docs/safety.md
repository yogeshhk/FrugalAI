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
Documentation, plus one health-related data-entry form. The earlier ASHA-assistant stub (plan and evaluation
format) was set aside and is not being worked on. No health guidance has been written, and no model has been
evaluated for giving health advice.

The one health-related item is the simplified antenatal home-visit form in `code/voice-form/forms/asha_anc_visit.yaml`
(synthetic data only, not an official form). It is **data entry only**: the app records what the worker says and
saves it only after a person confirms. It gives no advice, no diagnosis and no dosing, and it does not judge
danger signs. Two small language models (Qwen3 1.7B and Gemma 2 2B) were scored on how well they fill the form fields
from spoken Marathi and Hindi, which measures field capture, not health content. The form carries a
`data_entry_only: true` flag, but no code enforces it; the rule holds because the form contains no advice logic.
Any change that adds advice, danger-sign checks or guidance to it falls under the rules above and needs the
review in rule 7 first.
