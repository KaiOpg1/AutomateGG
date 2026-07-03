🤖 Discord Automator (Top.gg Voter)
Ein leistungsstarkes, auf Python basierendes Automatisierungstool, das mithilfe von Patchright und Chrome DevTools Protocol (CDP) den Voting-Prozess auf Top.gg für Discord-Accounts verwaltet und automatisiert. 🚀

✨ Features
🌐 Automatisierte Sitzungsverwaltung: Startet Chrome-Instanzen in isolierten Profilen für jeden Account.

⏳ Intelligentes Cooldown-System: Überwacht Wartezeiten pro Account, um API-Limits oder Sperren zu minimieren.

👻 Stealth-Modus: Unterstützt einen Headless-Modus sowie gezielte Tarnung der Browser-Fingerprints (via AutomationControlled Flags).

🛡️ Fehlertoleranz: Automatische Fehlererkennung bei Logins, Captchas oder bereits erfolgten Votes.

🧹 Bereinigung: Automatisches Aufräumen von Cache und Profildaten nach jeder Sitzung.

🛠️ Voraussetzungen
🐍 Python 3.8+

🌐 Google Chrome (Installationspfad ggf. in der Konfiguration anpassen)

📦 patchright & asyncio

📥 Installation
Repository klonen:

Bash
git clone https://github.com/KaiOpg1/AutomateGG.git
cd discord-automator
Abhängigkeiten installieren:

Bash
pip install -r requirements.txt
playwright install chromium
