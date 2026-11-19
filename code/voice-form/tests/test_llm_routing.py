from voiceform import config
from voiceform.llm import LLM


def test_dhir_has_its_own_server_and_the_others_use_lm_studio():
    assert config.url_for(config.DHIR_MODEL) == config.DHIR_URL
    assert config.url_for(config.DEFAULT_LLM) == config.LLM_URL
    assert config.url_for("gemma-2-2b-it") == config.LLM_URL


def test_llm_client_picks_the_url_from_the_model_id():
    assert LLM(config.DHIR_MODEL).url == config.DHIR_URL.rstrip("/")
    assert LLM(config.DEFAULT_LLM).url == config.LLM_URL.rstrip("/")
    assert LLM(config.DHIR_MODEL, url="http://localhost:9999/v1/").url == "http://localhost:9999/v1"


def test_default_model_stays_qwen():
    assert "qwen" in config.DEFAULT_LLM.lower()


def test_page_uses_dhir_for_marathi_when_its_server_runs():
    assert config.model_for_lang("mr") == config.DHIR_MODEL
    assert config.model_for_lang("hi") == config.DEFAULT_LLM


def test_page_falls_back_to_qwen_when_the_dhir_server_is_not_running():
    only_lm_studio = lambda model: model != config.DHIR_MODEL
    assert config.model_for_lang("mr", only_lm_studio) == config.DEFAULT_LLM
    assert config.model_for_lang("hi", only_lm_studio) == config.DEFAULT_LLM
