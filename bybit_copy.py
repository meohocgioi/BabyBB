# -*- coding: utf-8 -*-
"""
Bybit Multi-Sub Copy Tool
Nghe lenh tu 1 kenh Telegram -> mo Long + TP/SL tren nhieu sub account Bybit cung luc.
Chay: bam start.bat (Windows). Giao dien: http://127.0.0.1:8787
"""
VERSION = "1.4.0"

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
    "live_msg": None,               # [chat, message_id, rich] cua tin /status dang tu cap nhat
    "widgets": True,                # True = bot gui Rich Message (bang bieu), False = chu thuong
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
prices = {"t": 0.0, "map": {}}   # gia moi nhat cua tat ca hop dong (cap nhat moi giay)
lev_cache = {}                   # (ten acc, symbol) -> don bay da dat tren Bybit
PRICE_MAX_AGE = 4


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
                        "fee": max(0.0, -float(p.get("curRealisedPnl") or 0)),
                        "tp": p.get("takeProfit"), "sl": p.get("stopLoss")})
        return out


def public_client():
    return Bybit("public", "", "", ENVS.get(cfg["env"], ENVS["mainnet"]))


def rebuild_clients():
    global clients
    base = ENVS.get(cfg["env"], ENVS["mainnet"])
    clients = [Bybit(a.get("name") or f"Acc{i+1}", a["key"], a["secret"], base)
               for i, a in enumerate(cfg["accounts"]) if a.get("key") and a.get("secret")]
    lev_cache.clear()
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
async def set_lev(c, symbol, lev):
    """Dat don bay; tra ve None neu ok, nguoc lai tra ve thong bao loi."""
    try:
        r = await c.req("POST", "/v5/position/set-leverage",
                        {"category": "linear", "symbol": symbol,
                         "buyLeverage": f"{lev:g}", "sellLeverage": f"{lev:g}"})
        if r.get("retCode") in (0, 110043):
            lev_cache[(c.name, symbol)] = float(lev)
            return None
        return str(r.get("retMsg"))
    except Exception as e:
        return str(e)


async def price_loop():
    """Lay gia tat ca hop dong moi giay de luc vao lenh khong phai hoi gia nua."""
    while True:
        try:
            if clients:
                r = await public_client().req("GET", "/v5/market/tickers", {"category": "linear"}, auth=False)
                if r.get("retCode") == 0:
                    m = {}
                    for t in r["result"]["list"]:
                        try:
                            m[t["symbol"]] = float(t["lastPrice"])
                        except Exception:
                            pass
                    prices["map"], prices["t"] = m, time.time()
        except Exception:
            pass
        await asyncio.sleep(1)


async def get_price(symbol):
    if time.time() - prices["t"] <= PRICE_MAX_AGE and symbol in prices["map"]:
        return prices["map"][symbol], None
    r = await public_client().req("GET", "/v5/market/tickers",
                                  {"category": "linear", "symbol": symbol}, auth=False)
    try:
        return float(r["result"]["list"][0]["lastPrice"]), None
    except Exception:
        return None, r.get("retMsg")


