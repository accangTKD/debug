# app.py
import warnings
warnings.filterwarnings('ignore')

import os
import sys
import json
import base64
import random
import string
import hmac
import hashlib
import secrets
import time
from datetime import datetime

import requests
import urllib3
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from flask import Flask, request, jsonify

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)

# ============ KONFIGURASI REGION ============
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

# ============ KREDENSIAL ============
AUTH_SECRET = "2ee44819e9b4598845141067b281621874d0d5d7af9d8f7e00c1e54715b7d1e3"
DEVICE_ID   = "02-344afb0e-593c-40b7-92f2-171972f74807"
HOST_REG    = MAJOR_HOST

COOKIE_REG = (
    "datadome=oYpIhVco_RFvLHe_T9KFd5wuY0gcQuNfrlt4rHJY5QOkwv4TGt8gPMK32MbHuBdzJyfXnXlfzNZT_2tHr2kys8AMYT2~T71QP1S78_7Pdx4JLOXdSrflPT6cOX2vsyJh"
)
COOKIE_TOK = (
    "datadome=y23Z3X17pgkMHEt5zY8dqxC6BIf7WJMgC0RXNbqifHT7t9zajKe_hegFb1Ie9_7JixXpz7FRGVodOn~mWPk_NrqIIhUOXDYqKOahzoRQcyEy77GWEMcdA9_MqPJeM5qv"
)

AES_KEY = bytes([89, 103, 38, 116, 99, 37, 68, 69, 117, 104, 54, 37, 90, 99, 94, 56])
AES_IV  = bytes([54, 111, 121, 90, 68, 114, 50, 50, 69, 51, 121, 99, 104, 106, 77, 37])

REG_URL   = "https://100067.connect.garena.com/api/v2/oauth/guest:register"
TOKEN_URL = "https://100067.connect.garena.com/api/v2/oauth/guest/token:grant"
MAJOR_REGISTER_URL = f"https://{HOST_REG}/MajorRegister"
MAJOR_LOGIN_URL    = f"https://{HOST_REG}/MajorLogin"

USER_AGENTS = [
    "Dalvik/2.1.0 (Linux; U; Android 11)",
    "Dalvik/2.1.0 (Linux; U; Android 12)",
    "Dalvik/2.1.0 (Linux; U; Android 13)",
    "Dalvik/2.1.0 (Linux; U; Android 14; CPH2095 Build/RKQ1.211119.001)",
    "Dalvik/2.1.0 (Linux; U; Android 13; SM-A536E Build/TP1A.220624.014)",
    "Dalvik/2.1.0 (Linux; U; Android 12; V2111 Build/SP1A.210812.003)",
    "GarenaMSDK/4.0.44(25028RN03A;Android 15;id;ID;)",
    "GarenaMSDK/4.0.44(SM-S928B;Android 14;en;SG;)",
    "GarenaMSDK/4.0.44(Xiaomi 14;Android 14;id;ID;)",
    "BestHTTP/2 v2.4.0",
]

MAX_RETRIES     = 3
RETRY_DELAY     = 1
RATE_LIMIT_WAIT = 30

# ============ KARAKTER UNICODE ============
CHARS_VN = list("ăâđêôơưĂÂĐÊÔƠƯáàảãạấầẩẫậắằẳẵặéèẻẽẹếềểễệ"
                "íìỉĩịóòỏõọốồổỗộớờởỡợúùủũụứừửữựýỳỷỹỵ")
CHARS_KR = list("가나다라마바사아자차카타파하고노도로모보소오조초코토포호"
                "기니디리미비시이지치키티피히김박이최정강조윤장임한오서신")
CHARS_CN = list("爱天云雨风花月星晨海山水河林木火土人心明家国梦光影年春夏"
                "秋冬日夜朝暮雪霜露虹霞涛浪龙虎鹤凤麒麟梅兰竹菊松柏夜")
CHARS_JP = list("あいうえおかきくけこさしすせそたちつてとなにぬねのはひふへほ"
                "まみむめもやゆよらりるれろわアイウエオカキクケコサシスセソ桜花月星空海風雪光夢心")
CHARS_TH = list("กขคงจฉชซญฎฏฐณดตถทธนบปผฝพฟภมยรลวศษสหฬอฮะัาิีึืุูเแใโไ")

