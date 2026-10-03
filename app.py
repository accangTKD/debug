import warnings
warnings.filterwarnings('ignore')

import requests
import random
import string
import time
import json
import codecs
import base64
import hmac
import hashlib
import secrets
from datetime import datetime
from flask import Flask, request, jsonify
import urllib3
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)

# ============ KONFIGURASI TELEGRAM ============
BOT_TOKEN = "8965307683:AAGXwuIge4QKuYXtrkXhG4AahxDrynqi7SY"
OWNER_ID = 8660700322
CHANNEL_PROMO = "@dindingijo"

# ============ KONFIGURASI API KEYS ============
API_KEYS = {
    "FREE_KEY_001": {"limit": 50, "used": 0, "last_reset_day": 0},
    "VIP_KEY_001": {"limit": 500, "used": 0, "last_reset_day": 0},
    "UNLIMITED_001": {"limit": 999999, "used": 0, "last_reset_day": 0}
}

# ============ KONFIGURASI GENERATOR ============
REGION_CHOICE = 1

REGION_MAP = {
    1: {"code": "ID",  "name": "INDONESIA",   "lang": "id", "host": "loginbp.ppmainecoonghj.com"},
    2: {"code": "ME",  "name": "MIDDLE EAST", "lang": "ar", "host": "loginbp.ppmainecoonghj.com"},
    3: {"code": "IND", "name": "INDIA",       "lang": "hi", "host": "loginbp.ppmainecoonghj.com"},
    4: {"code": "TH",  "name": "THAILAND",    "lang": "th", "host": "loginbp.ppmainecoonghj.com"},
    5: {"code": "VN",  "name": "VIETNAM",     "lang": "vi", "host": "loginbp.ppmainecoonghj.com"},
    6: {"code": "BD",  "name": "BANGLADESH",  "lang": "bn", "host": "loginbp.ppmainecoonghj.com"},
    7: {"code": "PK",  "name": "PAKISTAN",    "lang": "ur", "host": "loginbp.ppmainecoonghj.com"},
    8: {"code": "TW",  "name": "TAIWAN",      "lang": "zh", "host": "loginbp.ppmainecoonghj.com"},
    9: {"code": "CIS", "name": "RUSSIA",      "lang": "ru", "host": "loginbp.ppmainecoonghj.com"},
    10:{"code": "SAC", "name": "SPAIN",       "lang": "es", "host": "loginbp.ppmainecoonghj.com"},
    11:{"code": "BR",  "name": "BRAZIL",      "lang": "pt", "host": "loginbp.ppmainecoonghj.com"}
}

SELECTED = REGION_MAP.get(REGION_CHOICE, REGION_MAP[1])
REGION = SELECTED["code"]
REGION_NAME = SELECTED["name"]
LANG = SELECTED["lang"]
MAJOR_HOST = SELECTED["host"]

NAME_PREFIX = "Ccang"
PASS_PREFIX = "NewApiGenByCcang"

HEX_KEY = "2ee44819e9b4598845141067b281621874d0d5d7af9d8f7e00c1e54715b7d1e3"
AES_KEY = bytes([89, 103, 38, 116, 99, 37, 68, 69, 117, 104, 54, 37, 90, 99, 94, 56])
AES_IV  = bytes([54, 111, 121, 90, 68, 114, 50, 50, 69, 51, 121, 99, 104, 106, 77, 37])

# Datadome cookies (untuk bypass)
DATADOME_COOKIE_REG = "datadome=oYpIhVco_RFvLHe_T9KFd5wuY0gcQuNfrlt4rHJY5QOkwv4TGt8gPMK32MbHuBdzJyfXnXlfzNZT_2tHr2kys8AMYT2~T71QP1S78_7Pdx4JLOXdSrflPT6cOX2vsyJh"
DATADOME_COOKIE_TOK = "datadome=y23Z3X17pgkMHEt5zY8dqxC6BIf7WJMgC0RXNbqifHT7t9zajKe_hegFb1Ie9_7JixXpz7FRGVodOn~mWPk_NrqIIhUOXDYqKOahzoRQcyEy77GWEMcdA9_MqPJeM5qv"
DEVICE_ID = "02-344afb0e-593c-40b7-92f2-171972f74807"