async def open_one(c, symbol, notional, tp, sl, price, allin=None):
    """allin = None: lenh co size. allin = ("lev", so) hoac ("max",): all-in toan bo so du."""
    ins = instruments[symbol]
    try:
        if allin:
            st = status.get(c.name) or {}      # so du duoc cap nhat moi 3 giay
            avail = st.get("balance") if time.time() - st.get("t", 0) < 8 else None
            if avail is None:
                avail = await c.balance()
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
        # Dat don bay SONG SONG voi lenh (khong cho) -> tiet kiem 1 luot di-ve toi Bybit.
        # Neu da biet don bay dang dung thi bo qua luon.
        lev_task = None
        if lev_cache.get((c.name, symbol)) != float(lev):
            lev_task = asyncio.create_task(set_lev(c, symbol, lev))
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

        async def place():
            r = await c.req("POST", "/v5/order/create", {**order, **tpsl})
            if r.get("retCode") != 0 and "position idx" in str(r.get("retMsg", "")).lower():
                order["positionIdx"] = 1   # tai khoan dang o hedge mode
                r = await c.req("POST", "/v5/order/create", {**order, **tpsl})
            if r.get("retCode") != 0 and tpsl and lev_task is None:
                # TP/SL bi tu choi (gia chay qua nhanh) -> vao lenh truoc, dat TP/SL sau
                r = await c.req("POST", "/v5/order/create", order)
            return r

        r = await place()
        lev_err = None
        if lev_task:
            lev_err = await lev_task
            lev_task = None
            if r.get("retCode") != 0 and not lev_err:
                r = await place()          # lenh den truoc khi don bay kip doi -> gui lai
        if r.get("retCode") != 0 and allin and "insufficient" in str(r.get("retMsg", "")).lower():
            real *= 0.9                # thieu ky quy -> thu lai voi 90% size
            qty = min(floor_step(D(real) / D(price), ins["step"]), ins["maxmkt"])
            order["qty"] = fmt(qty)
            r = await place()
        if r.get("retCode") != 0:
            extra = f" | đặt đòn bẩy x{lev:g} lỗi: {lev_err}" if lev_err else ""
            return f"❌ {c.name}: vào lệnh lỗi: {r.get('retMsg')}{extra}"
        if lev_err:
            note += f" ⚠️ đã vào lệnh nhưng đặt đòn bẩy x{lev:g} lỗi: {lev_err}"
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
    price, perr = await get_price(symbol)
    if price is None:
        msg = f"❌ Không lấy được giá {symbol}: {perr}"
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


# ---------------------------------------------------------------------------
# Trinh bay tin nhan bot: ban chu (fallback) + ban Rich Message (Bot API 10.1+)
# Rich message = danh sach "blocks": heading / paragraph / table / footer.
# ---------------------------------------------------------------------------
def B(t):
    return {"type": "bold", "text": t}


def K(t):
    return {"type": "code", "text": t}


def cell(text, header=False, align=None):
    c = {"text": text} if text != "" else {}
    if header:
        c["is_header"] = True
    if align:
        c["align"] = align
    return c


def r_head(text, size=3):
    return {"type": "heading", "text": text, "size": size}


def r_par(text):
    return {"type": "paragraph", "text": text}


def r_table(header, rows, aligns=None):
    aligns = aligns or [None] * len(header)
    cells = [[cell(B(h), True, a) for h, a in zip(header, aligns)]]
    cells += [[cell(v, False, a) for v, a in zip(r, aligns)] for r in rows]
    return {"type": "table", "cells": cells, "is_bordered": True, "is_striped": True, "is_compact": True}


def r_foot(text):
    return {"type": "footer", "text": text}


POS_HEAD = ["Acc", "Position", "Phí", "PnL %", "PnL USDT"]
POS_ALIGN = [None, None, "right", "right", "right"]




def num(x):
    """So gon cho gia/size: 2003.1, 0.01234"""
    try:
        return f"{float(x):.6g}"
    except Exception:
        return str(x)


def dot(x):
    return "🟢" if x >= 0 else "🔴"


def side_vn(side):
    return "Long" if side == "Buy" else "Short"


