@echo off
:: Frugal AI seminar: compile the Presentation and the CheatSheet (the c in -cp cleans the auxiliary files).
texify -cp --pdf Main_Seminar_AI_Frugal_Presentation.tex
texify -cp --pdf Main_Seminar_AI_Frugal_CheatSheet.tex