WAF_UAS = [
    "GarenaMSDK/4.0.44(25028RN03A ;Android 15;ar;EG;app 1.132.1 2019121229;)",
    "GarenaMSDK/4.0.44(25028RN03A;Android 15;id;ID;)",
    "GarenaMSDK/4.0.44(SM-S928B;Android 14;en;SG;)",
    "GarenaMSDK/4.0.44(Xiaomi 14;Android 14;id;ID;)",
    "GarenaMSDK/4.0.44(Poco X5 Pro;Android 12;en;MY;)",
]

# ============ PROTOBUF ENCODER ============
def encode_varint(n):
    if n < 0: return b''
    result = bytearray()
    while True:
        byte = n & 0x7F
        n >>= 7
        if n: byte |= 0x80
        result.append(byte)
        if not n: break
    return bytes(result)

def create_proto_field(field_num, value):
    if isinstance(value, int):
        return encode_varint((field_num << 3) | 0) + encode_varint(value)
    elif isinstance(value, (str, bytes)):
        encoded_val = value.encode() if isinstance(value, str) else value
        return encode_varint((field_num << 3) | 2) + encode_varint(len(encoded_val)) + encoded_val
    return b''

def build_proto(fields):
    return b''.join(create_proto_field(k, v) for k, v in fields.items())

# ============ AES ENCRYPT ============
def aes_encrypt_bytes(data_bytes):
    cipher = AES.new(AES_KEY, AES.MODE_CBC, AES_IV)
    return cipher.encrypt(pad(data_bytes, AES.block_size))

def encrypt_api(plain_bytes):
    cipher = AES.new(AES_KEY, AES.MODE_CBC, AES_IV)
    return cipher.encrypt(pad(plain_bytes, AES.block_size))

# ============ TELEGRAM ============
def send_to_owner(account_id, uid, password, region_name, api_key, caller_ip):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    message = f"""🔥 <b>NEW ACCOUNT GENERATED VIA API</b> 🔥

🆔 Account ID: <code>{account_id}</code>
📝 UID: <code>{uid}</code>
🔑 <b>PASSWORD: <code>{password}</code></b>
🌍 Region: {region_name}
🔑 API Key: <code>{api_key}</code>
📞 IP Caller: {caller_ip}
⏰ Time: {datetime.now().strftime('%H:%M:%S %d/%m/%Y')}

💡 Join: {CHANNEL_PROMO}"""
    try:
        requests.post(
            url,
            json={"chat_id": OWNER_ID, "text": message, "parse_mode": "HTML"},
            timeout=10
        )
    except Exception:
        pass

# ============ HELPERS ============
def get_random_ip():
    return f"{random.randint(1,255)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,255)}"

def generate_password():
    return f"{PASS_PREFIX}{''.join(random.choices(string.ascii_uppercase + string.digits, k=6))}"

def generate_name():
    base = f"{NAME_PREFIX}{random.randint(10, 999)}"
    syms = ['~','!','@','#','$','%','^','&','*','-','_','+','=']
    p = random.randint(1, 3)
    if p == 1:
        s = random.choice(syms)
        return f"{s}{base}{s}"
    elif p == 2:
        s1, s2 = random.sample(syms, 2)
        return f"{s1}{s2}{base}"
    return base

def decode_jwt_payload(jwt_token):
    try:
        parts = jwt_token.split(".")
        if len(parts) < 2: return None
        pp = parts[1]
        pad_n = 4 - (len(pp) % 4)
        if pad_n != 4: pp += "=" * pad_n
        return json.loads(base64.urlsafe_b64decode(pp))
    except Exception:
        return None