async def close_one(c):
    """Dong moi position cua 1 acc, tra ve list dict ket qua (co phi + PnL thuc te neu lay duoc)."""
    rows = []
    try:
        t_ms = int(time.time() * 1000) + time_offset - 3000
        for p in await c.positions():
            r = await c.req("POST", "/v5/order/create", {
                "category": "linear", "symbol": p["symbol"],
                "side": "Sell" if p["side"] == "Buy" else "Buy",
                "orderType": "Market", "qty": p["size"],
                "reduceOnly": True, "positionIdx": p["idx"]})
            ok = r.get("retCode") == 0
            rows.append({"acc": c.name, "symbol": p["symbol"], "side": p["side"], "size": p["size"],
                         "lev": p["lev"], "entry": p["avg"], "exit": None, "fee": None,
                         "pnl": p["pnl"], "pct": p["pct"], "est": True,
                         "ok": ok, "err": "" if ok else str(r.get("retMsg"))})
        want = {x["symbol"] for x in rows if x["ok"]}
        agg = {}
        for _ in range(5):                 # cho Bybit ghi nhan ket qua dong lenh
            if not want:
                break
            await asyncio.sleep(0.5)
            r = await c.req("GET", "/v5/position/closed-pnl",
                            {"category": "linear", "startTime": str(t_ms), "limit": "100"})
            if r.get("retCode") != 0:      # vd Demo Trading khong ho tro
                break
            agg = {}
            for it in r["result"]["list"]:
                a = agg.setdefault(it["symbol"], {"pnl": 0.0, "fee": 0.0, "ev": 0.0, "xv": 0.0, "q": 0.0})
                a["pnl"] += float(it.get("closedPnl") or 0)
                a["fee"] += float(it.get("openFee") or 0) + float(it.get("closeFee") or 0)
                a["ev"] += float(it.get("cumEntryValue") or 0)
                a["xv"] += float(it.get("cumExitValue") or 0)
                a["q"] += float(it.get("closedSize") or it.get("qty") or 0)
            if want <= set(agg):
                break
        for x in rows:
            a = agg.get(x["symbol"])
            if x["ok"] and a and a["q"]:
                x.update(pnl=a["pnl"], fee=a["fee"], exit=a["xv"] / a["q"], est=False,
                         pct=(a["pnl"] / a["ev"] * 100) if a["ev"] else 0)
    except Exception as e:
        rows.append({"acc": c.name, "symbol": "", "ok": False, "err": str(e)[:120]})
    return rows


async def close_all():
    """-> (ban chu, blocks cua rich message)"""
    res = await asyncio.gather(*(close_one(c) for c in clients))
    rows = [x for sub in res for x in sub]
    if not rows:
        log("Không có position nào đang mở")
        return ("🛑 Không có position nào đang mở",
                [r_head("🛑 Market close"), r_par("Không có position nào đang mở.")])
    done = [x for x in rows if x["ok"]]
    tot = sum(x["pnl"] for x in done)
    fees = [x["fee"] for x in done if x["fee"] is not None]
    est = any(x["est"] for x in done)
    T = [f"🛑 Đã đóng {len(done)}/{len(rows)} position"]
    R, errs = [], []
    for x in rows:
        if not x["ok"]:
            T.append(f"❌ {x['acc']}: {x['symbol']} lỗi: {x['err']}")
            errs.append(f"❌ {x['acc']} {x['symbol']}: {x['err']}")
            log(T[-1])
            continue
        px = f"{num(x['entry'])} → {num(x['exit'])}" if x["exit"] else f"entry {num(x['entry'])}"
        fee = f"{x['fee']:.4f}" if x["fee"] is not None else "—"
        tag = " (ước tính)" if x["est"] else ""
        T.append(f"{x['acc']} · {side_vn(x['side'])} {x['symbol']} x{x['lev']}\n"
                 f"   Size {x['size']} | {px}\n"
                 f"   Phí {fee} USDT | {dot(x['pnl'])} {x['pct']:+.2f}% | {x['pnl']:+.4f} USDT{tag}")
        R.append([B(x["acc"]), [B(f"{side_vn(x['side'])} {x['symbol']}"), f" x{x['lev']}\nSize {x['size']}\n{px}"],
                  fee, f"{dot(x['pnl'])} {x['pct']:+.2f}%", B(f"{x['pnl']:+.4f}{'*' if x['est'] else ''}")])
        log(f"✅ {x['acc']}: đóng {x['symbol']} | phí {fee} | {x['pct']:+.2f}% | {x['pnl']:+.4f} USDT{tag}")
    blocks = [r_head(f"🛑 Đã đóng {len(done)}/{len(rows)} position")]
    if done:
        ft = f"{sum(fees):.4f}" if fees else "—"
        note = ("* PnL ước tính theo giá lúc đóng, chưa trừ phí (Bybit chưa trả số liệu)" if est
                else "PnL đã trừ phí mở + đóng. Đơn vị: USDT.")
        T.append(f"Tổng phí {ft} USDT | Tổng PnL {dot(tot)} {tot:+.4f} USDT\n({note})")
        R.append([B("Tổng"), "", B(ft), dot(tot), B(f"{tot:+.4f}")])
        blocks.append(r_table(POS_HEAD, R, POS_ALIGN))
        blocks.append(r_foot(note))
    for e in errs:
        blocks.append(r_par(e))
    return "\n".join(T), blocks


