import os
import time
import json
import base64
import hashlib
import secrets
import requests
from seleniumwire import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

CLIENT_ID = os.environ.get("CLIENT_ID")
REDIRECT_URI = os.environ.get("REDIRECT_URI", "edpc://solar")
AUTH_HOST = os.environ.get("AUTH_HOST", "prd-accountlinking.auth.eu-west-1.amazoncognito.com")
TOKEN_SAVE_PATH = os.environ.get("TOKEN_SAVE_PATH", "/data/token.json")


def base64url_encode(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).decode().rstrip('=')


def gen_pkce():
    code_verifier = base64url_encode(secrets.token_bytes(32))
    code_challenge = base64url_encode(hashlib.sha256(code_verifier.encode()).digest())
    return code_verifier, code_challenge


def save_code_verifier(v):
    with open("/data/code_verifier.txt", "w") as f:
        f.write(v)


def save_tokens(data):
    with open(TOKEN_SAVE_PATH, "w") as f:
        json.dump(data, f, indent=2)
    print("Tokens guardados em", TOKEN_SAVE_PATH)


def exchange_code_for_tokens(code, code_verifier):
    token_url = f"https://{AUTH_HOST}/oauth2/token"
    payload = {
        "grant_type": "authorization_code",
        "client_id": CLIENT_ID,
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "code_verifier": code_verifier
    }
    print(payload)
    headers = {"Content-Type": "application/x-www-form-urlencoded",
               "Authorization": "Basic NnF2a2w3aWJ2c3BiZmphYm1ocWhpamU2ZTE6MTQ1dmttZG1jZm4xNDZhOW1qOGFuNm9yMGIzam1pcWdwM2M4NjFldnRuczZiYmE0ZDB0cA=="}
    r = requests.post(token_url, data=payload, headers=headers)
    r.raise_for_status()
    return r.json()


def salvar_console_logs(driver, output_file="/data/console.log"):
    logs = driver.get_log("browser")
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        for entry in logs:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    print(f"[INFO] Logs do console salvos em {output_file}")