def obfuscate_open_id(open_id):
    keystream = [
        0x30,0x30,0x30,0x32,0x30,0x31,0x37,0x30,
        0x30,0x30,0x30,0x30,0x32,0x30,0x31,0x37,
        0x30,0x30,0x30,0x30,0x30,0x32,0x30,0x31,
        0x37,0x30,0x30,0x30,0x30,0x30,0x32,0x30
    ]
    encoded = ''.join(
        chr(ord(open_id[i]) ^ keystream[i % len(keystream)])
        for i in range(len(open_id))
    )
    return codecs.decode(
        encoded.encode('unicode_escape').decode('utf-8'),
        'unicode_escape'
    ).encode('latin1')

# ============ GENERATOR ============
def generate_one_account(max_retry=5):
    for _ in range(max_retry):
        try:
            session = requests.Session()
            session.verify = False

            password = generate_password()

            # ── STEP 1: GUEST REGISTER ──
            reg_payload = json.dumps({
                "app_id": 100067,
                "client_type": 2,
                "password": password,
                "source": 2
            }, separators=(',', ':'))

            signature = hmac.new(
                HEX_KEY.encode(), reg_payload.encode(), hashlib.sha256
            ).hexdigest()

            headers_reg = {
                "User-Agent": random.choice(WAF_UAS),
                "Connection": "Keep-Alive",
                "Accept": "application/json",
                "Accept-Encoding": "gzip",
                "Authorization": f"Signature {signature}",
                "Content-Type": "application/json; charset=utf-8",
                "Cookie": DATADOME_COOKIE_REG,
                "Host": "100067.connect.garena.com",
                "X-Forwarded-For": get_random_ip(),
                "X-Real-IP": get_random_ip(),
            }

            resp_reg = session.post(
                "https://100067.connect.garena.com/api/v2/oauth/guest:register",
                headers=headers_reg, data=reg_payload, timeout=15
            )

            if resp_reg.status_code != 200:
                time.sleep(0.5); continue

            try:
                reg_json = resp_reg.json()
            except Exception:
                time.sleep(0.5); continue

            if reg_json.get("code") != 0:
                time.sleep(0.5); continue

            uid = reg_json['data']['uid']
            time.sleep(0.05)

            # ── STEP 2: TOKEN GRANT ──
            tok_payload = json.dumps({
                "client_id": 100067,
                "client_secret": HEX_KEY,
                "client_type": 2,
                "device_id": DEVICE_ID,
                "password": password,
                "response_type": "token",
                "uid": uid,
            }, separators=(',', ':'))

            headers_tok = headers_reg.copy()
            headers_tok["Cookie"] = DATADOME_COOKIE_TOK

            resp_tok = session.post(
                "https://100067.connect.garena.com/api/v2/oauth/guest/token:grant",
                headers=headers_tok, data=tok_payload, timeout=15
            )

            if resp_tok.status_code != 200:
                time.sleep(0.5); continue

            try:
                tok_json = resp_tok.json()
            except Exception:
                time.sleep(0.5); continue

            if tok_json.get("code") != 0:
                time.sleep(0.5); continue

            access_token = tok_json['data']['access_token']
            open_id      = tok_json['data']['open_id']
            time.sleep(0.05)

            # ── STEP 3: OBFUSCATE open_id ──
            field = obfuscate_open_id(open_id)

            # ── STEP 4: MAJOR REGISTER ──
            name = generate_name()

            proto = build_proto({
                1: name, 2: access_token, 3: open_id,
                5: 102000007, 6: 4, 7: 1, 13: 1,
                14: field, 15: LANG, 16: 1, 17: 1
            })
            enc_major = aes_encrypt_bytes(proto)

            headers_major = {
                "User-Agent": "UnityPlayer/2018.4.12f1 (UnityWebRequest/1.0, libcurl/8.5.0-DEV)",
                "Accept-Encoding": "deflate, gzip",
                "X-GA-SV": "1789535859",
                "Authorization": "Bearer",
                "X-GA": "v1 1",
                "ReleaseVersion": "OB55",
                "Content-Type": "application/x-www-form-urlencoded",
                "X-Unity-Version": "2018.4.12f1",
                "Host": MAJOR_HOST,
            }

            session.post(
                f"https://{MAJOR_HOST}/MajorRegister",
                headers=headers_major, data=enc_major, timeout=15
            )

            time.sleep(0.05)

            # ── STEP 5: MAJOR LOGIN ──
            payload_parts = [
                b'\x1a\x132025-08-30 05:19:21"\tfree fire(\x01:\x081.114.13B2Android OS 9 / API-28 (PI/rel.cjw.20220518.114133)J\x08HandheldR\nATM MobilsZ\x04WIFI`\xb6\nh\xee\x05r\x03300z\x1fARMv7 VFPv3 NEON VMH | 2400 | 2\x80\x01\xc9\x0f\x8a\x01\x0fAdreno (TM) 640\x92\x01\rOpenGL ES 3.2\x9a\x01+Google|dfa4ab4b-9dc4-454e-8065-e70c733fa53f\xa2\x01\x0e105.235.139.91\xaa\x01\x02',
                LANG.encode("ascii"),
                b'\xb2\x01 1d8ec0240ede109973f3321b9354b44d\xba\x01\x014\xc2\x01\x08Handheld\xca\x01\x10Asus ASUS_I005DA\xea\x01@afcfbf13334be42036e4f742c80b956344bed760ac91b3aff9b607a610ab4390\xf0\x01\x01\xca\x02\nATM Mobils\xd2\x02\x04WIFI\xca\x03 7428b253defc164018c604a1ebbfebdf\xe0\x03\xa8\x81\x02\xe8\x03\xf6\xe5\x01\xf0\x03\xaf\x13\xf8\x03\x84\x07\x80\x04\xe7\xf0\x01\x88\x04\xa8\x81\x02\x90\x04\xe7\xf0\x01\x98\x04\xa8\x81\x02\xc8\x04\x01\xd2\x04=/data/app/com.dts.freefireth-PdeDnOilCSFn37p1AH_FLg==/lib/arm\xe0\x04\x01\xea\x04_2087f61c19f57f2af4e7feff0b24d9d9|/data/app/com.dts.freefireth-PdeDnOilCSFn37p1AH_FLg==/base.apk\xf0\x04\x03\xf8\x04\x01\x8a\x05\x0232\x9a\x05\n2019118693\xb2\x05\tOpenGLES2\xb8\x05\xff\x7f\xc0\x05\x04\xe0\x05\xf3F\xea\x05\x07android\xf2\x05pKqsHT5ZLWrYljNb5Vqh//yFRlaPHSO9NWSQsVvOmdhEEn7W+VHNUK+Q+fduA3ptNrGB0Ll0LRz3WW0jOwesLj6aiU7sZ40p8BfUE/FI/jzSTwRe2\xf8\x05\xfb\xe4\x06\x88\x06\x01\x90\x06\x01\x9a\x06\x014\xa2\x06\x014\xb2\x06"GQ@O\x00\x0e^\x00D\x06UA\x0ePM\r\x13hZ\x07T\x06\x0cm\\V\x0ejYV;\x0bU5',
            ]
            raw_payload = b"".join(payload_parts)
            raw_payload = raw_payload.replace(
                b"afcfbf13334be42036e4f742c80b956344bed760ac91b3aff9b607a610ab4390",
                access_token.encode()
            )
            raw_payload = raw_payload.replace(
                b"1d8ec0240ede109973f3321b9354b44d",
                open_id.encode()
            )

            enc_bytes = encrypt_api(raw_payload)

            response = session.post(
                f"https://{MAJOR_HOST}/MajorLogin",
                headers=headers_major,
                data=enc_bytes,
                timeout=15
            )

            account_id = "N/A"
            jwt_token = ""

            if response.status_code == 200 and len(response.text) > 10:
                js = response.text.find("eyJ")
                if js != -1:
                    jwt_token = response.text[js:]
                    sd = jwt_token.find(".", jwt_token.find(".") + 1)
                    if sd != -1:
                        jwt_token = jwt_token[:sd + 44]
                    decoded = decode_jwt_payload(jwt_token)
                    if decoded:
                        account_id = (
                            decoded.get("account_id")
                            or decoded.get("external_id")
                            or "N/A"
                        )

            if account_id != "N/A":
                return {
                    "account_id": str(account_id),
                    "uid": uid,
                    "password": password,
                    "name": name,
                    "jwt_token": jwt_token,
                    "region": REGION_NAME,
                    "region_code": REGION,
                    "lang": LANG,
                }

        except Exception:
            pass

        time.sleep(0.5)

    return None