def status_text():
    lines = [f"Bot: {'🟢 ĐANG CHẠY' if cfg['running'] else '🔴 ĐANG DỪNG'} | "
             f"{'Theo kênh' if cfg['mode'] == 'follow' else 'Custom'} | Đòn bẩy all-in: {lev_label()}"]
    tot = 0.0
    for c in clients:
        st = status.get(c.name) or {}
        bal = f" (khả dụng {st['balance']:.2f} USDT)" if st.get("balance") is not None else ""
        if st.get("error"):
            lines.append(f"{c.name}: ⚠️ {st['error']}")
        elif not st.get("positions"):
            lines.append(f"{c.name}: không có position{bal}")
        else:
            for p in st["positions"]:
                tot += p["pnl"]
                lines.append(f"{c.name}: {side_vn(p['side'])} {p['symbol']} x{p['lev']}\n"
                             f"   Size {p['size']} | entry {num(p['avg'])} | phí {p.get('fee', 0):.4f}\n"
                             f"   {dot(p['pnl'])} {p['pct']:+.2f}% | {p['pnl']:+.4f} USDT")
    if any((status.get(c.name) or {}).get("positions") for c in clients):
        lines.append(f"Tổng PnL đang mở: {dot(tot)} {tot:+.4f} USDT")
    return "\n".join(lines)


def status_blocks(title=None, stamp=None):
    run = cfg["running"]
    blocks = [r_head(f"{title or '📊 Trạng thái'} — {'🟢 ĐANG CHẠY' if run else '🔴 ĐANG DỪNG'}"),
              r_par(["Chế độ: ", B("Theo lệnh kênh" if cfg["mode"] == "follow" else "Chỉ theo coin (custom)"),
                     " · Đòn bẩy all-in: ", B(lev_label())])]
    R, tot, has = [], 0.0, False
    for c in clients:
        st = status.get(c.name) or {}
        if st.get("error"):
            R.append([B(c.name), f"⚠️ {st['error']}", "", "", ""])
        elif not st.get("positions"):
            bal = f"Không có position\nKhả dụng {st['balance']:.2f} USDT" if st.get("balance") is not None else "Không có position"
            R.append([B(c.name), bal, "", "", ""])
        else:
            for p in st["positions"]:
                has = True
                tot += p["pnl"]
                R.append([B(c.name), [B(f"{side_vn(p['side'])} {p['symbol']}"),
                                      f" x{p['lev']}\nSize {p['size']}\nEntry {num(p['avg'])}"],
                          f"{p.get('fee', 0):.4f}", f"{dot(p['pnl'])} {p['pct']:+.2f}%", B(f"{p['pnl']:+.4f}")])
    if has:
        R.append([B("Tổng"), "", "", dot(tot), B(f"{tot:+.4f}")])
    if R:
        blocks.append(r_table(POS_HEAD, R, POS_ALIGN))
        blocks.append(r_foot("Phí = phí đã trả của position đang mở. Đơn vị: USDT."))
    else:
        blocks.append(r_par("Chưa cài sub account nào."))
    if stamp:
        blocks.append(r_foot(stamp))
    return blocks


async def status_loop():
    async def one(c):
        try:
            bal, pos = await asyncio.gather(c.balance(), c.positions())
            status[c.name] = {"balance": bal, "positions": pos, "error": "", "t": time.time()}
            for p in pos:
                try:
                    lev_cache[(c.name, p["symbol"])] = float(p["lev"])
                except Exception:
                    pass
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


