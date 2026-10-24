# Post 6: voice to form (DRAFT, hold)

HOLD: post only after the demo runs on the author's real Marathi and Hindi recordings. Check every sentence against
`code/voice-form/README.md` and `results/RESULTS.md` first, and rewrite the "what I found" paragraph from the real
results.

## Post

An ASHA worker visits a pregnant woman. Afterwards she fills a form: name, age, village, weeks of pregnancy, blood pressure, weight, the next visit date. On a small phone screen. Often in a second language. Often standing up.

What if she could just say it?

"रेखा जाधव, वय एकोणतीस, गाव शिरूर, सोळा आठवडे..."

That's the fourth Frugal AI project. You speak in Marathi or Hindi, and the form fills itself on a laptop with no internet.

Here's how the work is split. A small speech model writes down what was said. Plain code handles everything code is good at: numbers spoken as words, "एकशे चाळीस बाय नव्वद" for blood pressure, phone numbers said digit by digit, dates like "उद्या". A small language model only decides which words belong to which field, and it has to quote the words each value came from. If the quote isn't really in what was said, the field turns amber. Nothing is saved until the worker checks and confirms.

The same pipeline fills a voter-roll enumeration form and a service ticket for a technician. A new form is one short file, no new code.

[WHAT I FOUND: rewrite from the real results, including what did not work]

It's a proof of concept, built on synthetic data, and it gives no medical advice of any kind. The obvious next steps are open: an Android version, more languages, real field noise, many speakers. Each one could be an internship, a paper, or the start of a product.

github.com/yogeshhk/FrugalAI (code/voice-form)

#FrugalAI #SpeechRecognition #Marathi #Hindi #DigitalPublicGoods

## Banner
Title: "Speak the form"
Scene: A health worker in a simple sari with a cloth bag, sitting on a charpai outside a village home, speaking into
a basic phone; small paper form fields float beside her and fill in with handwriting as she speaks.
Alt text: Hand-drawn illustration of a village health worker speaking into a phone while a paper form fills itself
beside her, titled "Speak the form".
