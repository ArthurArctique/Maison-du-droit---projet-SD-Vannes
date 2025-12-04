@echo off
:: Se placer dans le dossier où se trouve ce fichier
cd /d "%~dp0"

:: Message pour rassurer l'utilisateur
echo Lancement de l'application MDD Reporting...
echo Veuillez patienter, le navigateur va s'ouvrir.
echo.
echo NE FERMEZ PAS CETTE FENETRE NOIRE tant que vous utilisez l'application.

:: Lancer le script Python
python app.py

:: Si ça plante, on fait une pause pour voir l'erreur
pause