CHAR_GROUPS = {"vn": CHARS_VN, "kr": CHARS_KR, "cn": CHARS_CN, "jp": CHARS_JP, "th": CHARS_TH}
ALL_GROUPS = list(CHAR_GROUPS.values())
ALL_CHARS = CHARS_VN + CHARS_KR + CHARS_CN + CHARS_JP + CHARS_TH

# ============ NAME & PASSWORD GENERATOR ============
def make_name() -> str:
    CORE = "Ccang"
    target_total = random.randint(7, 11)
    extra = target_total - len(CORE)

    for _ in range(40):
        if extra == 1:
            pre_len, suf_len = 0, 1
        else:
            pre_len = random.randint(0, extra)
            suf_len = extra - pre_len

        groups = random.sample(ALL_GROUPS, k=random.randint(2, len(ALL_GROUPS)))
        g1 = groups[0]
        g2 = groups[1] if len(groups) > 1 else groups[0]
        g3 = groups[2] if len(groups) > 2 else random.choice(ALL_GROUPS)

        prefix = "".join(random.choice(g1) for _ in range(pre_len))
        suffix = "".join(random.choice(g2) for _ in range(suf_len))

        if suf_len >= 2 and random.random() < 0.5:
            suffix = suffix[:-1] + random.choice(g3)

        name = f"{prefix}{CORE}{suffix}"
        if 7 <= len(name) <= 11:
            return name

    pre = random.choice(random.choice(ALL_GROUPS))
    suf = random.choice(random.choice(ALL_GROUPS))
    return f"{pre}Ccang{suf}"

def make_password() -> str:
    g1, g2 = random.sample(ALL_GROUPS, k=2)
    suffix = random.choice(g1) + random.choice(g2)
    return f"Generator@ByAccang{suffix}"

def random_username() -> str:
    return "id" + "".join(secrets.choice(string.ascii_letters + string.digits) for _ in range(12)) + "cang"

# ============ AES & HMAC ============
def aes_encrypt(data: bytes) -> bytes:
    return AES.new(AES_KEY, AES.MODE_CBC, AES_IV).encrypt(pad(data, AES.block_size))