def run_browser_flow(USERNAME, PASSWORD):
    startTimer = time.time()
    tokens = None
    code_verifier, code_challenge = gen_pkce()
    save_code_verifier(code_verifier)
    login_url = f"https://{AUTH_HOST}/login?redirect_uri={requests.utils.quote(REDIRECT_URI)}&response_type=code&client_id={CLIENT_ID}&code_challenge_method=S256&code_challenge={code_challenge}&scope=openid%20profile%20email"
    print("Login URL:", login_url)

    # selenium wire options (to capture network)
    options = {
        'request_storage': 'memory',
        'request_storage_max_size': 1000
    }

    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.5735.90 Safari/537.36")
    chrome_options.add_argument("--headless=new")  # tentar headless; se falhar, tira esta linha
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    chrome_options.set_capability("goog:loggingPrefs", {"browser": "ALL"})

    driver = webdriver.Chrome(seleniumwire_options=options, options=chrome_options)

    try:
        driver.get(login_url)
        print("Abrindo Pagina:")
        driver.implicitly_wait(10)
        driver.get_screenshot_as_file('/data/login.png')
        print("PrintScreen do login:")
        with open("/data/login.html", "w", encoding='utf-8') as f:
            f.write(driver.page_source)

        username_inputs = driver.find_elements(By.ID, "signInFormUsername")
        for el in username_inputs:
            driver.execute_script("arguments[0].value = arguments[1];", el, USERNAME)

        password_inputs = driver.find_elements(By.ID, "signInFormPassword")
        for el in password_inputs:
            driver.execute_script("arguments[0].value = arguments[1];", el, PASSWORD)
        driver.get_screenshot_as_file('/data/post-login.png')

        # Injetar antes de clicar no submit
        driver.execute_script("""
            (function() {
                window.__capturedRedirects = [];

                const originalAssign = window.location.assign;
                window.location.assign = function(url) {
                    window.__capturedRedirects.push(url);
                    originalAssign.call(window.location, url);
                };

                const originalReplace = window.location.replace;
                window.location.replace = function(url) {
                    window.__capturedRedirects.push(url);
                    originalReplace.call(window.location, url);
                };

                const originalPushState = history.pushState;
                history.pushState = function(state, title, url) {
                    if(url) window.__capturedRedirects.push(url);
                    return originalPushState.apply(history, arguments);
                };

                const originalReplaceState = history.replaceState;
                history.replaceState = function(state, title, url) {
                    if(url) window.__capturedRedirects.push(url);
                    return originalReplaceState.apply(history, arguments);
                };
            })();
        """)
        driver.execute_script("""
            const originalGetASF = window.getAdvancedSecurityData;

            window.getAdvancedSecurityData = function(formReference) {
                let result = originalGetASF(formReference);  // chama a função original
                try {
                    const usernameInput = document.getElementsByName("username")[0];
                    const username = usernameInput ? usernameInput.value : "";
                    const userPoolId = "";
                    const clientId = (function() {
                        name = 'client_id';
                        name = name.replace(/[\\[]/, '\\\\[').replace(/[\\]]/, '\\\\]');
                        var regex = new RegExp('[\\\\?&]' + name + '=([^&#]*)');
                        var results = regex.exec(location.search);
                        return results === null ? '' : decodeURIComponent(results[1].replace(/\\+/g, ' '));
                    })();
                    const asfData = AmazonCognitoAdvancedSecurityData.getData(username, userPoolId, clientId);
                    console.log("[ASF-DATA]", JSON.stringify(asfData));
                    window.__capturedASF = asfData;  // guarda globalmente
                    const form = document.forms['cognitoSignInForm'];
                         if (form && form.cognitoAsfData) {{
                             form.cognitoAsfData.value = asfData;
                         }}
                } catch(e) {
                    console.error("Erro capturando ASF:", e);
                }
                return result;
            };
        """)
        submit_btn = driver.find_elements(By.NAME, "signInSubmitButton")
        driver.execute_script("arguments[0].click();", submit_btn[1])
        # Agora, após submeter o form ou disparar a função
        asf_data = driver.execute_script("return window.__capturedASF;")
        driver.execute_script("arguments[0].click();", submit_btn[1])
        print("ASF Data capturada:", asf_data)
        driver.get_screenshot_as_file("/data/post-click-2.png")

        code = None
        start = time.time()
        timeout = 10
        first = True
        while time.time() - start < timeout:
            # verificar requests capturados pelo selenium-wire
            if first:
                first = False
                submit_btn = driver.find_elements(By.NAME, "signInSubmitButton")
                driver.execute_script("arguments[0].click();", submit_btn[1])
                print("Clicado aguardando!")
                driver.get_screenshot_as_file('/data/post-click.png')

            for req in driver.requests:
                if req.url:
                    try:
                        with open('/data/logs.txt', "a", encoding="utf-8") as f:
                            if not req.url.endswith('js') | req.url.endswith('css') | req.url.endswith('ico') | (
                                    'googleapis' in req.url):
                                if req.method == 'POST':
                                    f.write(f"---\n")
                                    f.write(f"Time: {time.time()}\n")
                                    f.write(f"Method: {req.method}\n")
                                    f.write(f"URL: {req.url}\n")
                                    f.write(f"Headers: {dict(req.headers)}\n")
                                    if req.body:
                                        try:
                                            body_str = req.body.decode() if isinstance(req.body, bytes) else str(
                                                req.body)
                                            f.write(f"Body: {body_str}\n")
                                        except Exception as e:
                                            f.write(f"Body: <unreadable: {e}>\n")
                                        # --- RESPONSE ---
                                    f.write(f"Response Status: {req.response.status_code}\n")
                                    f.write(f"Response Headers: {dict(req.response.headers)}\n")
                                    try:
                                        body_str = req.response.body.decode("utf-8", errors="replace")
                                        f.write(f"Response Body: {body_str}\n")
                                    except Exception as e:
                                        f.write(f"Response Body: <unreadable: {e}>\n")

                                    if req.response and "location" in req.response.headers:
                                        location = req.response.headers["location"]
                                        if location.startswith("edpc://solar"):
                                            print("🚀 Redirect capturado:", location)
                                            # extrair apenas o code
                                            import urllib.parse
                                            parsed = urllib.parse.urlparse(location)
                                            q = urllib.parse.parse_qs(parsed.query)
                                            code = q.get("code", [None])[0]
                                            print("✅ Code extraído:", code)
                                            break
                    except Exception as e:
                        print("Erro ao escrever log:", e)
            if code:
                break
        if code:
            print("Code capturado:", code + "...")
            tokens = exchange_code_for_tokens(code, code_verifier)
            save_tokens(tokens)
            return tokens

    finally:
        salvar_console_logs(driver)
        endTimer = time.time()
        print(endTimer - startTimer)
        driver.quit()


# if __name__ == "__main__":
#     run_browser_flow()