HELP_ITEMS = [
    ("/start", "Chạy bot — bắt đầu nghe lệnh từ kênh"),
    ("/stop", "Dừng bot — position đang mở giữ nguyên"),
    ("/status", "Xem position, phí và PnL từng acc — tin tự cập nhật liên tục"),
    ("/buy #coin size tp sl", "Mở Long ngay trên tất cả acc. size = USDT, tp/sl = % so với entry. Vd: /buy #eth 1000 10 2"),
    ("/lev N", "Đặt đòn bẩy cho /allin. Vd: /lev 10 — hoặc /lev max = max của coin"),
    ("/allin #coin tp sl", "All-in toàn bộ vốn mỗi acc với đòn bẩy /lev (tự hạ nếu coin không cho). Vd: /allin #evaa 10 2"),
    ("/close", "Market close toàn bộ position, báo phí và PnL"),
    ("/help", "Hiện danh sách lệnh này"),
]
HELP_TEXT = "📖 Các lệnh:\n" + "\n".join(f"{c} — {d}" for c, d in HELP_ITEMS)


def help_blocks():
    return [r_head("📖 Các lệnh"),
            r_table(["Lệnh", "Tác dụng"], [[K(c), d] for c, d in HELP_ITEMS])]


BUY_RE = re.compile(r"^/buy(?:@\w+)?\s+#?([A-Za-z0-9]+)\s+(\d+(?:[.,]\d+)?)\s+(\d+(?:[.,]\d+)?)\s+(\d+(?:[.,]\d+)?)\s*$", re.I)


def parse_buy(text):
    m = BUY_RE.match((text or "").strip())
    if not m:
        return None
    f = lambda x: float(x.replace(",", "."))
    b = {"coin": m.group(1).upper(), "size": f(m.group(2)), "tp": f(m.group(3)), "sl": f(m.group(4))}
    return b if b["size"] > 0 else None


botst = {"ok": False, "err": "", "last": 0, "name": "", "token": ""}
BOT_MAX_AGE = 120      # bo qua lenh bot cu hon 120s (vd gui luc tool dang tat)


tg_http = None         # session rieng cho Telegram (giu ket noi san de gui nhanh)


async def bot_api(method, _timeout=8, _quiet=False, **params):
    """Goi Bot API. Timeout ngan de 1 ket noi bi treo khong lam ca bot bi lag."""
    if not cfg["bot_token"]:
        return {}
    url = f"https://api.telegram.org/bot{cfg['bot_token']}/{method}"
    try:
        to = aiohttp.ClientTimeout(total=_timeout, sock_connect=5)
        async with tg_http.post(url, json=params, timeout=to) as r:
            j = await r.json()
    except Exception as e:
        j = {"ok": False, "description": f"{type(e).__name__}: {str(e)[:100]}".rstrip(": ")}
    if not j.get("ok") and not _quiet:
        log(f"⚠️ Bot Telegram {method} lỗi: {j.get('description')}")
    return j


async def _send(chat, text):
    for attempt in range(1, 5):
        r = await bot_api("sendMessage", _quiet=True, chat_id=chat, text=text[:4000])
        if r.get("ok"):
            if attempt > 1:
                log(f"Bot đã gửi được tin sau {attempt} lần thử (mạng tới Telegram chập chờn)")
            return (r.get("result") or {}).get("message_id"), False
        desc = str(r.get("description"))
        if "Timeout" not in desc and "Connect" not in desc and "Disconnected" not in desc:
            break                      # loi tu Telegram (khong phai mang) -> thu lai vo ich
    log(f"⚠️ Bot không gửi được tin trả lời: {desc}")
    return None, False


async def _send_rich(chat, text, blocks):
    """Thu gui Rich Message; khong duoc thi gui ban chu."""
    if cfg.get("widgets", True) and botst.get("rich") is not False:
        for _ in range(3):
            r = await bot_api("sendRichMessage", _quiet=True, chat_id=chat, rich_message={"blocks": blocks})
            if r.get("ok"):
                botst["rich"] = True
                return (r.get("result") or {}).get("message_id"), True
            desc = str(r.get("description"))
            if "Timeout" in desc or "Connect" in desc or "Disconnected" in desc:
                continue               # loi mang -> thu lai
            if "not found" in desc.lower() or "404" in desc:
                botst["rich"] = False     # Bot API chua co sendRichMessage -> thoi khong thu nua
            log(f"Rich message bị Telegram từ chối ({desc[:120]}) — gửi bản chữ thay thế")
            break
    return await _send(chat, text)


