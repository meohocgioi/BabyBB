# -*- coding: utf-8 -*-
"""
Bybit Multi-Sub Copy Tool
Nghe lenh tu 1 kenh Telegram -> mo Long + TP/SL tren nhieu sub account Bybit cung luc.
Chay: bam start.bat (Windows). Giao dien: http://127.0.0.1:8787
"""
VERSION = "1.0.6"

import asyncio, hashlib, hmac, html as htmllib, json, math, os, re, sys, time, webbrowser
from collections import deque
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from urllib.parse import urlencode, urlparse

import aiohttp
from aiohttp import web

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
PORT = 8787
RESTART_CODE = 42
DEFAULT_UPDATE_URL = "https://raw.githubusercontent.com/meohocgioi/BabyBB/main/bybit_copy.py"
SAFETY = 0.95          # chi dung 95% so du de tinh don bay (chua phi)
SIGNAL_MAX_AGE = 60    # bo qua tin cu hon 60s

ENVS = {
    "mainnet": "https://api.bybit.com",
    "demo": "https://api-demo.bybit.com",
    "testnet": "https://api-testnet.bybit.com",
}

DEFAULT_CFG = {
    "env": "mainnet",
    "accounts": [],                 # [{name, key, secret}]
    "mode": "follow",               # follow = theo het lenh kenh | custom = chi theo coin
    "size_unit": 1000,              # size 1 trong lenh = 1000 USDT
    "custom_size": 1000,            # USDT gia tri position (che do custom)
    "custom_tp": 10,                # %
    "custom_sl": 2,                 # %
    "allin_lev": "",                # don bay cho /allin: "" chua dat | so | "max"
    "channel_id": "", "channel_title": "",
    "bot_token": "", "bot_owner_id": "",
    "update_url": DEFAULT_UPDATE_URL,
    "running": False,
}

cfg = dict(DEFAULT_CFG)
logs = deque(maxlen=300)
status = {}            # name -> {balance, positions:[...], error}
instruments = {}       # symbol -> {step, min, maxmkt, tick, maxlev}
clients = []           # list[Bybit]
http = None            # aiohttp.ClientSession
time_offset = 0        # ms lech gio so voi Bybit
seen_msgs = deque(maxlen=200)


def log(msg):
    line = f"[{datetime.now().strftime('%H:%M:%S')}] {msg}"
    logs.appendleft(line)
    try:
        print(line, flush=True)
    except Exception:
        pass


def load_cfg():
    global cfg
    cfg = dict(DEFAULT_CFG)
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                cfg.update(json.load(f))
        except Exception as e:
            log(f"Lỗi đọc config.json: {e}")
    if not str(cfg.get("update_url") or "").strip():
        cfg["update_url"] = DEFAULT_UPDATE_URL


def save_cfg():
    tmp = CONFIG_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
    os.replace(tmp, CONFIG_PATH)


# ----------------------------------------------------------------------------
# Lenh Telegram:  m #coin size tp sl
# ----------------------------------------------------------------------------
CMD_RE = re.compile(
    r"^\s*m\s+#([A-Za-z0-9]+)"
    r"(?:\s+(\d+(?:[.,]\d+)?)\s+(\d+(?:[.,]\d+)?)\s+(\d+(?:[.,]\d+)?))?\s*$",
    re.I,
)


def parse_command(text):
    """Tra ve dict {coin, size, tp, sl} (size/tp/sl co the None) hoac None."""
    if not text:
        return None
    first = text.strip().splitlines()[0] if text.strip() else ""
    m = CMD_RE.match(first)
    if not m:
        return None
    f = lambda s: float(s.replace(",", ".")) if s else None
    return {"coin": m.group(1).upper(), "size": f(m.group(2)),
            "tp": f(m.group(3)), "sl": f(m.group(4))}


def plan_from_command(cmd):
    """Ap dung che do follow/custom -> (notional_usdt, tp%, sl%) hoac (None, ly do)."""
    if cfg["mode"] == "custom":
        return float(cfg["custom_size"]), float(cfg["custom_tp"]), float(cfg["custom_sl"])
    if cmd["size"] is None:
        return None, "lệnh thiếu size/tp/sl (chế độ theo kênh)"
    return cmd["size"] * float(cfg["size_unit"]), cmd["tp"], cmd["sl"]


# ----------------------------------------------------------------------------
# So hoc
# ----------------------------------------------------------------------------
def D(x):
    return Decimal(str(x))


def fmt(d):
    s = format(d, "f")
    return s.rstrip("0").rstrip(".") if "." in s else s


