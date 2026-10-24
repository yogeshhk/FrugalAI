@echo off
rem Extraction on the reference text, tune set only, every route and model. Run from code\voice-form.
rem Held-out lines are run separately, once, after tuning is finished (run_heldout.bat).
set PY=python
for %%L in (mr hi) do (
  %PY% -m voiceform eval-extract --lang %%L --route rules --set tune
  %PY% -m voiceform eval-extract --lang %%L --route direct --model qwen/qwen3-1.7b --set tune
  %PY% -m voiceform eval-extract --lang %%L --route direct --model gemma-2-2b-it --set tune
  %PY% -m voiceform eval-extract --lang %%L --route translate --model qwen/qwen3-1.7b --set tune
)
%PY% -m voiceform report