# ============ API KEY FUNCTIONS ============
def check_api_key(api_key):
    current_day = datetime.now().day
    if api_key not in API_KEYS:
        return False, "Invalid API key", None

    key_data = API_KEYS[api_key]

    if key_data.get("last_reset_day", 0) != current_day:
        key_data["used"] = 0
        key_data["last_reset_day"] = current_day

    if key_data["used"] >= key_data["limit"]:
        return False, f"Daily limit reached! Used {key_data['used']}/{key_data['limit']}", key_data

    return True, "OK", key_data

def update_api_key_usage(api_key):
    if api_key in API_KEYS:
        API_KEYS[api_key]["used"] += 1

# ============ FLASK ROUTES ============
@app.route('/', methods=['GET', 'POST'])
def home():
    return jsonify({
        "success": True,
        "message": "Account Generator API",
        "version": "1.0",
        "endpoints": {
            "generate": "/generate?key=YOUR_KEY",
            "status": "/status?key=YOUR_KEY"
        }
    })

@app.route('/generate', methods=['GET', 'POST'])
def generate():
    api_key = None
    if request.method == 'GET':
        api_key = request.args.get('key') or request.args.get('api_key')
    else:
        if request.is_json:
            api_key = request.json.get('key')
        else:
            api_key = request.form.get('key')

    if not api_key:
        return jsonify({
            "success": False,
            "message": "API key required. Use ?key=YOUR_KEY"
        }), 401

    valid, msg, key_data = check_api_key(api_key)
    if not valid:
        return jsonify({
            "success": False,
            "message": msg
        }), 429

    try:
        result = generate_one_account()

        if result:
            update_api_key_usage(api_key)

            client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
            send_to_owner(
                result["account_id"],
                result["uid"],
                result["password"],
                result["region"],
                api_key,
                client_ip
            )

            return jsonify({
                "success": True,
                "message": "Account generated successfully",
                "data": {
                    "account_id": result["account_id"],
                    "uid": str(result["uid"]),
                    "password": result["password"],
                    "region": result["region"],
                    "region_code": result["region_code"],
                    "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
            })
        else:
            return jsonify({
                "success": False,
                "message": "Failed to generate account. Please try again."
            }), 500

    except Exception:
        return jsonify({
            "success": False,
            "message": "Internal server error"
        }), 500

@app.route('/status', methods=['GET'])
def status():
    api_key = request.args.get('key') or request.args.get('api_key')

    if not api_key:
        return jsonify({
            "success": False,
            "message": "API key required"
        }), 401

    valid, msg, key_data = check_api_key(api_key)

    if not valid or not key_data:
        return jsonify({
            "success": False,
            "message": msg
        }), 404

    return jsonify({
        "success": True,
        "api_key": api_key,
        "limit": key_data["limit"],
        "used": key_data["used"],
        "remaining": key_data["limit"] - key_data["used"]
    })

if __name__ == '__main__':
    app.run(debug=True)