# --- /status tu cap nhat: tool sua thang vao tin /status moi nhat ---
live = {"chat": None, "mid": None, "rich": True, "sig": "", "t": 0.0, "wait": 0.0}
LIVE_EVERY = 3         # giay giua 2 lan sua tin (khi so lieu thay doi)
LIVE_BEAT = 60         # so lieu khong doi van sua moi 60s de thay gio cap nhat


def live_stamp():
    return f"🔄 Tự cập nhật · lần cuối {datetime.now().strftime('%H:%M:%S')}"


def live_stop(why=""):
    if live["mid"] and why:
        log(f"Dừng tự cập nhật tin /status: {why}")
    live.update(chat=None, mid=None)
    if cfg.get("live_msg"):
        cfg["live_msg"] = None
        save_cfg()


async def start_live(chat):
    old = (live["chat"], live["mid"], live["rich"])
    live_stop()
    if old[1]:                         # danh dau tin cu la da ngung
        asyncio.create_task(live_edit(*old, final=True))
    mid, rich = await _send_rich(chat, status_text() + "\n" + live_stamp(), status_blocks(stamp=live_stamp()))
    if mid:
        live.update(chat=chat, mid=mid, rich=rich, sig=json.dumps(status_blocks(), ensure_ascii=False),
                    t=time.time(), wait=0.0)
        cfg["live_msg"] = [chat, mid, rich]
        save_cfg()


async def live_edit(chat, mid, rich, final=False):
    stamp = "⏹ Đã ngừng cập nhật — xem tin /status mới hơn" if final else live_stamp()
    p = {"chat_id": chat, "message_id": mid}
    if rich:
        p["rich_message"] = {"blocks": status_blocks(stamp=stamp)}
    else:
        p["text"] = (status_text() + "\n" + stamp)[:4000]
    return await bot_api("editMessageText", _quiet=True, **p)


async def live_loop():
    lm = cfg.get("live_msg")
    if lm:                             # tiep tuc sau khi tool khoi dong lai / update
        live.update(chat=lm[0], mid=lm[1], rich=bool(lm[2]))
    while True:
        await asyncio.sleep(1)
        try:
            if not live["mid"] or not cfg["bot_token"]:
                continue
            now = time.time()
            if now < live["wait"] or now - live["t"] < LIVE_EVERY:
                continue
            sig = json.dumps(status_blocks(), ensure_ascii=False)
            if sig == live["sig"] and now - live["t"] < LIVE_BEAT:
                continue
            r = await live_edit(live["chat"], live["mid"], live["rich"])
            desc = str(r.get("description") or "")
            if r.get("ok") or "not modified" in desc:
                live.update(sig=sig, t=time.time())
            elif "Too Many Requests" in desc or "retry after" in desc.lower():
                wait = float((r.get("parameters") or {}).get("retry_after") or 10)
                live["wait"] = time.time() + wait + 1
            elif "Timeout" in desc or "Connect" in desc or "Disconnected" in desc:
                live["wait"] = time.time() + 5
            else:                      # tin da bi xoa / khong sua duoc nua
                live_stop(desc[:100])
        except Exception as e:
            log(f"live status: {type(e).__name__}: {e}")


def send_rich(chat, text, blocks):
    asyncio.create_task(_send_rich(chat, text, blocks))


def send(chat, text):
    """Gui tin o nen: lenh tiep theo khong phai cho tin truoc gui xong."""
    asyncio.create_task(_send(chat, text))


async def notify(text):
    if cfg["bot_token"] and cfg["bot_owner_id"]:
        send(cfg["bot_owner_id"], text)


async def tg_keepalive():
    """Giu san 1 ket noi toi Telegram de tin tra loi khong phai mo ket noi moi."""
    while True:
        await asyncio.sleep(20)
        if cfg["bot_token"] and botst["ok"]:
            await bot_api("getMe", _timeout=6, _quiet=True)