def floor_step(x, step):
    return (D(x) // step) * step


def round_tick(x, tick):
    return (D(x) / tick).quantize(Decimal(1), rounding=ROUND_HALF_UP) * tick


FEE_RESERVE = 0.0012   # phi mo + du phong phi dong (taker 0.055% x2)


def allin_plan(avail, want, maxlev):
    """All-in: (lev, notional) voi lev = min(want, max cua coin); want = None -> max."""
    lev = maxlev if want is None else min(float(want), maxlev)
    lev = max(1.0, lev)
    lev = int(lev) if lev == int(lev) else lev
    return lev, avail * 0.97 / (1 / lev + FEE_RESERVE)


def calc_leverage(notional, avail, maxlev):
    """Don bay nho nhat de mo du notional voi so du avail. Tra ve (lev, notional_thuc)."""
    usable = avail * SAFETY
    if usable <= 0:
        return None, 0
    lev = max(1, math.ceil(notional / usable))
    if lev > maxlev:
        lev = int(maxlev)
        notional = min(notional, usable * lev)
    return lev, notional


# ----------------------------------------------------------------------------
# Bybit V5 REST
# ----------------------------------------------------------------------------
class Bybit:
    def __init__(self, name, key, secret, base):
        self.name, self.key, self.secret, self.base = name, key, secret.encode(), base

    async def req(self, method, path, params=None, auth=True):
        params = params or {}
        headers = {}
        if method == "GET":
            payload = urlencode(params)
            url = self.base + path + ("?" + payload if payload else "")
            data = None
        else:
            payload = json.dumps(params, separators=(",", ":"))
            url = self.base + path
            data = payload
            headers["Content-Type"] = "application/json"
        if auth:
            ts = str(int(time.time() * 1000) + time_offset)
            recv = "10000"
            sign = hmac.new(self.secret, (ts + self.key + recv + payload).encode(),
                            hashlib.sha256).hexdigest()
            headers.update({"X-BAPI-API-KEY": self.key, "X-BAPI-TIMESTAMP": ts,
                            "X-BAPI-RECV-WINDOW": recv, "X-BAPI-SIGN": sign})
        async with http.request(method, url, data=data, headers=headers) as r:
            txt = await r.text()
        try:
            return json.loads(txt)
        except Exception:
            return {"retCode": -1, "retMsg": f"HTTP {r.status}: {txt[:150]}"}

    async def balance(self):
        r = await self.req("GET", "/v5/account/wallet-balance", {"accountType": "UNIFIED"})
        if r.get("retCode") != 0:
            raise RuntimeError(r.get("retMsg"))
        a = r["result"]["list"][0]
        for k in ("totalAvailableBalance", "totalWalletBalance", "totalEquity"):
            try:
                return float(a.get(k))
            except (TypeError, ValueError):
                continue
        return 0.0

    async def positions(self):
        r = await self.req("GET", "/v5/position/list",
                           {"category": "linear", "settleCoin": "USDT", "limit": "200"})
        if r.get("retCode") != 0:
            raise RuntimeError(r.get("retMsg"))
        out = []
        for p in r["result"]["list"]:
            size = float(p.get("size") or 0)
            if size <= 0:
                continue
            avg = float(p.get("avgPrice") or 0)
            pnl = float(p.get("unrealisedPnl") or 0)
            value = avg * size
            out.append({"symbol": p["symbol"], "side": p["side"], "size": p["size"],
                        "avg": avg, "pnl": pnl,
                        "pct": (pnl / value * 100) if value else 0,
                        "lev": p.get("leverage"), "idx": int(p.get("positionIdx") or 0),
                        "tp": p.get("takeProfit"), "sl": p.get("stopLoss")})
        return out


def public_client():
    return Bybit("public", "", "", ENVS.get(cfg["env"], ENVS["mainnet"]))


def rebuild_clients():
    global clients
    base = ENVS.get(cfg["env"], ENVS["mainnet"])
    clients = [Bybit(a.get("name") or f"Acc{i+1}", a["key"], a["secret"], base)
               for i, a in enumerate(cfg["accounts"]) if a.get("key") and a.get("secret")]
    for k in list(status):
        if k not in [c.name for c in clients]:
            status.pop(k, None)


async def sync_time():
    global time_offset
    try:
        r = await public_client().req("GET", "/v5/market/time", auth=False)
        time_offset = int(int(r["result"]["timeNano"]) / 1e6) - int(time.time() * 1000)
    except Exception as e:
        log(f"Không đồng bộ được giờ Bybit: {e}")


def _store_instrument(it):
    try:
        instruments[it["symbol"]] = {
            "step": D(it["lotSizeFilter"]["qtyStep"]),
            "min": D(it["lotSizeFilter"]["minOrderQty"]),
            "maxmkt": D(it["lotSizeFilter"].get("maxMktOrderQty") or it["lotSizeFilter"]["maxOrderQty"]),
            "tick": D(it["priceFilter"]["tickSize"]),
            "maxlev": float(it["leverageFilter"]["maxLeverage"]),
        }
    except Exception:
        pass


async def load_instruments(symbol=None):
    pub, cursor, n = public_client(), "", 0
    while True:
        p = {"category": "linear", "limit": "1000"}
        if symbol:
            p["symbol"] = symbol
        if cursor:
            p["cursor"] = cursor
        r = await pub.req("GET", "/v5/market/instruments-info", p, auth=False)
        if r.get("retCode") != 0:
            raise RuntimeError(r.get("retMsg"))
        for it in r["result"]["list"]:
            if it.get("quoteCoin") == "USDT" and it.get("status") == "Trading":
                _store_instrument(it)
                n += 1
        cursor = r["result"].get("nextPageCursor") or ""
        if not cursor or symbol:
            break
    return n


async def resolve_symbol(coin):
    cands = [coin + "USDT", "1000" + coin + "USDT", "10000" + coin + "USDT", "1000000" + coin + "USDT"]
    for s in cands:
        if s in instruments:
            return s
    try:  # coin moi list -> hoi truc tiep
        await load_instruments(cands[0])
    except Exception:
        pass
    return cands[0] if cands[0] in instruments else None


# ----------------------------------------------------------------------------
# Vao lenh
# ----------------------------------------------------------------------------
async def open_one(c, symbol, notional, tp, sl, price, allin=None):
    """allin = None: lenh co size. allin = ("lev", so) hoac ("max",): all-in toan bo so du."""
    ins = instruments[symbol]
    try:
        if allin:
            avail = await c.balance()          # all-in: lay so du moi nhat
            if avail <= 0:
                return f"❌ {c.name}: số dư = 0"
            want = allin[1] if allin[0] == "lev" else None
            lev, real = allin_plan(avail, want, ins["maxlev"])
            note = f" | ALL-IN vốn {avail:.2f} USDT"
            if want and lev < want:
                note += f" (coin chỉ cho tối đa x{lev:g})"
        else:
            avail = (status.get(c.name) or {}).get("balance")
            if avail is None:
                avail = await c.balance()
            lev, real = calc_leverage(notional, avail, ins["maxlev"])
            if lev is None:
                return f"❌ {c.name}: số dư = 0"
            note = "" if real >= notional - 0.01 else f" (giảm size còn {real:.0f} USDT vì max đòn bẩy x{lev})"
        r = await c.req("POST", "/v5/position/set-leverage",
                        {"category": "linear", "symbol": symbol,
                         "buyLeverage": f"{lev:g}", "sellLeverage": f"{lev:g}"})
        if r.get("retCode") not in (0, 110043):
            return f"❌ {c.name}: đặt đòn bẩy x{lev} lỗi: {r.get('retMsg')}"
        qty = min(floor_step(D(real) / D(price), ins["step"]), ins["maxmkt"])
        if qty < ins["min"]:
            return f"❌ {c.name}: size quá nhỏ (min {fmt(ins['min'])})"
        order = {"category": "linear", "symbol": symbol, "side": "Buy",
                 "orderType": "Market", "qty": fmt(qty), "positionIdx": 0}
        tpsl = {}
        if tp:
            tpsl["takeProfit"] = fmt(round_tick(D(price) * (1 + D(tp) / 100), ins["tick"]))
        if sl:
            tpsl["stopLoss"] = fmt(round_tick(D(price) * (1 - D(sl) / 100), ins["tick"]))
        if tpsl:
            tpsl["tpslMode"] = "Full"
        r = await c.req("POST", "/v5/order/create", {**order, **tpsl})
        if r.get("retCode") != 0 and "position idx" in str(r.get("retMsg", "")).lower():
            order["positionIdx"] = 1   # tai khoan dang o hedge mode
            r = await c.req("POST", "/v5/order/create", {**order, **tpsl})
        if r.get("retCode") != 0 and allin and "insufficient" in str(r.get("retMsg", "")).lower():
            real *= 0.9                # thieu ky quy -> thu lai voi 90% size
            qty = min(floor_step(D(real) / D(price), ins["step"]), ins["maxmkt"])
            order["qty"] = fmt(qty)
            r = await c.req("POST", "/v5/order/create", {**order, **tpsl})
        if r.get("retCode") != 0 and tpsl:
            # TP/SL bi tu choi (gia chay qua nhanh) -> vao lenh truoc, dat TP/SL sau
            r = await c.req("POST", "/v5/order/create", order)
        if r.get("retCode") != 0:
            return f"❌ {c.name}: vào lệnh lỗi: {r.get('retMsg')}"
        asyncio.create_task(fix_tpsl(c, symbol, tp, sl, order["positionIdx"]))
        return f"✅ {c.name}: Long {symbol} {fmt(qty)} (~{real:.0f} USDT, x{lev:g}){note}"
    except Exception as e:
        return f"❌ {c.name}: {e}"


async def fix_tpsl(c, symbol, tp, sl, idx):
    """Sau khi khop: dat lai TP/SL chinh xac theo gia entry thuc te."""
    if not tp and not sl:
        return
    ins = instruments[symbol]
    for _ in range(6):
        await asyncio.sleep(0.4)
        try:
            pos = [p for p in await c.positions() if p["symbol"] == symbol and p["side"] == "Buy"]
            if not pos or not pos[0]["avg"]:
                continue
            avg = D(pos[0]["avg"])
            body = {"category": "linear", "symbol": symbol, "tpslMode": "Full", "positionIdx": idx}
            if tp:
                body["takeProfit"] = fmt(round_tick(avg * (1 + D(tp) / 100), ins["tick"]))
            if sl:
                body["stopLoss"] = fmt(round_tick(avg * (1 - D(sl) / 100), ins["tick"]))
            r = await c.req("POST", "/v5/position/trading-stop", body)
            if r.get("retCode") in (0, 34040):
                return
            log(f"⚠️ {c.name}: đặt TP/SL theo entry lỗi: {r.get('retMsg')}")
            return
        except Exception as e:
            log(f"⚠️ {c.name}: fix TP/SL: {e}")
    log(f"⚠️ {c.name}: không thấy position {symbol} để đặt TP/SL — KIỂM TRA TAY!")


async def execute_signal(text, source="telegram", t0=None):
    t0 = t0 or time.time()
    cmd = parse_command(text)
    if not cmd:
        return "Không phải lệnh hợp lệ"
    plan = plan_from_command(cmd)
    if plan[0] is None:
        log(f"Bỏ qua '{text.strip()}': {plan[1]}")
        return plan[1]
    notional, tp, sl = plan
    return await execute_order(cmd["coin"], notional, tp, sl, source, t0)


async def execute_order(coin, notional, tp, sl, source, t0=None, allin=None):
    """Mo Long coin voi gia tri position = notional USDT tren tat ca sub account."""
    t0 = t0 or time.time()
    cmd = {"coin": coin.upper()}
    if not clients:
        log("Có lệnh nhưng chưa cài sub account nào")
        return "Chưa có sub account"
    symbol = await resolve_symbol(cmd["coin"])
    if not symbol:
        msg = f"❌ Không tìm thấy hợp đồng {cmd['coin']}USDT trên Bybit"
        log(msg); asyncio.create_task(notify(msg))
        return msg
    r = await public_client().req("GET", "/v5/market/tickers",
                                  {"category": "linear", "symbol": symbol}, auth=False)
    try:
        price = float(r["result"]["list"][0]["lastPrice"])
    except Exception:
        msg = f"❌ Không lấy được giá {symbol}: {r.get('retMsg')}"
        log(msg); asyncio.create_task(notify(msg))
        return msg
    res = await asyncio.gather(*(open_one(c, symbol, notional, tp, sl, price, allin) for c in clients))
    ms = int((time.time() - t0) * 1000)
    if allin:
        mx = instruments[symbol]["maxlev"]
        lv = mx if allin[0] == "max" else min(allin[1], mx)
        head = f"📥 [{source}] ALL-IN Long {symbol} | đòn bẩy x{lv:g} (coin max x{mx:g}) | TP +{tp:g}% | SL -{sl:g}% | {ms}ms"
        if sl and sl >= 90 / lv:
            head += f"\n⚠️ SL -{sl:g}% xa hơn mức thanh lý ước tính (~-{100 / lv:.1f}%) — có thể bị thanh lý trước khi chạm SL"
    else:
        head = f"📥 [{source}] Long {symbol} | size {notional:.0f} USDT | TP +{tp:g}% | SL -{sl:g}% | {ms}ms"
    log(head)
    for line in res:
        log(line)
    asyncio.create_task(notify(head + "\n" + "\n".join(res)))
    return head + "\n" + "\n".join(res)


async def close_one(c):
    out = []
    try:
        for p in await c.positions():
            r = await c.req("POST", "/v5/order/create", {
                "category": "linear", "symbol": p["symbol"],
                "side": "Sell" if p["side"] == "Buy" else "Buy",
                "orderType": "Market", "qty": p["size"],
                "reduceOnly": True, "positionIdx": p["idx"]})
            ok = r.get("retCode") == 0
            out.append(f"{'✅' if ok else '❌'} {c.name}: đóng {p['symbol']}"
                       + ("" if ok else f" lỗi: {r.get('retMsg')}"))
    except Exception as e:
        out.append(f"❌ {c.name}: {e}")
    return out


async def close_all():
    res = await asyncio.gather(*(close_one(c) for c in clients))
    lines = [l for sub in res for l in sub] or ["Không có position nào đang mở"]
    for l in lines:
        log(l)
    return "\n".join(lines)


def status_text():
    lines = [f"Bot: {'🟢 ĐANG CHẠY' if cfg['running'] else '🔴 ĐANG DỪNG'} | "
             f"{'Theo kênh' if cfg['mode'] == 'follow' else 'Custom'} | Đòn bẩy all-in: {lev_label()}"]
    for c in clients:
        st = status.get(c.name) or {}
        if st.get("error"):
            lines.append(f"{c.name}: ⚠️ {st['error']}")
        elif not st.get("positions"):
            lines.append(f"{c.name}: không có position")
        else:
            for p in st["positions"]:
                side = "Long" if p["side"] == "Buy" else "Short"
                lines.append(f"{c.name}: {side} {p['symbol']}, {p['pct']:+.2f}%, {p['pnl']:+.2f} USDT")
    return "\n".join(lines)


async def status_loop():
    async def one(c):
        try:
            bal, pos = await asyncio.gather(c.balance(), c.positions())
            status[c.name] = {"balance": bal, "positions": pos, "error": ""}
        except Exception as e:
            prev = status.get(c.name) or {}
            status[c.name] = {"balance": prev.get("balance"), "positions": prev.get("positions", []),
                              "error": str(e)[:120]}
    n = 0
    while True:
        try:
            if clients:
                await asyncio.gather(*(one(c) for c in clients))
            n += 1
            if n % 200 == 0:   # ~10 phut
                await sync_time()
                await load_instruments()
        except Exception as e:
            log(f"status loop: {e}")
        await asyncio.sleep(3)


# ----------------------------------------------------------------------------
# Telegram: nghe kenh — KHONG dang nhap tai khoan
#   1) Kenh cong khai (@username): doc trang xem truoc t.me/s/<username>
#   2) Bot cua ban la admin kenh: nhan channel_post qua Bot API (xem bot_loop)
# ----------------------------------------------------------------------------
listen = {"mode": "none", "ok": False, "err": "", "last": 0}
POLL_INTERVAL = 1.0


def chan_norm():
    """Channel ID nguoi dung nhap -> (id so dang -100..., username)."""
    s = str(cfg.get("channel_id") or "").strip()
    s = re.sub(r"^(https?://)?t\.me/(s/)?", "", s).lstrip("@").strip("/")
    if re.fullmatch(r"-?\d+", s):
        return (int(s) if s.startswith("-") else int("-100" + s)), None
    return None, (s.lower() or None)


async def handle_channel_text(msg_id, text, age, source, t0):
    if not parse_command(text):
        return
    if msg_id in seen_msgs:
        return
    seen_msgs.append(msg_id)
    if age > SIGNAL_MAX_AGE:
        log(f"Bỏ qua lệnh cũ ({age:.0f}s): {text.strip()}")
        return
    if not cfg["running"]:
        log(f"Bot đang DỪNG — bỏ qua lệnh: {text.strip()}")
        return
    await execute_signal(text, source, t0)


def parse_preview(page):
    """HTML cua t.me/s/<kenh> -> [(msg_id, text, timestamp)] tang dan theo id."""
    out = []
    for chunk in page.split('data-post="')[1:]:
        m = re.match(r'[^"/]+/(\d+)"', chunk)
        if not m:
            continue
        t = re.search(r'js-message_text"[^>]*>(.*?)</div>', chunk, re.S)
        text = ""
        if t:
            text = re.sub(r"<br\s*/?>", "\n", t.group(1))
            text = htmllib.unescape(re.sub(r"<[^>]+>", "", text))
        ts = time.time()
        d = re.findall(r'<time datetime="([^"]+)"', chunk)
        if d:
            try:
                ts = datetime.fromisoformat(d[-1]).timestamp()
            except Exception:
                pass
        out.append((int(m.group(1)), text, ts))
    return sorted(out)


async def web_listen_loop():
    cur, last_id = None, None
    while True:
        await asyncio.sleep(POLL_INTERVAL)
        num, uname = chan_norm()
        if not uname:
            listen.update(mode="bot" if num else "none", ok=False, err="")
            cur = None
            continue
        if uname != cur:
            cur, last_id = uname, None
        listen["mode"] = "web"
        try:
            t0 = time.time()
            async with http.get(f"https://t.me/s/{uname}",
                                headers={"User-Agent": "Mozilla/5.0", "Cache-Control": "no-cache"},
                                timeout=aiohttp.ClientTimeout(total=6)) as r:
                page = await r.text()
            posts = parse_preview(page)
            if not posts:
                listen.update(ok=False, err="không đọc được kênh (kênh riêng tư, sai tên, hoặc tắt xem trước)")
                continue
            listen.update(ok=True, err="", last=time.time())
            if last_id is None:            # lan dau: chi ghi moc, khong vao lenh cu
                last_id = posts[-1][0]
                log(f"Đang nghe kênh công khai @{uname} (tin mới nhất #{last_id})")
                continue
            for mid, text, ts in posts:
                if mid > last_id:
                    last_id = mid
                    await handle_channel_text(mid, text, time.time() - ts, "kênh", t0)
        except Exception as e:
            listen.update(ok=False, err=str(e)[:100])


# ----------------------------------------------------------------------------
# Telegram: bot dieu khien (Bot API)
# ----------------------------------------------------------------------------
def allin_setting():
    """cfg['allin_lev'] -> None (chua dat) | ("max",) | ("lev", so)."""
    v = str(cfg.get("allin_lev") or "").strip().lower()
    if v == "max":
        return ("max",)
    try:
        f = float(v)
        return ("lev", f) if 1 <= f <= 200 else None
    except ValueError:
        return None


def lev_label():
    a = allin_setting()
    return "chưa đặt" if not a else ("max của coin" if a[0] == "max" else f"x{a[1]:g}")


ALLIN_RE = re.compile(r"^/allin(?:@\w+)?\s+#?([A-Za-z0-9]+)\s+(\d+(?:[.,]\d+)?)\s+(\d+(?:[.,]\d+)?)\s*$", re.I)


def parse_allin(text):
    m = ALLIN_RE.match((text or "").strip())
    if not m:
        return None
    f = lambda x: float(x.replace(",", "."))
    return {"coin": m.group(1).upper(), "tp": f(m.group(2)), "sl": f(m.group(3))}


HELP_TEXT = (
    "📖 Các lệnh:\n"
    "/start — chạy bot (nghe lệnh từ kênh)\n"
    "/stop — dừng bot (position đang mở giữ nguyên)\n"
    "/status — xem position và PnL từng acc\n"
    "/buy #coin size tp sl — mở Long ngay trên tất cả acc\n"
    "      size = USDT, tp/sl = % so với giá entry\n"
    "      vd: /buy #eth 1000 10 2\n"
    "/lev N — đặt đòn bẩy cho /allin (vd /lev 10; /lev max = max của coin)\n"
    "/allin #coin tp sl — all-in toàn bộ vốn mỗi acc với đòn bẩy /lev\n"
    "      coin không cho tới mức đó thì tự hạ xuống max của coin\n"
    "      vd: /allin #evaa 10 2\n"
    "/close — market close toàn bộ position\n"
    "/help — hiện danh sách lệnh này"
)

BUY_RE = re.compile(r"^/buy(?:@\w+)?\s+#?([A-Za-z0-9]+)\s+(\d+(?:[.,]\d+)?)\s+(\d+(?:[.,]\d+)?)\s+(\d+(?:[.,]\d+)?)\s*$", re.I)


def parse_buy(text):
    m = BUY_RE.match((text or "").strip())
    if not m:
        return None
    f = lambda x: float(x.replace(",", "."))
    b = {"coin": m.group(1).upper(), "size": f(m.group(2)), "tp": f(m.group(3)), "sl": f(m.group(4))}
    return b if b["size"] > 0 else None


async def bot_api(method, **params):
    if not cfg["bot_token"]:
        return {}
    url = f"https://api.telegram.org/bot{cfg['bot_token']}/{method}"
    try:
        async with http.post(url, json=params, timeout=aiohttp.ClientTimeout(total=40)) as r:
            return await r.json()
    except Exception:
        return {}


async def notify(text):
    if cfg["bot_token"] and cfg["bot_owner_id"]:
        await bot_api("sendMessage", chat_id=cfg["bot_owner_id"], text=text[:4000])


async def bot_loop():
    offset, token = None, None
    while True:
        if not cfg["bot_token"]:
            await asyncio.sleep(3)
            continue
        if token != cfg["bot_token"]:      # token moi -> bo het lenh ton dong cu
            token = cfg["bot_token"]
            r = await bot_api("getUpdates", offset=-1, timeout=0)
            ups = r.get("result") or []
            offset = ups[-1]["update_id"] + 1 if ups else None
        p = {"timeout": 25, "allowed_updates": ["message", "channel_post"]}
        if offset:
            p["offset"] = offset
        r = await bot_api("getUpdates", **p)
        if not r.get("ok"):
            await asyncio.sleep(3)
            continue
        for u in r["result"]:
            offset = u["update_id"] + 1
            cp = u.get("channel_post")
            if cp:   # bot la admin cua kenh phat lenh -> nghe truc tiep, khong can dang nhap
                ch = cp.get("chat") or {}
                num, uname = chan_norm()
                if (num and ch.get("id") == num) or (uname and (ch.get("username") or "").lower() == uname):
                    try:
                        await handle_channel_text(cp["message_id"], cp.get("text") or "",
                                                  time.time() - cp.get("date", time.time()), "kênh-bot", time.time())
                    except Exception as e:
                        log(f"Lỗi xử lý channel_post: {e}")
                continue
            m = u.get("message") or {}
            chat = str((m.get("chat") or {}).get("id", ""))
            cmd = (m.get("text") or "").strip().split()[0:1]
            cmd = cmd[0].split("@")[0].lower() if cmd else ""
            if not chat:
                continue
            if chat != str(cfg["bot_owner_id"]).strip():
                await bot_api("sendMessage", chat_id=chat,
                              text=f"Chat ID của bạn: {chat}\nNhập số này vào ô 'Chat ID chủ bot' trên tool.")
                continue
            if cmd == "/start":
                cfg["running"] = True; save_cfg(); log("▶️ Start (từ Telegram)")
                reply = "▶️ Bot ĐÃ CHẠY\n" + status_text()
            elif cmd == "/stop":
                cfg["running"] = False; save_cfg(); log("⏸ Stop (từ Telegram)")
                reply = "⏸ Bot ĐÃ DỪNG (các position đang mở vẫn giữ nguyên)"
            elif cmd == "/close":
                log("🛑 Close all (từ Telegram)")
                reply = "🛑 Market close tất cả:\n" + await close_all()
            elif cmd == "/status":
                reply = status_text()
            elif cmd == "/lev":
                arg = (m.get("text") or "").split()[1:2]
                arg = arg[0].lower().lstrip("x").replace(",", ".") if arg else ""
                ok = arg == "max"
                if not ok:
                    try:
                        ok = 1 <= float(arg) <= 200
                    except ValueError:
                        ok = False
                if ok:
                    cfg["allin_lev"] = arg; save_cfg()
                    log(f"⚙️ Đòn bẩy all-in: {lev_label()} (từ Telegram)")
                    reply = (f"⚙️ Đã đặt đòn bẩy all-in: {lev_label()} cho tất cả sub account.\n"
                             "Áp dụng khi dùng /allin. Coin nào max thấp hơn thì tool tự hạ xuống max của coin đó.")
                else:
                    reply = f"Đòn bẩy all-in hiện tại: {lev_label()}\nDùng: /lev 10 (từ 1 đến 200) hoặc /lev max"
            elif cmd == "/allin":
                a = parse_allin(m.get("text") or "")
                st = allin_setting()
                if not a:
                    reply = ("Sai cú pháp. Dùng: /allin #coin tp sl\n"
                             "Ví dụ: /allin #evaa 10 2 → all-in Long EVAAUSDT, TP +10%, SL -2%")
                elif not st:
                    reply = "Chưa đặt đòn bẩy all-in. Gõ /lev 10 (hoặc /lev max để dùng max của coin) rồi gửi lại /allin."
                else:
                    log(f"🛒 /allin {a['coin']} {a['tp']:g} {a['sl']:g} (từ Telegram)")
                    await execute_order(a["coin"], 0, a["tp"], a["sl"], "/allin", allin=st)
                    continue
            elif cmd == "/buy":
                b = parse_buy(m.get("text") or "")
                if not b:
                    reply = ("Sai cú pháp. Dùng: /buy #coin size tp sl\n"
                             "Ví dụ: /buy #eth 1000 10 2 → Long ETHUSDT 1000 USDT, TP +10%, SL -2%")
                else:
                    log(f"🛒 /buy {b['coin']} {b['size']:g} {b['tp']:g} {b['sl']:g} (từ Telegram)")
                    await execute_order(b["coin"], b["size"], b["tp"], b["sl"], "/buy")
                    continue   # ket qua da duoc gui qua notify()
            else:
                reply = HELP_TEXT
            await bot_api("sendMessage", chat_id=chat, text=reply[:4000])


# ----------------------------------------------------------------------------
# Web UI
# ----------------------------------------------------------------------------
def public_cfg():
    c = {k: v for k, v in cfg.items() if k not in ("accounts", "bot_token")}
    c["accounts"] = [{"name": a.get("name", ""), "key": a.get("key", ""),
                      "has_secret": bool(a.get("secret"))} for a in cfg["accounts"]]
    c["has_bot_token"] = bool(cfg["bot_token"])
    return c


async def h_index(req):
    return web.Response(text=HTML.replace("__VERSION__", VERSION), content_type="text/html")


async def h_state(req):
    accs = []
    for c in clients:
        st = status.get(c.name) or {}
        accs.append({"name": c.name, "balance": st.get("balance"),
                     "positions": st.get("positions", []), "error": st.get("error", "")})
    return web.json_response({"version": VERSION, "running": cfg["running"], "mode": cfg["mode"],
                              "accounts": accs, "logs": list(logs)[:120], "listen": listen,
                              "channel": cfg["channel_id"], "bot": bool(cfg["bot_token"])})


async def h_get_cfg(req):
    return web.json_response(public_cfg())


async def h_save_cfg(req):
    d = await req.json()
    old = {a.get("key"): a.get("secret", "") for a in cfg["accounts"]}
    accs = []
    for i, a in enumerate(d.get("accounts", [])):
        key = (a.get("key") or "").strip()
        if not key:
            continue
        secret = (a.get("secret") or "").strip() or old.get(key, "")
        accs.append({"name": (a.get("name") or f"Acc{i+1}").strip(), "key": key, "secret": secret})
    cfg["accounts"] = accs
    if "allin_lev" in d:
        v = str(d["allin_lev"]).strip().lower().lstrip("x").replace(",", ".")
        cfg["allin_lev"] = v
        if not allin_setting():
            cfg["allin_lev"] = ""
    for k in ("env", "mode", "bot_owner_id", "update_url",
              "channel_id"):
        if k in d:
            cfg[k] = str(d[k]).strip()
    for k in ("size_unit", "custom_size", "custom_tp", "custom_sl"):
        try:
            cfg[k] = max(0.0, float(d[k]))
        except Exception:
            pass
    if (d.get("bot_token") or "").strip():
        cfg["bot_token"] = d["bot_token"].strip()
    save_cfg()
    rebuild_clients()
    instruments.clear()
    try:
        await sync_time()
        await load_instruments()
    except Exception as e:
        log(f"Tải danh sách hợp đồng lỗi: {e}")
    log("💾 Đã lưu cài đặt")
    return web.json_response({"ok": True})


async def h_start(req):
    cfg["running"] = True; save_cfg(); log("▶️ Start bot")
    return web.json_response({"ok": True})


async def h_stop(req):
    cfg["running"] = False; save_cfg(); log("⏸ Stop bot")
    return web.json_response({"ok": True})


async def h_close(req):
    log("🛑 Close all (từ tool)")
    return web.json_response({"ok": True, "msg": await close_all()})


async def h_manual(req):
    d = await req.json()
    msg = await execute_signal(d.get("text", ""), "tay")
    return web.json_response({"ok": True, "msg": msg})


async def h_update(req):
    url = cfg["update_url"].strip()
    if not url:
        return web.json_response({"ok": False, "msg": "Chưa nhập link update (GitHub raw) trong Cài đặt"})
    try:
        sep = "&" if "?" in url else "?"
        async with http.get(f"{url}{sep}t={int(time.time())}") as r:
            if r.status != 200:
                return web.json_response({"ok": False, "msg": f"Tải file lỗi HTTP {r.status}"})
            code = await r.text()
        m = re.search(r'^VERSION\s*=\s*"([^"]+)"', code, re.M)
        if not m:
            return web.json_response({"ok": False, "msg": "File tải về không phải tool này (thiếu VERSION)"})
        compile(code, "bybit_copy.py", "exec")
        if m.group(1) == VERSION:
            return web.json_response({"ok": True, "msg": f"Đang là bản mới nhất ({VERSION})"})
        me = os.path.abspath(__file__)
        with open(me, "r", encoding="utf-8") as f:
            old = f.read()
        with open(me + ".bak", "w", encoding="utf-8") as f:
            f.write(old)
        with open(me, "w", encoding="utf-8", newline="\n") as f:
            f.write(code)
        log(f"⬆️ Update {VERSION} -> {m.group(1)}, đang khởi động lại...")
        asyncio.get_event_loop().call_later(1.0, restart)
        return web.json_response({"ok": True, "restart": True,
                                  "msg": f"Đã update lên {m.group(1)} — tool tự khởi động lại"})
    except SyntaxError as e:
        return web.json_response({"ok": False, "msg": f"Bản mới bị lỗi code, giữ bản cũ: {e}"})
    except Exception as e:
        return web.json_response({"ok": False, "msg": str(e)})


def restart():
    if os.environ.get("BYBITCOPY_LAUNCHER"):
        os._exit(RESTART_CODE)          # start.bat se chay lai
    import subprocess
    env = dict(os.environ, BYBITCOPY_RESTARTED="1")
    subprocess.Popen([sys.executable, os.path.abspath(__file__)], env=env)
    os._exit(0)


@web.middleware
async def guard(req, handler):
    origin = req.headers.get("Origin")
    if req.method == "POST" and origin and urlparse(origin).netloc != req.host:
        return web.json_response({"ok": False, "msg": "forbidden"}, status=403)
    return await handler(req)


async def main():
    global http
    load_cfg()
    http = aiohttp.ClientSession(
        timeout=aiohttp.ClientTimeout(total=10),
        connector=aiohttp.TCPConnector(limit=50, keepalive_timeout=60))
    rebuild_clients()
    await sync_time()
    try:
        n = await load_instruments()
        log(f"Đã tải {n} hợp đồng USDT perp ({cfg['env']})")
    except Exception as e:
        log(f"Tải danh sách hợp đồng lỗi: {e}")
    for k in ("tg_api_id", "tg_api_hash", "tg_phone", "channel_title"):
        cfg.pop(k, None)

    app = web.Application(middlewares=[guard])
    app.add_routes([
        web.get("/", h_index), web.get("/api/state", h_state), web.get("/api/config", h_get_cfg),
        web.post("/api/config", h_save_cfg), web.post("/api/start", h_start),
        web.post("/api/stop", h_stop), web.post("/api/close", h_close),
        web.post("/api/manual", h_manual), web.post("/api/update", h_update),
    ])
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, "127.0.0.1", PORT).start()
    log(f"Tool v{VERSION} đang chạy: http://127.0.0.1:{PORT}")
    if not os.environ.get("BYBITCOPY_RESTARTED"):
        try:
            webbrowser.open(f"http://127.0.0.1:{PORT}")
        except Exception:
            pass
    asyncio.create_task(status_loop())
    asyncio.create_task(bot_loop())
    asyncio.create_task(web_listen_loop())
    await asyncio.Event().wait()


