import asyncio
import os
import json
import time
import shutil
import subprocess
import random
from patchright.async_api import async_playwright


EINSTELLUNGEN = [
"Token 1",
"Token 2", 
"USW"
]
BASE_PROXY = {
    "server": "proxy 123.123.123.123",  
    "username": "USERNAME 123123123123",
    "password": "okasdopkasdop123"
}

BROWSER_COOLDOWN_FILE = "browser_cooldowns.json"
USER_DATA_DIR_BASE = "discord_profiles"
TWELVE_HOURS = 12 * 60 * 60

def save_browser_cooldown(token, timestamp):
    data = {}
    if os.path.exists(BROWSER_COOLDOWN_FILE):
        try:
            with open(BROWSER_COOLDOWN_FILE, "r") as f: data = json.load(f)
        except: pass
    data[token_str_key(token)] = timestamp
    with open(BROWSER_COOLDOWN_FILE, "w") as f: json.dump(data, f)

def get_browser_cooldown(token):
    if not os.path.exists(BROWSER_COOLDOWN_FILE): return 0
    try:
        with open(BROWSER_COOLDOWN_FILE, "r") as f: data = json.load(f)
        return data.get(token_str_key(token), 0)
    except: return 0

def clear_browser_cooldowns():
    if os.path.exists(BROWSER_COOLDOWN_FILE):
        try: os.remove(BROWSER_COOLDOWN_FILE)
        except: pass
    
    if os.path.exists(USER_DATA_DIR_BASE):
        try:
            shutil.rmtree(USER_DATA_DIR_BASE)
            print("[System] Config gelöscht! Cooldowns und Profile wurden vollständig zurückgesetzt.")
        except Exception as e:
            print(f"[Fehler] Konnte Profile nicht löschen: {e}")
    else:
        print("[System] Config gelöscht!")

def token_str_key(token):
    return token.split(".")[0] if "." in token else token[:20]