async def bot_loop():
    offset = None
    while True:
        try:
            if not cfg["bot_token"]:
                botst.update(ok=False, err="")
                await asyncio.sleep(3)
                continue
            p = {"timeout": 25, "allowed_updates": ["message", "channel_post"]}
            if offset:
                p["offset"] = offset
            r = await bot_api("getUpdates", _timeout=40, _quiet=True, **p)
            if not r.get("ok"):
                err = str(r.get("description") or "không kết nối được Telegram")
                if err != botst["err"]:
                    log(f"⚠️ Bot Telegram không nhận được lệnh: {err}")
                botst.update(ok=False, err=err)
                await asyncio.sleep(3)
                continue
            if not botst["ok"] or botst["token"] != cfg["bot_token"]:
                me = await bot_api("getMe", _quiet=True)
                botst["name"] = "@" + str((me.get("result") or {}).get("username") or "?")
                botst["token"] = cfg["bot_token"]
                log(f"🤖 Bot Telegram đã kết nối: {botst['name']} — hãy nhắn lệnh cho đúng bot này")
            botst.update(ok=True, err="", last=time.time())
            for u in r["result"]:
                offset = u["update_id"] + 1
                try:
                    await handle_update(u)
                except Exception as e:
                    log(f"⚠️ Lỗi xử lý lệnh bot: {type(e).__name__}: {e}")
        except Exception as e:
            log(f"⚠️ bot loop: {type(e).__name__}: {e}")
            await asyncio.sleep(3)


async def handle_update(u):
    if True:
        if True:
            cp = u.get("channel_post")
            if cp:   # bot la admin cua kenh phat lenh -> nghe truc tiep, khong can dang nhap
                ch = cp.get("chat") or {}
                num, uname = chan_norm()
                if (num and ch.get("id") == num) or (uname and (ch.get("username") or "").lower() == uname):
                    await handle_channel_text(cp["message_id"], cp.get("text") or "",
                                              time.time() - cp.get("date", time.time()), "kênh-bot", time.time())
                return
            m = u.get("message") or {}
            chat = str((m.get("chat") or {}).get("id", ""))
            log(f"📩 Bot nhận: {(m.get('text') or '(không phải tin chữ)')[:40]} (chat {chat or '?'})")
            cmd = (m.get("text") or "").strip().split()[0:1]
            cmd = cmd[0].split("@")[0].lower() if cmd else ""
            if not chat:
                return
            age = time.time() - m.get("date", time.time())
            if age > BOT_MAX_AGE:
                log(f"Bỏ qua lệnh bot cũ ({age:.0f}s): {(m.get('text') or '')[:40]}")
                return
            if chat != str(cfg["bot_owner_id"]).strip():
                send(chat, f"Chat ID của bạn: {chat}\nNhập số này vào ô 'Chat ID chủ bot' trên tool.")
                return
            if cmd == "/start":
                cfg["running"] = True; save_cfg(); log("▶️ Start (từ Telegram)")
                send_rich(chat, "▶️ Bot ĐÃ CHẠY\n" + status_text(), status_blocks("▶️ Bot đã chạy"))
                return
            elif cmd == "/stop":
                cfg["running"] = False; save_cfg(); log("⏸ Stop (từ Telegram)")
                send_rich(chat, "⏸ Bot ĐÃ DỪNG (các position đang mở vẫn giữ nguyên)\n" + status_text(),
                          status_blocks("⏸ Bot đã dừng"))
                return
            elif cmd == "/close":
                log("🛑 Close all (từ Telegram)")
                send_rich(chat, *(await close_all()))
                return
            elif cmd == "/status":
                asyncio.create_task(start_live(chat))
                return
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
                    return
            elif cmd == "/buy":
                b = parse_buy(m.get("text") or "")
                if not b:
                    reply = ("Sai cú pháp. Dùng: /buy #coin size tp sl\n"
                             "Ví dụ: /buy #eth 1000 10 2 → Long ETHUSDT 1000 USDT, TP +10%, SL -2%")
                else:
                    log(f"🛒 /buy {b['coin']} {b['size']:g} {b['tp']:g} {b['sl']:g} (từ Telegram)")
                    await execute_order(b["coin"], b["size"], b["tp"], b["sl"], "/buy")
                    return   # ket qua da duoc gui qua notify()
            else:
                send_rich(chat, HELP_TEXT, help_blocks())
                return
            send(chat, reply)