HTML = r"""<!doctype html>
<html lang="vi"><head><meta charset="utf-8"><title>Bybit Multi-Sub Copy</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
:root{--bg:#0e1116;--card:#171b22;--line:#262c36;--tx:#e6e9ee;--mut:#8b94a3;--gr:#20c997;--rd:#ff5c5c;--yl:#f7a600;--bl:#4c8dff}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--tx);font:14px/1.5 "Segoe UI",system-ui,sans-serif}
.wrap{max-width:1100px;margin:0 auto;padding:18px}
header{display:flex;align-items:center;gap:12px;flex-wrap:wrap;margin-bottom:14px}
h1{font-size:19px;margin:0;margin-right:auto}h1 small{color:var(--mut);font-weight:400;font-size:12px}
h2{font-size:14px;margin:0 0 10px;color:var(--yl);text-transform:uppercase;letter-spacing:.05em}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px;margin-bottom:14px}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:14px}@media(max-width:800px){.grid{grid-template-columns:1fr}}
button{border:0;border-radius:7px;padding:8px 14px;font:600 13px inherit;cursor:pointer;color:#fff;background:#2c3440}
button:hover{filter:brightness(1.15)}.b-gr{background:var(--gr);color:#04261b}.b-rd{background:var(--rd)}.b-yl{background:var(--yl);color:#231800}.b-bl{background:var(--bl)}
textarea{resize:vertical;font:12px/1.6 Consolas,monospace !important;white-space:pre;overflow-x:auto}
input,select,textarea{width:100%;background:#0e1116;border:1px solid var(--line);border-radius:6px;color:var(--tx);padding:7px 9px;font:13px inherit}
label{display:block;color:var(--mut);font-size:12px;margin:8px 0 3px}
.row{display:flex;gap:8px;align-items:end}.row>*{flex:1}.row>button{flex:0 0 auto}
.pill{padding:4px 12px;border-radius:99px;font-weight:700;font-size:12px}.on{background:#0f3d2e;color:var(--gr)}.off{background:#43201f;color:var(--rd)}
.acc{display:flex;gap:10px;padding:8px 0;border-bottom:1px solid var(--line);font-variant-numeric:tabular-nums}
.acc:last-child{border:0}.acc b{flex:0 0 90px}.acc .bal{margin-left:auto;color:var(--mut);white-space:nowrap}
.pos{color:var(--gr)}.neg{color:var(--rd)}.mut{color:var(--mut)}
#logs{font:12px/1.55 Consolas,monospace;max-height:300px;overflow:auto;white-space:pre-wrap;color:#c3cad5}
.modes{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.mode{border:1px solid var(--line);border-radius:8px;padding:10px;cursor:pointer}.mode.sel{border-color:var(--yl);background:#221c0d}
.mode b{display:block}.mode span{color:var(--mut);font-size:12px}
.accrow{display:grid;grid-template-columns:90px 1fr 1fr;gap:6px;margin-bottom:6px}
#toast{position:fixed;right:18px;bottom:18px;background:#222a35;border:1px solid var(--line);padding:10px 14px;border-radius:8px;display:none;max-width:420px;white-space:pre-wrap}
</style></head><body><div class="wrap">
<header>
  <h1>Bybit Multi-Sub Copy <small>v__VERSION__</small></h1>
  <span id="run" class="pill off">ĐANG DỪNG</span>
  <button class="b-gr" onclick="post('/api/start')">▶ Start</button>
  <button onclick="post('/api/stop')">⏸ Stop</button>
  <button class="b-rd" onclick="if(confirm('Market close TOÀN BỘ position của tất cả sub account?'))post('/api/close')">🛑 Close All</button>
  <button class="b-yl" onclick="update()">⬆ Update New Ver</button>
</header>

<div class="card"><h2>Status</h2><div id="status" class="mut">Đang tải…</div>
  <div class="mut" style="margin-top:8px;font-size:12px">Nghe kênh: <span id="tgst"></span> · Kênh: <span id="chn"></span> · Bot điều khiển: <span id="botst"></span></div></div>

<div class="grid">
<div>
  <div class="card"><h2>Chế độ vào lệnh</h2>
    <div class="modes">
      <div class="mode" id="m-follow" onclick="setMode('follow')"><b>1 · Theo lệnh kênh</b><span>Lấy cả size, TP, SL từ tin nhắn</span></div>
      <div class="mode" id="m-custom" onclick="setMode('custom')"><b>2 · Chỉ theo coin</b><span>Size, TP, SL do tôi tự đặt</span></div>
    </div>
    <div id="box-follow"><label>Size 1 trong lệnh = bao nhiêu USDT position</label><input id="size_unit" type="number"></div>
    <div id="box-custom" class="row">
      <div><label>Position size (USDT)</label><input id="custom_size" type="number"></div>
      <div><label>Target Price (+%)</label><input id="custom_tp" type="number" step="0.1"></div>
      <div><label>Stop Loss (−%)</label><input id="custom_sl" type="number" step="0.1"></div>
    </div>
    <div style="margin-top:12px"><button class="b-bl" onclick="save()">💾 Lưu cài đặt</button></div>
  </div>

  <div class="card"><h2>Gửi lệnh bằng tay (lệnh thật)</h2>
    <div class="row"><input id="manual" placeholder="m #space 1 10 2"><button onclick="manual()">Gửi</button></div></div>

  <div class="card"><h2>Log</h2><div id="logs"></div></div>
</div>

<div>
  <div class="card"><h2>Sub account Bybit</h2>
    <label>Môi trường</label><select id="env"><option value="mainnet">Mainnet (tiền thật)</option><option value="demo">Demo Trading (thử nghiệm)</option><option value="testnet">Testnet</option></select>
    <label>Mỗi dòng 1 sub account, định dạng <b>apikey=apisecret</b> (dòng 1 = Acc1, dòng 2 = Acc2…)</label>
    <textarea id="acctxt" rows="6" spellcheck="false" placeholder="apikey=apisecret&#10;apikey=apisecret"></textarea>
  </div>

  <div class="card"><h2>Telegram — nghe kênh</h2>
    <label>Channel ID của kênh phát lệnh (@tenkenh nếu kênh công khai, hoặc -100…)</label><input id="channel_id">
    <div class="mut" style="font-size:12px;margin-top:6px">Trạng thái: <span id="tgst2"></span></div>
  </div>

  <div class="card"><h2>Bot Telegram điều khiển từ xa</h2>
    <label>Bot Token (từ @BotFather)</label><input id="bot_token" type="password">
    <label>Chat ID chủ bot (nhắn bất kỳ cho bot để bot báo ID)</label><input id="bot_owner_id">
    <label>Đòn bẩy cho /allin (số, hoặc max = max của coin)</label><input id="allin_lev" placeholder="chưa đặt">
    <div class="mut" style="font-size:12px;margin-top:6px">Lệnh: /lev N · /allin #coin tp sl · /start · /stop · /status · /buy #coin size tp sl · /close · /help</div>
  </div>

  <div class="card"><h2>Update</h2>
    <label>Link GitHub raw của file bybit_copy.py</label><input id="update_url" placeholder="https://raw.githubusercontent.com/&lt;user&gt;/&lt;repo&gt;/main/bybit_copy.py">
  </div>
  <button class="b-bl" onclick="save()">💾 Lưu cài đặt</button>
</div>
</div></div><div id="toast"></div>
<script>
const $=id=>document.getElementById(id);let mode='follow',cfg={};
function toast(t){const e=$('toast');e.textContent=t;e.style.display='block';clearTimeout(toast.t);toast.t=setTimeout(()=>e.style.display='none',6000)}
async function post(u,b){try{const r=await fetch(u,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(b||{})});const j=await r.json();if(j.msg)toast(j.msg);refresh();return j}catch(e){toast('Lỗi: '+e)}}
function esc(s){return String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]))}
function setMode(m){mode=m;$('m-follow').classList.toggle('sel',m=='follow');$('m-custom').classList.toggle('sel',m=='custom');$('box-follow').style.display=m=='follow'?'':'none';$('box-custom').style.display=m=='custom'?'flex':'none'}
async function loadCfg(){cfg=await(await fetch('/api/config')).json();
  for(const k of['env','size_unit','custom_size','custom_tp','custom_sl','bot_owner_id','update_url','channel_id','allin_lev'])$(k).value=cfg[k]??'';
  $('bot_token').placeholder=cfg.has_bot_token?'•••• đã lưu':'';
  $('acctxt').value=cfg.accounts.map(a=>a.key+'='+(a.has_secret?'••••••••':'')).join('\n');
  setMode(cfg.mode||'follow')}
function collect(){const accounts=$('acctxt').value.split('\n').map(l=>l.trim()).filter(l=>l).map((l,i)=>{const p=l.indexOf('=');const key=(p<0?l:l.slice(0,p)).trim();let secret=p<0?'':l.slice(p+1).trim();if(/^•+$/.test(secret))secret='';return{name:'Acc'+(i+1),key,secret}});
  const o={accounts,mode};
  for(const k of['env','size_unit','custom_size','custom_tp','custom_sl','bot_token','bot_owner_id','update_url','channel_id','allin_lev'])o[k]=$(k).value;return o}
async function save(){await post('/api/config',collect());toast('Đã lưu cài đặt');loadCfg()}
async function manual(){const t=$('manual').value.trim();if(!t)return;if(confirm('Gửi LỆNH THẬT: '+t+' ?'))post('/api/manual',{text:t})}
async function update(){const j=await post('/api/update');if(j&&j.restart)setTimeout(()=>location.reload(),5000)}
function lst(s){const l=s.listen;if(l.mode=='web')return l.ok?'✅ đang đọc kênh công khai':'⚠ '+(l.err||'đang kết nối…');if(l.mode=='bot')return s.bot?'qua bot (bot của bạn phải là admin kênh)':'⚠ ID dạng số cần bot của bạn làm admin kênh — hoặc nhập @tenkenh nếu kênh công khai';return '⚠ chưa nhập Channel ID'}
async function refresh(){try{const s=await(await fetch('/api/state')).json();
  $('run').textContent=s.running?'ĐANG CHẠY':'ĐANG DỪNG';$('run').className='pill '+(s.running?'on':'off');
  $('tgst').textContent=$('tgst2').textContent=lst(s);$('chn').textContent=s.channel||'chưa chọn';$('botst').textContent=s.bot?'đã cài':'chưa cài';
  $('status').innerHTML=s.accounts.length?s.accounts.map(a=>{let body;
    if(a.error)body=`<span class="neg">⚠ ${esc(a.error)}</span>`;
    else if(!a.positions.length)body='<span class="mut">không có position</span>';
    else body=a.positions.map(p=>{const c=p.pnl>=0?'pos':'neg';return `${p.side=='Buy'?'Long':'Short'} <b>${esc(p.symbol)}</b>, <span class="${c}">${p.pct>=0?'+':''}${p.pct.toFixed(2)}%</span>, <span class="${c}">${p.pnl>=0?'+':''}${p.pnl.toFixed(2)} USDT</span> <span class="mut">(x${esc(p.lev)})</span>`}).join('<br>');
    return `<div class="acc"><b>${esc(a.name)}:</b><div>${body}</div><div class="bal">${a.balance==null?'':'Khả dụng '+a.balance.toFixed(2)+' USDT'}</div></div>`}).join(''):'Chưa có sub account — nhập apikey=apisecret ở cột bên phải rồi bấm Lưu.';
  $('logs').textContent=s.logs.join('\n')}catch(e){$('run').textContent='MẤT KẾT NỐI TOOL';$('run').className='pill off'}}
loadCfg();refresh();setInterval(refresh,2000);
</script></body></html>
"""

if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    if sys.platform == "win32":
        try:
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        except Exception:
            pass
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