async def simuliere_sitzung(token, index, headless):
    last_use = get_browser_cooldown(token)
    remaining = (last_use + TWELVE_HOURS) - time.time()
    if remaining > 0:
        hours_left = round(remaining / 3600, 1)
        print(f"[Skipped] Token gesperrt für weitere {hours_left} Stunden.")
        return
    
    chrome_profile_path = f"C:\\Users\\shaii\\Desktop\\ChromeDebugProfile_{index}"
    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    
    chrome_args = [
        chrome_path,
        "--remote-debugging-port=9222",
        "--start-maximized",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-infobars",
        "--disable-blink-features=AutomationControlled",
        f"--user-data-dir={chrome_profile_path}"
    ]

    if headless:
        print(f"[System] Starte Instanz von Chrome für Account {index+1}...")
        startupinfo.wShowWindow = 0  # SW_HIDE: Macht das Fenster unsichtbar
        chrome_args.append("--headless=new")
        chrome_args.append("--window-size=1920,1080")
    else:
        print(f"[System] Starte Instanz von Chrome für Account {index+1}...")
        startupinfo.wShowWindow = 7  # SW_SHOWMINNOACTIVE: Minimiert im Hintergrund starten

    chrome_process = subprocess.Popen(chrome_args, startupinfo=startupinfo, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    await asyncio.sleep(3)

    async with async_playwright() as p:
        try:
            print(f"[Info] Verbinde Patchright mit lokalem Chrome...")
            browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
            context = browser.contexts[0]
            page = context.pages[0] if context.pages else await context.new_page()
            
           
            await page.set_extra_http_headers({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            })
            
          
            if not headless:
                try:
                    client = await page.context.new_cdp_session(page)
                    await client.send("Browser.setWindowBounds", {
                        "windowId": (await client.send("Browser.getWindowForTarget"))["windowId"],
                        "bounds": {"windowState": "maximized"}
                    })
                except: pass
            
            # 1. Discord Login
            print(f"[Info] Initialisiere Discord-Verbindung...")
            await page.goto("https://discord.com/login", timeout=25000)
            await asyncio.sleep(2)
            
            # 2. Token-Injektion
            print(f"[Info] Starte Intervall-Token-Injektion...")
            await page.evaluate(f"""
                (function() {{
                    const token = "{token}";
                    const loginInterval = setInterval(() => {{
                        try {{
                            const iframe = document.createElement('iframe');
                            document.body.appendChild(iframe);
                            iframe.contentWindow.localStorage.token = `"${{token}}"`;
                        }} catch(e) {{}}
                    }}, 50);
                    
                    setTimeout(() => {{
                        clearInterval(loginInterval);
                        location.href = "https://discord.com/channels/@me";
                    }}, 500);
                }})();
            """)
            
            print(f"[Info] Aktualisiere Sitzung und warte auf Dashboard...")
            try:
                await page.wait_for_url("**/channels/@me", timeout=20000)
                await asyncio.sleep(4)
            except Exception: pass
            
            # 3. Login-Status prüfen
            if "login" in page.url or page.url in ["https://discord.com/", "https://discord.com/login"]:
                sperr_dauer = 9999 * 3600
                save_browser_cooldown(token, time.time() - (TWELVE_HOURS - sperr_dauer))
                print(f"[System] Token {index+1} wurde permanent (9999h) gesperrt.")
                return 
            else:
                print(f"[🟢] Discord Login - Erfolgreich eingeloggt!")
            
            # 4. Weiterleitung zu Top.gg
            print(f"[Info] Navigiere zu Top.gg...")
            try: 
                await page.goto("https://www.google.de", timeout=5000)
                await asyncio.sleep(1)
            except: pass
            
            await page.goto("https://top.gg/auth/login?redir=%2Fbot%2F458302301187342336%2Fvote", timeout=25000)
            await asyncio.sleep(4)

            # Cookie-Banner automatisch akzeptieren
            try:
                cookie_button = page.locator("button:has-text('Akzeptieren'), button:has-text('Accept')")
                if await cookie_button.is_visible():
                    await cookie_button.click(timeout=3000)
                    print("[Info] Cookie-Banner erfolgreich akzeptiert.")
                    await asyncio.sleep(1)
            except: pass

            # Prüfen, ob bereits gevotet wurde
            if await page.locator("text=You have already voted").is_visible():
                print("[🔴] Dieser Account hat bereits gevotet! Setze 12h Cooldown...")
                save_browser_cooldown(token, time.time())
                return

            
            print("[Info] Klicke auf 'Login with Discord'...")
            try:
                await page.click("text=Login with Discord", timeout=8000, force=True)
            except Exception as e:
                print(f"[Hinweis] Konnte den Login-Button nicht automatisch klicken: {e}")

            
            print("[Info] Warte auf Discord-Autorisierung (Authorize)...")
            try:
                await page.wait_for_url("**/oauth2/authorize*", timeout=20000)
                await asyncio.sleep(2)
                
                authorize_button = page.locator("button:has-text('Authorize'), button:has-text('Autorisieren'), .lookFilled-1GseHa")
                await authorize_button.first.wait_for(state="visible", timeout=12000)
                await authorize_button.first.click(force=True)
                print("[🟢] Discord erfolgreich autorisiert!")
            except Exception as e:
                print(f"[Hinweis] Automatische Autorisierung übersprungen oder fehlgeschlagen: {e}")

            
            print("[Info] Warte auf Weiterleitung zur Vote-Seite...")
            try:
                await page.wait_for_url("**/bot/458302301187342336/vote*", timeout=15000)
            except: pass

            if await page.locator("text=You have already voted").is_visible():
                print("[🔴] Nach Login erkannt: Bereits gevotet! Setze 12h Cooldown...")
                save_browser_cooldown(token, time.time())
                return

            print("[Info] Warte 11 Sekunden, bis die Seite vollständig bereit ist...")
            await asyncio.sleep(11)

            print("[Info] Klicke auf den 'Vote' Button...")
            try:
                vote_button = page.locator("button:has-text('Vote'), button.btn-vote")
                await vote_button.first.click(timeout=5000, force=True)
                print("[🟢] Erfolgreich auf 'Vote' geklickt!")
            except Exception as e:
                print(f"[Fehler] Konnte nicht auf 'Vote' klicken (evtl. Captcha im Weg?): {e}")

            print("[Info] Warte finale 5 Sekunden...")
            await asyncio.sleep(5)
            
            print("[Info] Warte 3 weitere Sekunden vor dem automatischen Schließen...")
            await asyncio.sleep(3)
            
            print("[System] Schließe Browser automatisch und trage Token in den 12h Cooldown ein...")
            save_browser_cooldown(token, time.time())
            
        except Exception as e:
            print(f"[Fehler]: {e}")
        finally:
            try: await context.close()
            except: pass
                
            print(f"[System] Schließe Chrome-Prozess für Account {index+1}...")
            chrome_process.terminate()
            chrome_process.wait()
            
            if os.path.exists(chrome_profile_path):
                for _ in range(3):
                    try:
                        shutil.rmtree(chrome_profile_path)
                        break
                    except Exception: await asyncio.sleep(1)
            print(f"[System] Bereinigung für Account {index+1} abgeschlossen.")
            
async def main():
    headless_mode = True
    while True:
        print("\n" + "="*30)
        print("          MENÜ")
        print("="*30)
        print("[01] Script starten")
        print("[02] Script starten (Sichtbarer Modus)")
        print("[09] Config & Profile clearen")
        print("="*30)
        auswahl = input("Auswahl treffen: ").strip()

        if auswahl == "09":
            clear_browser_cooldowns()
        elif auswahl == "01":
            headless_mode = True
            break
        elif auswahl == "02":
            headless_mode = False
            break

    for index, token in enumerate(EINSTELLUNGEN):
        print(f"\n=== STARTE SITZUNG FÜR ACCOUNT {index+1} ===")
        await simuliere_sitzung(token, index, headless=headless_mode)

if __name__ == "__main__":
    asyncio.run(main())