# ----------------------------------------------------------------------------
# Web UI
# ----------------------------------------------------------------------------
def public_cfg():
    c = {k: v for k, v in cfg.items() if k not in ("accounts", "bot_token", "live_msg")}
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
                              "channel": cfg["channel_id"], "bot": bool(cfg["bot_token"]), "botst": botst})


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
    if "widgets" in d:
        cfg["widgets"] = str(d["widgets"]) != "0"
        botst.pop("rich", None)
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
    new_token = (d.get("bot_token") or "").strip()
    if new_token and new_token != cfg["bot_token"]:
        if re.fullmatch(r"\d+:[\w-]{30,}", new_token):
            cfg["bot_token"] = new_token
            log("🔑 Bot Token đã được thay bằng token mới")
        else:
            log("⚠️ Bỏ qua Bot Token vừa nhập vì không đúng dạng token của BotFather — vẫn giữ token cũ")
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
    return web.json_response({"ok": True, "msg": (await close_all())[0]})


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
    global http, tg_http
    load_cfg()
    http = aiohttp.ClientSession(
        timeout=aiohttp.ClientTimeout(total=10),
        connector=aiohttp.TCPConnector(limit=50, keepalive_timeout=60))
    tg_http = aiohttp.ClientSession(connector=aiohttp.TCPConnector(limit=20, keepalive_timeout=90))
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
    asyncio.create_task(tg_keepalive())
    asyncio.create_task(live_loop())
    asyncio.create_task(price_loop())
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
.secret{-webkit-text-security:disc}
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
    <label>Bot Token (từ @BotFather)</label><input id="bot_token" type="text" class="secret" autocomplete="off" data-lpignore="true" data-1p-ignore>
    <label>Chat ID chủ bot (nhắn bất kỳ cho bot để bot báo ID)</label><input id="bot_owner_id">
    <label>Kiểu tin nhắn của bot</label><select id="widgets"><option value="1">Rich message (bảng biểu)</option><option value="0">Chữ thường</option></select>
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
  $('widgets').value=cfg.widgets===false?'0':'1';
  $('acctxt').value=cfg.accounts.map(a=>a.key+'='+(a.has_secret?'••••••••':'')).join('\n');
  setMode(cfg.mode||'follow')}
function collect(){const accounts=$('acctxt').value.split('\n').map(l=>l.trim()).filter(l=>l).map((l,i)=>{const p=l.indexOf('=');const key=(p<0?l:l.slice(0,p)).trim();let secret=p<0?'':l.slice(p+1).trim();if(/^•+$/.test(secret))secret='';return{name:'Acc'+(i+1),key,secret}});
  const o={accounts,mode,widgets:$('widgets').value};
  for(const k of['env','size_unit','custom_size','custom_tp','custom_sl','bot_token','bot_owner_id','update_url','channel_id','allin_lev'])o[k]=$(k).value;return o}
async function save(){await post('/api/config',collect());toast('Đã lưu cài đặt');loadCfg()}
async function manual(){const t=$('manual').value.trim();if(!t)return;if(confirm('Gửi LỆNH THẬT: '+t+' ?'))post('/api/manual',{text:t})}
async function update(){const j=await post('/api/update');if(j&&j.restart)setTimeout(()=>location.reload(),5000)}
function lst(s){const l=s.listen;if(l.mode=='web')return l.ok?'✅ đang đọc kênh công khai':'⚠ '+(l.err||'đang kết nối…');if(l.mode=='bot')return s.bot?'qua bot (bot của bạn phải là admin kênh)':'⚠ ID dạng số cần bot của bạn làm admin kênh — hoặc nhập @tenkenh nếu kênh công khai';return '⚠ chưa nhập Channel ID'}
async function refresh(){try{const s=await(await fetch('/api/state')).json();
  $('run').textContent=s.running?'ĐANG CHẠY':'ĐANG DỪNG';$('run').className='pill '+(s.running?'on':'off');
  $('tgst').textContent=$('tgst2').textContent=lst(s);$('chn').textContent=s.channel||'chưa chọn';$('botst').textContent=!s.bot?'chưa cài':(s.botst.ok?'✅ '+s.botst.name:'⚠ '+(s.botst.err||'đang kết nối…'));
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