def make_signature(payload: str) -> str:
    return hmac.new(AUTH_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()

# ============ PROTOBUF ============
def _encode_varint(n: int) -> bytes:
    if n < 0:
        return b""
    out = bytearray()
    while True:
        b = n & 0x7F
        n >>= 7
        if n:
            b |= 0x80
        out.append(b)
        if not n:
            break
    return bytes(out)

def _encode_field(field: int, value) -> bytes:
    if isinstance(value, bool):
        value = int(value)
    if isinstance(value, int):
        return _encode_varint((field << 3) | 0) + _encode_varint(value)
    if isinstance(value, (str, bytes)):
        raw = value.encode("utf-8") if isinstance(value, str) else value
        return _encode_varint((field << 3) | 2) + _encode_varint(len(raw)) + raw
    return b""

def assemble_proto(fields: dict) -> bytes:
    return b"".join(_encode_field(k, v) for k, v in fields.items())

def parse_proto(data: bytes) -> dict:
    out = {}
    i, n = 0, len(data)
    while i < n:
        tag, shift = 0, 0
        while i < n:
            b = data[i]; i += 1
            tag |= (b & 0x7F) << shift
            if not (b & 0x80): break
            shift += 7
        field_num = tag >> 3
        wire_type = tag & 7

        if wire_type == 0:
            val, shift = 0, 0
            while i < n:
                b = data[i]; i += 1
                val |= (b & 0x7F) << shift
                if not (b & 0x80): break
                shift += 7
            out[field_num] = val
        elif wire_type == 2:
            length, shift = 0, 0
            while i < n:
                b = data[i]; i += 1
                length |= (b & 0x7F) << shift
                if not (b & 0x80): break
                shift += 7
            payload = data[i:i + length]; i += length
            try:
                text = payload.decode("utf-8")
                out[field_num] = text if text.isprintable() else payload
            except Exception:
                out[field_num] = payload
        elif wire_type == 1:
            i += 8; out[field_num] = "<64>"
        elif wire_type == 5:
            i += 4; out[field_num] = "<32>"
        else:
            break
    return out

# ============ OPENID XOR ============
_OPENID_XOR_KEY = bytes([
    0x30,0x30,0x30,0x32,0x30,0x31,0x37,0x30,
    0x30,0x30,0x30,0x30,0x32,0x30,0x31,0x37,
    0x30,0x30,0x30,0x30,0x30,0x32,0x30,0x31,
    0x37,0x30,0x30,0x30,0x30,0x30,0x32,0x30,
])

def xor_open_id(open_id: str) -> bytes:
    return bytes(ord(open_id[i]) ^ _OPENID_XOR_KEY[i % len(_OPENID_XOR_KEY)] for i in range(len(open_id)))

def random_ip() -> str:
    return f"{random.randint(1,255)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,255)}"

# ============ GUEST REGISTER + TOKEN ============
def create_guest_account(max_retries: int = MAX_RETRIES):
    for _ in range(max_retries):
        try:
            session = requests.Session()
            session.verify = False

            password = random_username()
            user_agent = random.choice(USER_AGENTS)

            reg_payload = json.dumps(
                {"app_id": 100067, "client_type": 2, "password": password, "source": 2},
                separators=(",", ":"),
            )

            headers = {
                "User-Agent": user_agent,
                "Connection": "Keep-Alive",
                "Accept": "application/json",
                "Accept-Encoding": "gzip",
                "Authorization": f"Signature {make_signature(reg_payload)}",
                "Content-Type": "application/json; charset=utf-8",
                "Cookie": COOKIE_REG,
                "Host": "100067.connect.garena.com",
                "X-Forwarded-For": random_ip(),
                "X-Real-IP": random_ip(),
            }

            r = session.post(REG_URL, headers=headers, data=reg_payload, timeout=15)
            if r.status_code == 429:
                time.sleep(RATE_LIMIT_WAIT); continue
            if r.status_code != 200:
                time.sleep(RETRY_DELAY); continue

            try:
                j = r.json()
            except Exception:
                time.sleep(RETRY_DELAY); continue
            if j.get("code") != 0:
                time.sleep(RETRY_DELAY); continue

            uid = j["data"]["uid"]

            token_payload = json.dumps({
                "client_id": 100067,
                "client_secret": AUTH_SECRET,
                "client_type": 2,
                "device_id": DEVICE_ID,
                "password": password,
                "response_type": "token",
                "uid": uid,
            }, separators=(",", ":"))

            token_headers = headers.copy()
            token_headers["Cookie"] = COOKIE_TOK

            r = session.post(TOKEN_URL, headers=token_headers, data=token_payload, timeout=15)
            if r.status_code != 200:
                time.sleep(RETRY_DELAY); continue
            try:
                j = r.json()
            except Exception:
                time.sleep(RETRY_DELAY); continue
            if j.get("code") != 0:
                time.sleep(RETRY_DELAY); continue

            return {
                "uid": str(uid),
                "password": password,
                "access_token": j["data"]["access_token"],
                "open_id": j["data"]["open_id"],
                "session": session,
            }
        except Exception:
            time.sleep(RETRY_DELAY)
    return None

# ============ MAJOR REGISTER ============
FIELD_22_HEX = (
    "474752450101010062020000a78910bd098e3ff2e4345d59a31db114ea088f37e32e65"
    "212ff96621793d9eb78720d0bf2ac95176569765247ada5eb01376b3b9931794a4946"
    "d76ef8890779f3f2129317e6e1cb2fdcf7b06247cea343b8d4f167eff85a2e1dfe99"
    "b4583a7e1a155dbe7f7f85cff3b223eb77222ec1228f3ee1ef6ce7f8ca24b00a554"
    "e497328812f8df74c82d519ae3e3ceab436eb145e8a517089a7cef6a4efb22214b2"
    "a4b19989b74807584afe5e52825e7ac60e19a596a9bf02d961de6a0ed2515ec6023"
    "fdb7684d9464b97b21c527ce61b6bee4ef30d20a1fa33a996952d44d44e44f2f86c"
    "768aaf2a7808ad60f91048dca0207961ba7c2555c48341b30190debc775edb2cee24"
    "4cf51fca3760ce4388be2db45e80b813b5beb9c784007b7762d7a1e428affc8a3a4"
    "cd76cbaef648a274297fde33233dccd3f272cb77f39a1affe0365a24954111f768f72"
    "0e77535af024bea2b2726c3bac992374755c3deacf09235e6865d456e651680d115a"
    "751a797225eaacdf9a513cf104526e1a32e5296e111a33ae581a63850837921df848"
    "9adfd41ea895b7cf3f5b2e45d538a6e4f032f590ccbb7daf5fa9c50adadee0799661"
    "4c3f957bda349e6c484fdf55970d1943ad7955a76671298b6d98b636b69ebde6bc94"
    "dbd93ac3393a6ae230130445b2d744189167854a5617be2393e7d8fbb5719a1b4754"
    "1ba466167e3e05a6c244f1301ee2035acf94dffc8adbde747d5cd85e35ead3acc372"
    "a59c4220e54bf63f9d80485f3de2518495c1d0f78c911d2da595911fd2a1989cf17"
    "cf3ded5f6c92dea64d675c555c11df92d6c517ca5d0d61a8962f43f76ec7e87596c"
    "8325ebf9ab0f8e6d2eca33c511ceac6980906ebd68c478665591dcecf788ec6ef34c"
    "fbe3fcc279c6147c5bf91cd43cdc9704236"
)

FIELD_94_STR = (
    "KqsHT+UrR1HKqb6+1db+Ofei+NtZr2+hbiBo3yKDL8w+8E3S5qF2IgEEe1fFQFyHRzl4"
    "iyHjHp+QsfeLbjJ6+DidTiKxm0ak2uYYa6QR4nAUdlZR"
)

def send_major_register(session, name, access_token, open_id):
    fields = {
        1:  name,
        2:  access_token,
        3:  open_id,
        5:  102000007,
        6:  4,
        7:  1,
        13: 1,
        14: xor_open_id(open_id),
        15: "en",
        16: 2,
        20: "2.133.8",
        21: 1,
        22: bytes.fromhex(FIELD_22_HEX),
    }
    encrypted = aes_encrypt(assemble_proto(fields))

    headers = {
        "Host": HOST_REG,
        "User-Agent": "UnityPlayer/2018.4.12f1 (UnityWebRequest/1.0, libcurl/8.5.0-DEV)",
        "Accept": "*/*",
        "Accept-Encoding": "deflate, gzip",
        "X-GA-SV": str(int(time.time())),
        "Authorization": "Bearer",
        "X-GA": "v1 1",
        "ReleaseVersion": "OB55",
        "Content-Type": "application/x-www-form-urlencoded",
        "X-Unity-Version": "2018.4.12f1",
        "Content-Length": str(len(encrypted)),
    }

    resp = session.post(MAJOR_REGISTER_URL, data=encrypted, headers=headers, timeout=30)
    if resp.status_code != 200:
        raise Exception(f"MajorRegister HTTP {resp.status_code}: {resp.text}")
    return parse_proto(resp.content)

def major_register(session, access_token, open_id, name):
    try:
        result = send_major_register(session, name, access_token, open_id)
        if 3 in result and isinstance(result[3], int) and result[3] > 0:
            return {"ok": True, "real_uid": str(result[3]), "reason": "created"}
        if 9 in result and isinstance(result[9], str):
            return {"ok": False, "real_uid": None, "reason": "rejected"}
        return {"ok": False, "real_uid": None, "reason": "unknown"}
    except Exception as e:
        msg = str(e)
        if "ACCOUNT_EXISTS" in msg:
            return {"ok": True, "real_uid": None, "reason": "exists"}
        if "429" in msg:
            return {"ok": False, "real_uid": None, "reason": "rate_limit"}
        return {"ok": False, "real_uid": None, "reason": f"exception: {msg}"}

# ============ MAJOR LOGIN ============
def build_major_login_fields(access_token, open_id):
    return {
        3:  time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
        4:  "free fire", 5: 1, 7: "2.133.9",
        8:  "Android OS 10 / API-29 (QP1A.190711.020/1617006012)",
        9:  "Handheld", 10: "Vi India", 11: "WIFI",
        12: 1600, 13: 720, 14: "320",
        15: "ARM64 FP ASIMD AES | 2301 | 8",
        16: 2799, 17: "PowerVR Rogue GE8320",
        18: "OpenGL ES 3.2 build 1.11@5425693",
        19: "Google|9f7d6b8b-b10c-454a-852d-06332cd498eb",
        20: "151.158.158.220", 21: "en",
        22: access_token, 23: "4", 24: "Handheld",
        25: "realme RMX2189", 26: "SG",
        29: "9892ee38a1d1e2fdbc069b357a754a8c885145af7d32eac25ef81b072595d123",
        30: 1, 41: "Vi India", 42: "WIFI",
        57: "1ac4b80ecf0478a44203bf8fac6120f5",
        60: 19799, 61: 2536, 62: 5056, 64: 2768, 65: 19999,
        66: 2536, 67: 19799, 73: 1,
        74: "/data/app/com.dts.freefiremax-ShI7E0dK8p1IiZ785pvuVQ==/lib/arm64",
        76: 2,
        77: "38f4751a330688ab124c2c804cec90a5|/data/app/com.dts.freefiremax-ShI7E0dK8p1IiZ785pvuVQ==/base.apk",
        78: 2, 79: 2, 81: "64", 83: "2019118527",
        86: "OpenGLES3", 87: 3071, 88: 4, 92: 67920,
        93: "android_max", 94: FIELD_94_STR, 95: 111107,
        96: '{"cur_rate":null,"support_etc2":true}',
        97: 1, 98: 1, 99: "4", 100: "4", 102: "",
        104: 83812, 105: 1,
        106: "https://dl-bs.ggpolarbear.com/live/ABHotUpdates/|"
             "https://core-bs.ggpolarbear.com/live/ABHotUpdates/|"
             "a4332cb1c1a84e51dd77441e4856ed5a",
        107: "1.9393e7b8e53e8aeb",
    }

def major_login(session, access_token, open_id):
    try:
        plain = assemble_proto(build_major_login_fields(access_token, open_id))
        encrypted = aes_encrypt(plain)

        headers = {
            "Host": HOST_REG,
            "User-Agent": random.choice(USER_AGENTS),
            "Accept-Encoding": "deflate, gzip",
            "X-GA-SV": "1789535859",
            "Authorization": "Bearer",
            "X-GA": "v1 1",
            "ReleaseVersion": "OB55",
            "Content-Type": "application/x-www-form-urlencoded",
            "X-Unity-Version": "2018.4.12f1",
        }

        r = session.post(MAJOR_LOGIN_URL, headers=headers, data=encrypted, verify=False, timeout=15)

        if r.status_code == 200:
            idx = r.text.find("eyJ")
            if idx != -1:
                token = r.text[idx:]
                dot = token.find(".", token.find(".") + 1)
                if dot != -1:
                    token = token[: dot + 44]
                    payload = token.split(".")[1]
                    payload += "=" * (4 - len(payload) % 4)
                    j = json.loads(base64.urlsafe_b64decode(payload))
                    acct = j.get("account_id") or j.get("external_id")
                    if acct:
                        return str(acct), token
    except Exception:
        pass
    return None, None

# ============ ORKESTRASI ============
def generate_one_account(max_attempts: int = 10):
    for _ in range(max_attempts):
        try:
            creds = create_guest_account()
            if not creds:
                time.sleep(RETRY_DELAY); continue

            session      = creds["session"]
            uid          = creds["uid"]
            password     = creds["password"]
            access_token = creds["access_token"]
            open_id      = creds["open_id"]

            nickname   = make_name()
            pw_display = make_password()

            reg = major_register(session, access_token, open_id, nickname)
            if reg["reason"] == "rate_limit":
                time.sleep(RATE_LIMIT_WAIT); continue
            if not reg["ok"]:
                time.sleep(RETRY_DELAY); continue

            real_uid_from_reg = reg.get("real_uid")
            time.sleep(1)

            real_uid, _ = major_login(session, access_token, open_id)
            final_uid = real_uid or real_uid_from_reg

            if not final_uid or final_uid == "0":
                time.sleep(RETRY_DELAY); continue

            return {
                "account_id": str(final_uid),
                "uid": str(uid),
                "password": pw_display,
                "name": nickname,
                "region": REGION_NAME,
                "region_code": REGION,
                "lang": LANG,
            }
        except Exception:
            time.sleep(RETRY_DELAY)
    return None

# ============ FLASK ROUTES ============
@app.route('/', methods=['GET', 'POST'])
def home():
    return jsonify({
        "success": True,
        "message": "Account Generator API",
        "version": "2.0",
        "endpoints": {
            "generate": "/generate"
        }
    })

@app.route('/generate', methods=['GET', 'POST'])
def generate():
    try:
        result = generate_one_account()
        if not result:
            return jsonify({
                "success": False,
                "message": "Failed to generate account. Please try again."
            }), 500

        return jsonify({
            "success": True,
            "message": "Account generated successfully",
            "data": {
                "account_id": result["account_id"],
                "uid": result["uid"],
                "password": result["password"],
                "region": result["region"],
                "region_code": result["region_code"],
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Internal server error: {str(e)}"
        }), 500

if __name__ == '__main__':
    app.run(debug=False)
