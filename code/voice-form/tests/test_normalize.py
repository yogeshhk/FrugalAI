import datetime as dt

import pytest

from voiceform import normalize as nz

TODAY = dt.date(2026, 10, 31)


@pytest.mark.parametrize("spoken, digits", [
    ("एकशे चाळीस बाय नव्वद", "140 बाय 90"),
    ("दोन शे चाळीस", "240"),
    ("एक सौ बीस बाय अस्सी", "120 बाय 80"),
    ("मकान नंबर एक सौ पांच", "मकान नंबर 105"),
    ("साडे दहा", "10.5"),
    ("साढ़े आठ", "8.5"),
    ("दहा पॉइंट पाच", "10.5"),
    ("लोहाच्या शंभर गोळ्या", "लोहाच्या 100 गोळ्या"),
    ("आयरन की सौ गोलियां", "आयरन की 100 गोलियां"),
    ("दो हज़ार पांच", "2005"),
    ("दीडशे", "150"),
    ("वय चोवीस वर्षे", "वय 24 वर्षे"),
    ("उम्र उनतीस", "उम्र 29"),
    ("वय एकोणतीस", "वय 29"),
    ("चव्वेचाळीस", "44"),
    ("नव्व्याण्णव", "99"),
    ("निन्यानबे", "99"),
    ("१४०/९०", "140/90"),
])
def test_number_words(spoken, digits):
    assert nz.normalize_text(spoken) == digits


def test_spoken_digits_stay_separate_and_make_a_phone_number():
    text = nz.normalize_text("मोबाईल नऊ आठ दोन तीन चार पाच सहा सात आठ नऊ")
    assert text == "मोबाईल 9 8 2 3 4 5 6 7 8 9"
    assert nz.parse_phone(text) == "9823456789"


def test_ambiguous_words_are_left_alone_without_a_number_next_to_them():
    assert nz.normalize_text("एक महिला आली") == "एक महिला आली"
    assert nz.normalize_text("गोलियां दो") == "गोलियां दो"
    assert nz.normalize_text("शून्य एक दो तीन") == "0 1 2 3"


def test_fold_ignores_nukta_and_chandrabindu():
    assert nz.fold("पाँच") == nz.fold("पांच")
    assert nz.fold("वज़न") == nz.fold("वजन")
    assert nz.fold("खेड़ा") == nz.fold("खेडा")


@pytest.mark.parametrize("value, expected", [
    ("140/90", (140, 90)), ("140 by 90", (140, 90)), ("एकशे वीस बाय ऐंशी", (120, 80)),
    ({"systolic": 130, "diastolic": 85}, (130, 85)), ("140 पर 90", (140, 90)), ("nothing", None),
])
def test_bp(value, expected):
    assert nz.parse_bp(value) == expected


@pytest.mark.parametrize("value, expected", [
    ("9823456789", "9823456789"), ("+91 98234 56789", "9823456789"), ("09823456789", "9823456789"),
    ("12345", None), ("1234567890", None),
])
def test_phone(value, expected):
    assert nz.parse_phone(value) == expected


@pytest.mark.parametrize("value, expected", [
    ("2026-11-12", dt.date(2026, 11, 12)),
    ("12 नोव्हेंबर", dt.date(2026, 11, 12)),
    ("बारा नोव्हेंबरला", dt.date(2026, 11, 12)),
    ("पंधरा डिसेंबर", dt.date(2026, 12, 15)),
    ("बारह नवंबर", dt.date(2026, 11, 12)),
    ("12 November 2027", dt.date(2027, 11, 12)),
    ("12/11/2026", dt.date(2026, 11, 12)),
    ("उद्या", dt.date(2026, 11, 1)),
    ("परवा", dt.date(2026, 11, 2)),
    ("5 ऑक्टोबर", dt.date(2027, 10, 5)),  # already past this year, so next year
])
def test_dates(value, expected):
    assert nz.parse_date(value, TODAY) == expected


def test_hindi_kal_is_ambiguous():
    with pytest.raises(nz.DateAmbiguous):
        nz.parse_date("कल", TODAY)


def test_bool():
    assert nz.parse_bool("वॉरंटी आहे") is True
    assert nz.parse_bool("वारंटी नहीं है") is False
    assert nz.parse_bool(True) is True
    assert nz.parse_bool("maybe") is None


def test_options_longest_synonym_wins():
    product = {"water_pump": ["पंप", "मोटर"], "sprayer": ["फवारणी पंप", "स्प्रे पंप"]}
    assert nz.match_option("फवारणी पंप गळतो", product) == "sprayer"
    assert nz.match_option("पंप", product) == "water_pump"
    assert nz.match_option("sprayer", product) == "sprayer"
    urgency = {"high": ["जल्दी", "तुरंत"], "low": ["जल्दी नहीं"]}
    assert nz.match_option("जल्दी नहीं है", urgency) == "low"
    assert nz.match_option("tractor", product) is None
