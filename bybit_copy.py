# -*- coding: utf-8 -*-
"""
Bybit Multi-Sub Copy Tool
Nghe lenh tu 1 kenh Telegram -> mo Long + TP/SL tren nhieu sub account Bybit cung luc.
Chay: bam start.bat (Windows). Giao dien: http://127.0.0.1:8787
"""
VERSION = "1.12.0"

# Change log: ban moi nhat o tren cung. Bot gui phan nay sau moi lan /update.
CHANGELOG = [
    ("1.12.0", ["/status có chart nến 1 phút (60 nến gần nhất) của coin đang mở, kèm vạch ENTRY / TP / SL",
                "Chart tự cập nhật khoảng 15 giây/lần cho đến khi mọi sub account đóng hết position",
                "Đang mở nhiều coin thì vẽ coin có size lớn nhất"]),
    ("1.11.1", ["Bỏ dòng Total fee ở /per và Position History (PnL đã gồm phí)"]),
    ("1.11.0", ["/per và Position History gọn hơn trên điện thoại: bỏ cột Fee, thêm dòng Total fee cuối bảng",
                "Chấm 🟢/🔴 nằm cùng dòng với số PnL; Position History ghi Long/Short và số acc (vd 4 acc)",
                "Biểu đồ balance: trục dọc không còn lặp cùng một số khi balance gần như không đổi",
                "Tiêu đề và dòng chú thích cuối tin ngắn lại"]),
    ("1.10.2", ["Rà soát toàn bộ số hiển thị: tối đa 2 số sau dấu chấm; giá entry/exit từ 1 trở lên cũng 2 số (vd 2003.12)",
                "Riêng giá coin dưới 1 USDT giữ 4 chữ số có nghĩa (vd 0.004321) để không bị hiện thành 0.00"]),
    ("1.10.1", ["PnL và phí hiện 2 số sau dấu chấm (vd -1.07) ở /per, Position History, /status, /close — bảng gọn hơn trên điện thoại"]),
    ("1.10.0", ["Lệnh mới /buyall #coin tp sl — mở Long toàn bộ vốn mỗi acc với đòn bẩy max của coin (size lớn nhất có thể)",
                "Lệnh mới /sellall #coin tp sl — giống /buyall nhưng mở Short",
                "Bỏ lệnh /allin (thay bằng /buyall); /buyall và /sellall không cần đặt /lev trước"]),
    ("1.9.0", ["/per có biểu đồ đường: total balance trung bình của các acc (1 day: mốc 4 giờ; week/month: mốc theo ngày)",
               "Tool tự ghi balance mỗi 5 phút để vẽ biểu đồ (dữ liệu bắt đầu từ bản này)"]),
    ("1.8.1", ["Mọi chỗ hiện size đều tính bằng USDT (/status, /close, /per, tin vào lệnh, tin báo lỗi)",
               "Position History ghi rõ tên acc khi không phải tất cả acc cùng đóng"]),
    ("1.8.0", ["Lệnh /per — performance của các acc với nút 1 day / This week / This Month",
               "Nút Position History — 5 position đóng gần nhất, gộp cả các acc"]),
    ("1.7.0", ["Lệnh /sell #coin size tp sl — mở Short (ngược với /buy): TP khi giá giảm tp%, SL khi giá tăng sl%"]),
    ("1.6.2", ["Realized PnL chỉ hiện khi còn position đang mở; đóng hết thì kết quả cả đợt nằm trong tin báo đóng",
               "Nút Close Partial Position chỉ hiện khi có position đang mở"]),
    ("1.6.1", ["Bảng /status gọn hơn: No Position, Avai, Last Update; bỏ dòng chú thích phí",
               "Realized PnL: dòng trên đổi tên thành PnL (đã gồm phí)"]),
    ("1.6.0", ["Tin /status có nút đóng một phần position: 10% / 30% / 50% / 70% / 100% (bấm xong phải Xác nhận)",
               "Sau khi đóng, đầu tin /status hiện Realized PnL: Profit or Loss và Total fee"]),
    ("1.5.2", ["Khi lệnh lỗi, bot thêm dòng 💡 gợi ý cách sửa: size tối thiểu, size tối đa theo số dư, lỗi API key…"]),
    ("1.5.1", ["Chỉ cập nhật khi bạn gõ /update (hoặc bấm nút trên tool) — bỏ tự động cập nhật",
               "/update trả về change log dạng rich message"]),
    ("1.5.0", ["Lệnh /update qua bot Telegram",
               "Bản mới được chạy thử trước khi thay; lỗi khi khởi động thì tự quay về bản cũ"]),
    ("1.4.2", ["Tự đồng bộ lại giờ với Bybit khi bị từ chối vì lệch giờ"]),
    ("1.4.1", ["/lev áp dụng cho mọi lệnh (/buy, /allin, lệnh kênh)", "Hiện đúng giá trị thật của lệnh sau khi làm tròn"]),
    ("1.4.0", ["Tin /status tự cập nhật ngay trong tin"]),
    ("1.3.0", ["Bot trả lời bằng rich message (bảng): /status, /close, /help, /start, /stop"]),
    ("1.2.0", ["/close báo phí và PnL thực tế từng acc"]),
    ("1.1.0", ["Vào lệnh nhanh hơn: giá có sẵn, đòn bẩy đặt song song với lệnh"]),
    ("1.0.9", ["Bot không còn lag khi kết nối tới Telegram bị treo"]),
    ("1.0.6", ["Lệnh /lev và /allin"]),
    ("1.0.5", ["Lệnh /help và /buy"]),
]


def ver_key(v):
    try:
        return tuple(int(x) for x in str(v).split("."))
    except Exception:
        return (0,)


def changelog_since(old=None, limit=6):
    """Cac ban moi hon `old` (old=None -> chi ban hien tai)."""
    if old is None:
        return CHANGELOG[:1]
    return [e for e in CHANGELOG if ver_key(old) < ver_key(e[0]) <= ver_key(VERSION)][:limit] or CHANGELOG[:1]


def changelog_msg(title, entries):
    """-> (ban chu, blocks rich message)"""
    T = [title] + [f"v{v}\n" + "\n".join(f"  • {c}" for c in ch) for v, ch in entries]
    blocks = [r_head(title),
              r_table(["Bản", "Thay đổi"], [[B(f"v{v}"), "\n".join(f"• {c}" for c in ch)] for v, ch in entries])]
    return "\n".join(T), blocks

import asyncio, hashlib, hmac, html as htmllib, json, struct, zlib, math, os, re, sys, time, webbrowser
from collections import deque
from datetime import datetime, timedelta, timezone
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
    "update_note": "",              # tin bao se gui qua bot sau khi khoi dong lai
    "realized": {"pnl": 0.0, "fee": 0.0, "n": 0},   # PnL da chot cua dot position hien tai
    "live_msg": None,               # [chat, message_id, rich] cua tin /status dang tu cap nhat
    "widgets": True,                # True = bot gui Rich Message (bang bieu), False = chu thuong
    "allin_lev": "",                # don bay /lev cho moi lenh: "" chua dat | so | "max"
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
        r = await self._req(method, path, params, auth)
        if auth and is_time_error(r):
            # Dong ho may lech so voi Bybit -> dong bo lai ngay roi gui lai 1 lan
            await sync_time(force=True)
            r = await self._req(method, path, params, auth)
            if is_time_error(r):
                r["retMsg"] = "Lệch giờ với Bybit — tool đang tự đồng bộ lại, thử lại sau vài giây"
        return r

    async def _req(self, method, path, params=None, auth=True):
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
        self.equity = None
        for k in ("totalEquity", "totalWalletBalance"):      # total balance (gom ca PnL dang mo)
            try:
                self.equity = float(a.get(k))
                break
            except (TypeError, ValueError):
                continue
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


def is_time_error(r):
    return r.get("retCode") == 10002 or "timestamp" in str(r.get("retMsg", "")).lower()


_sync = {"t": 0.0, "lock": None}


async def sync_time(force=False):
    """Tinh do lech giua dong ho may va Bybit. Bybit tu choi lenh neu gio gui di
    som hon gio server qua 1 giay hoac tre hon 10 giay."""
    global time_offset
    if _sync["lock"] is None:
        _sync["lock"] = asyncio.Lock()
    async with _sync["lock"]:
        if time.time() - _sync["t"] < (1 if force else 20):
            return                     # vua dong bo xong (nhieu acc cung goi 1 luc)
        try:
            r = await public_client()._req("GET", "/v5/market/time", auth=False)
            server = int(int(r["result"]["timeNano"]) / 1e6)
            new = server - int(time.time() * 1000) - 300   # lui 300ms cho an toan
            if abs(new - time_offset) > 1500:
                log(f"🕒 Đồng hồ máy lệch {new / 1000:+.1f}s so với Bybit — đã tự bù")
            time_offset = new
            _sync["t"] = time.time()
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
            "minval": float(it["lotSizeFilter"].get("minNotionalValue") or 0),
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


async def open_one(c, symbol, notional, tp, sl, price, allin=None, side="Buy"):
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
            note = f" | toàn bộ vốn {avail:.2f} USDT"
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
            st = allin_setting()       # /lev da dat -> dung muc do (tu nang neu khong du ky quy cho size)
            if st:
                want = ins["maxlev"] if st[0] == "max" else min(st[1], ins["maxlev"])
                lev = max(lev, int(want) if want == int(want) else want)
        # Dat don bay SONG SONG voi lenh (khong cho) -> tiet kiem 1 luot di-ve toi Bybit.
        # Neu da biet don bay dang dung thi bo qua luon.
        lev_task = None
        if lev_cache.get((c.name, symbol)) != float(lev):
            lev_task = asyncio.create_task(set_lev(c, symbol, lev))
        qty = min(floor_step(D(real) / D(price), ins["step"]), ins["maxmkt"])
        if qty < ins["min"]:
            return f"❌ {c.name}: size quá nhỏ (min ≈ {min_usdt(symbol, price):g} USDT)"
        d = 1 if side == "Buy" else -1     # Long: TP tren, SL duoi. Short: nguoc lai
        order = {"category": "linear", "symbol": symbol, "side": side,
                 "orderType": "Market", "qty": fmt(qty), "positionIdx": 0}
        tpsl = {}
        if tp:
            tpsl["takeProfit"] = fmt(round_tick(D(price) * (1 + d * D(tp) / 100), ins["tick"]))
        if sl:
            tpsl["stopLoss"] = fmt(round_tick(D(price) * (1 - d * D(sl) / 100), ins["tick"]))
        if tpsl:
            tpsl["tpslMode"] = "Full"

        async def place():
            r = await c.req("POST", "/v5/order/create", {**order, **tpsl})
            if r.get("retCode") != 0 and "position idx" in str(r.get("retMsg", "")).lower():
                order["positionIdx"] = 1 if side == "Buy" else 2   # tai khoan dang o hedge mode
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
        asyncio.create_task(fix_tpsl(c, symbol, tp, sl, order["positionIdx"], side))
        val = float(qty) * price       # gia tri thuc sau khi lam tron so luong theo buoc cua san
        return f"✅ {c.name}: {side_vn(side)} {symbol} ~{val:.2f} USDT, x{lev:g}{note}"
    except Exception as e:
        return f"❌ {c.name}: {e}"


async def fix_tpsl(c, symbol, tp, sl, idx, side="Buy"):
    """Sau khi khop: dat lai TP/SL chinh xac theo gia entry thuc te."""
    if not tp and not sl:
        return
    ins = instruments[symbol]
    for _ in range(6):
        await asyncio.sleep(0.4)
        try:
            d = 1 if side == "Buy" else -1
            pos = [p for p in await c.positions() if p["symbol"] == symbol and p["side"] == side]
            if not pos or not pos[0]["avg"]:
                continue
            avg = D(pos[0]["avg"])
            body = {"category": "linear", "symbol": symbol, "tpslMode": "Full", "positionIdx": idx}
            if tp:
                body["takeProfit"] = fmt(round_tick(avg * (1 + d * D(tp) / 100), ins["tick"]))
            if sl:
                body["stopLoss"] = fmt(round_tick(avg * (1 - d * D(sl) / 100), ins["tick"]))
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


async def execute_order(coin, notional, tp, sl, source, t0=None, allin=None, side="Buy"):
    busy["n"] += 1
    try:
        return await _execute_order(coin, notional, tp, sl, source, t0, allin, side)
    finally:
        busy["n"] -= 1


async def _execute_order(coin, notional, tp, sl, source, t0=None, allin=None, side="Buy"):
    """Mo Long coin voi gia tri position = notional USDT tren tat ca sub account."""
    t0 = t0 or time.time()
    if (cfg.get("realized") or {}).get("n") and not any((status.get(c.name) or {}).get("positions") for c in clients):
        cfg["realized"] = {"pnl": 0.0, "fee": 0.0, "n": 0}     # dot position moi -> tinh lai tu dau
    cmd = {"coin": coin.upper()}
    if not clients:
        msg = "❌ Chưa cài sub account nào\n💡 Mở tool trên máy, dán apikey=apisecret của từng sub vào ô Sub account rồi bấm Lưu."
        log(msg); asyncio.create_task(notify(msg))
        return msg
    symbol = await resolve_symbol(cmd["coin"])
    if not symbol:
        msg = (f"❌ Không tìm thấy hợp đồng {cmd['coin']}USDT trên Bybit\n"
               f"💡 Kiểm tra lại tên coin: phải là hợp đồng USDT Perpetual đang giao dịch trên Bybit. "
               f"Coin giá rất nhỏ thường có tiền tố, vd #1000pepe.")
        log(msg); asyncio.create_task(notify(msg))
        return msg
    price, perr = await get_price(symbol)
    if price is None:
        msg = f"❌ Không lấy được giá {symbol}: {perr}\n💡 Thường do mạng tới Bybit chập chờn: gửi lại lệnh sau vài giây."
        log(msg); asyncio.create_task(notify(msg))
        return msg
    res = await asyncio.gather(*(open_one(c, symbol, notional, tp, sl, price, allin, side) for c in clients))
    ms = int((time.time() - t0) * 1000)
    if allin:
        mx = instruments[symbol]["maxlev"]
        lv = mx if allin[0] == "max" else min(allin[1], mx)
        sg = ("+", "-") if side == "Buy" else ("-", "+")
        head = (f"{'📥' if side == 'Buy' else '📤'} [{source}] MAX {side_vn(side)} {symbol} | đòn bẩy x{lv:g} (max của coin) | "
                f"TP {sg[0]}{tp:g}% | SL {sg[1]}{sl:g}% | {ms}ms")
        if sl and sl >= 90 / lv:
            head += (f"\n⚠️ SL {sg[1]}{sl:g}% xa hơn mức thanh lý ước tính (~{sg[1]}{100 / lv:.1f}%) — "
                     "có thể bị thanh lý trước khi chạm SL")
    else:
        sg = ("+", "-") if side == "Buy" else ("-", "+")
        head = (f"{'📥' if side == 'Buy' else '📤'} [{source}] {side_vn(side)} {symbol} | size {notional:.0f} USDT | "
                f"TP {sg[0]}{tp:g}% | SL {sg[1]}{sl:g}% | {ms}ms")
    res = list(res) + order_hints(res, cmd["coin"], symbol, price, tp, sl, source, allin)
    log(head)
    for line in res:
        log(line)
    asyncio.create_task(notify(head + "\n" + "\n".join(res)))
    return head + "\n" + "\n".join(res)


def min_usdt(symbol, price):
    """Size USDT nho nhat de dat duoc lenh (da cong 2% du phong gia chay)."""
    ins = instruments[symbol]
    v = max(float(ins["min"]) * price, ins.get("minval", 0)) * 1.02
    return math.ceil(v) if v >= 10 else math.ceil(v * 10) / 10


def order_hints(res, coin, symbol, price, tp, sl, source, allin):
    """Them dong 💡 huong dan cach sua cho cac loi thuong gap."""
    bad = " ".join(x for x in res if x.startswith("❌")).lower()
    if not bad:
        return []
    ins, H = instruments[symbol], []
    base = symbol[:-4]
    if "size quá nhỏ" in bad:
        mu = min_usdt(symbol, price)
        H.append(f"💡 Size tối thiểu của {symbol} là {fmt(ins['min'])} {base} ≈ {mu:g} USDT (giá {num(price)}).")
        if allin:
            lv = ins["maxlev"] if allin[0] == "max" else min(allin[1], ins["maxlev"])
            H.append(f"   {source} ở x{lv:g} cần ít nhất ~{mu / lv * 1.1:.2f} USDT khả dụng mỗi acc. Nạp thêm vốn vào acc.")
        elif source in ("/buy", "/sell"):
            H.append(f"   Gõ lại: {source} #{coin.lower()} {mu:g} {tp:g} {sl:g}")
        else:
            unit = float(cfg["size_unit"]) or 1
            H.append(f"   Lệnh kênh cần size ≥ {math.ceil(mu / unit * 100) / 100:g} (1 = {unit:g} USDT), hoặc đổi sang chế độ Custom với size ≥ {mu:g} USDT.")
    if "insufficient" in bad or "not enough" in bad:
        caps = []
        for c in clients:
            b = (status.get(c.name) or {}).get("balance")
            if b is not None:
                caps.append((b * SAFETY * ins["maxlev"], c.name, b))
        if caps:
            cap, name, b = min(caps)
            H.append(f"💡 Không đủ ký quỹ. Size tối đa mở được ở mọi acc: ~{cap:.0f} USDT "
                     f"({name} còn {b:.2f} USDT khả dụng, {symbol} max x{ins['maxlev']:g}).")
        else:
            H.append("💡 Không đủ ký quỹ: giảm size hoặc nạp thêm USDT vào Unified Trading Account của sub.")
    if "số dư = 0" in bad:
        H.append("💡 Acc chưa có USDT khả dụng: chuyển USDT vào Unified Trading Account của sub đó.")
    if "api key" in bad or "apikey" in bad or "sign" in bad:
        H.append("💡 API key/secret sai hoặc đã hết hạn: tạo lại API key của sub và dán lại vào tool (dạng apikey=apisecret).")
    if "permission" in bad:
        H.append("💡 API key thiếu quyền: bật Contract → Orders + Positions (Read-Write) cho API key của sub.")
    if "unmatched ip" in bad or " ip " in bad:
        H.append("💡 IP máy bạn không nằm trong danh sách IP của API key: thêm IP hiện tại hoặc bỏ giới hạn IP.")
    if "risk limit" in bad:
        H.append("💡 Vượt giới hạn rủi ro của Bybit ở mức đòn bẩy này: giảm size hoặc hạ /lev.")
    if "lệch giờ" in bad:
        H.append("💡 Tool đã tự đồng bộ lại giờ với Bybit: gửi lại lệnh sau vài giây.")
    if "max" in bad and "qty" in bad:
        H.append(f"💡 Vượt khối lượng tối đa cho 1 lệnh market của {symbol} ({fmt(ins['maxmkt'])} {base} ≈ {float(ins['maxmkt']) * price:,.0f} USDT): giảm size.")
    if not H:
        H.append("💡 Lỗi do Bybit trả về (dòng ❌ ở trên). Kiểm tra position mode là One-Way và acc là Unified Trading Account; nếu vẫn lỗi, chụp lại tin này để nhờ sửa.")
    return H


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
    """Gia: tu 1 tro len -> 2 so sau dau cham (2003.12); duoi 1 -> 4 chu so co nghia (0.01234)."""
    try:
        v = float(x)
        return f"{v:.2f}" if abs(v) >= 1 else f"{v:.4g}"
    except Exception:
        return str(x)


def dot(x):
    return "🟢" if x >= 0 else "🔴"


def side_vn(side):
    return "Long" if side == "Buy" else "Short"


async def close_one(c, pct=100):
    """Dong pct% moi position cua 1 acc, tra ve list dict ket qua (co phi + PnL thuc te neu lay duoc)."""
    rows = []
    try:
        t_ms = int(time.time() * 1000) + time_offset - 3000
        for p in await c.positions():
            qty = p["size"]
            if pct < 100:
                if p["symbol"] not in instruments:
                    try:
                        await load_instruments(p["symbol"])
                    except Exception:
                        pass
                ins = instruments.get(p["symbol"])
                q = floor_step(D(p["size"]) * D(pct) / 100, ins["step"]) if ins else D(0)
                if not ins or q < ins["min"]:
                    need = f"~{float(ins['min']) * p['avg']:.0f} USDT" if ins else "?"
                    rows.append({"acc": c.name, "symbol": p["symbol"], "ok": False,
                                 "err": f"{pct}% của position (~{float(p['size']) * p['avg'] * pct / 100:.0f} USDT) nhỏ hơn mức tối thiểu {need} — chọn % lớn hơn"})
                    continue
                qty = fmt(q)
            r = await c.req("POST", "/v5/order/create", {
                "category": "linear", "symbol": p["symbol"],
                "side": "Sell" if p["side"] == "Buy" else "Buy",
                "orderType": "Market", "qty": qty,
                "reduceOnly": True, "positionIdx": p["idx"]})
            ok = r.get("retCode") == 0
            frac = float(qty) / float(p["size"]) if float(p["size"]) else 1
            rows.append({"acc": c.name, "symbol": p["symbol"], "side": p["side"], "size": qty,
                         "usd": float(qty) * p["avg"],
                         "lev": p["lev"], "entry": p["avg"], "exit": None, "fee": None,
                         "pnl": p["pnl"] * frac, "pct": p["pct"], "est": True,
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


def add_realized(rows):
    rz = cfg.setdefault("realized", {"pnl": 0.0, "fee": 0.0, "n": 0})
    done = [x for x in rows if x.get("ok")]
    if not done:
        return
    rz["pnl"] += sum(x["pnl"] for x in done)
    rz["fee"] += sum(x["fee"] for x in done if x.get("fee") is not None)
    rz["n"] += 1
    if any(x.get("est") for x in done):
        rz["est"] = True
    save_cfg()


def has_pos():
    return any((status.get(c.name) or {}).get("positions") for c in clients)


def realized_lines(always=False):
    """3 dong Realized PnL cua dot position dang mo (hoac [] neu khong co gi de hien)."""
    rz = cfg.get("realized") or {}
    if not rz.get("n") or not (always or has_pos()):
        return []
    lab = "PnL (ước tính, chưa gồm phí)" if rz.get("est") else "PnL (đã gồm phí)"
    return ["Realized PnL", f"{lab} = {dot(rz['pnl'])} {rz['pnl']:+.2f} USDT",
            f"Total fee = {rz['fee']:.2f} USDT"]


async def close_partial(pct):
    """Dong pct% tat ca position (nut bam duoi tin /status). -> cau tom tat ngan"""
    busy["n"] += 1
    try:
        res = await asyncio.gather(*(close_one(c, pct) for c in clients))
    finally:
        busy["n"] -= 1
    rows = [x for sub in res for x in sub]
    if not rows:
        return "Không có position nào đang mở"
    add_realized(rows)
    done = [x for x in rows if x["ok"]]
    for x in rows:
        if x["ok"]:
            fee = f"{x['fee']:.2f}" if x.get("fee") is not None else "—"
            log(f"✂️ {x['acc']}: đóng {pct}% {x['symbol']} (~{x['usd']:.2f} USDT) | phí {fee} | {x['pnl']:+.2f} USDT")
        else:
            log(f"❌ {x['acc']}: đóng {pct}% {x['symbol']} lỗi: {x['err']}")
    errs = [x for x in rows if not x["ok"]]
    msg = f"Đã đóng {pct}% trên {len(done)}/{len(rows)} position"
    if errs:
        msg += f". Lỗi: {errs[0]['acc']} — {errs[0]['err']}"
    return msg


async def close_all():
    """-> (ban chu, blocks cua rich message)"""
    busy["n"] += 1
    try:
        res = await asyncio.gather(*(close_one(c) for c in clients))
    finally:
        busy["n"] -= 1
    rows = [x for sub in res for x in sub]
    prev_n = (cfg.get("realized") or {}).get("n", 0)
    add_realized(rows)
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
        fee = f"{x['fee']:.2f}" if x["fee"] is not None else "—"
        tag = " (ước tính)" if x["est"] else ""
        T.append(f"{x['acc']} · {side_vn(x['side'])} {x['symbol']} x{x['lev']}\n"
                 f"   Size {x['usd']:.2f} USDT | {px}\n"
                 f"   Phí {fee} USDT | {dot(x['pnl'])} {x['pct']:+.2f}% | {x['pnl']:+.2f} USDT{tag}")
        R.append([B(x["acc"]), [B(f"{side_vn(x['side'])} {x['symbol']}"), f" x{x['lev']}\nSize {x['usd']:.2f} USDT\n{px}"],
                  fee, f"{dot(x['pnl'])} {x['pct']:+.2f}%", B(f"{x['pnl']:+.2f}{'*' if x['est'] else ''}")])
        log(f"✅ {x['acc']}: đóng {x['symbol']} | phí {fee} | {x['pct']:+.2f}% | {x['pnl']:+.2f} USDT{tag}")
    blocks = [r_head(f"🛑 Đã đóng {len(done)}/{len(rows)} position")]
    if done:
        ft = f"{sum(fees):.2f}" if fees else "—"
        note = ("* PnL ước tính theo giá lúc đóng, chưa trừ phí (Bybit chưa trả số liệu)" if est
                else "PnL đã trừ phí mở + đóng. Đơn vị: USDT.")
        T.append(f"Tổng phí {ft} USDT | Tổng PnL {dot(tot)} {tot:+.2f} USDT\n({note})")
        R.append([B("Tổng"), "", B(ft), dot(tot), B(f"{tot:+.2f}")])
        blocks.append(r_table(POS_HEAD, R, POS_ALIGN))
        blocks.append(r_foot(note))
    for e in errs:
        blocks.append(r_par(e))
    rl = realized_lines(always=True)
    if prev_n and rl and done:         # truoc do da dong 1 phan -> bao tong ca dot
        rz = cfg["realized"]
        T.append(f"Cả đợt (gồm các lần đóng một phần): {rl[1]} | {rl[2]}")
        blocks.append(r_table(["Cả đợt (gồm các lần đóng một phần)", "USDT"],
                              [[rl[1].split(" = ")[0], B(f"{dot(rz['pnl'])}\u00a0{rz['pnl']:+.2f}")],
                               ["Total fee", B(f"{rz['fee']:.2f}")]], [None, "right"]))
    return "\n".join(T), blocks


def status_text():
    lines = [f"Bot: {'🟢 ĐANG CHẠY' if cfg['running'] else '🔴 ĐANG DỪNG'} | "
             f"{'Theo kênh' if cfg['mode'] == 'follow' else 'Custom'} | Đòn bẩy: {lev_label()}"]
    rl = realized_lines()
    if rl:
        lines += [rl[0] + ":", "   " + rl[1], "   " + rl[2]]
    tot = 0.0
    for c in clients:
        st = status.get(c.name) or {}
        bal = f" | Avai {st['balance']:.2f} USDT" if st.get("balance") is not None else ""
        if st.get("error"):
            lines.append(f"{c.name}: ⚠️ {st['error']}")
        elif not st.get("positions"):
            lines.append(f"{c.name}: No Position{bal}")
        else:
            for p in st["positions"]:
                tot += p["pnl"]
                lines.append(f"{c.name}: {side_vn(p['side'])} {p['symbol']} x{p['lev']}\n"
                             f"   Size {float(p['size']) * p['avg']:.2f} USDT | entry {num(p['avg'])} | phí {p.get('fee', 0):.2f}\n"
                             f"   {dot(p['pnl'])} {p['pct']:+.2f}% | {p['pnl']:+.2f} USDT")
    if any((status.get(c.name) or {}).get("positions") for c in clients):
        lines.append(f"Tổng PnL đang mở: {dot(tot)} {tot:+.2f} USDT")
    return "\n".join(lines)


def status_blocks(title=None, stamp=None):
    run = cfg["running"]
    blocks = [r_head(f"{title or '📊 Trạng thái'} — {'🟢 ĐANG CHẠY' if run else '🔴 ĐANG DỪNG'}"),
              r_par(["Chế độ: ", B("Theo lệnh kênh" if cfg["mode"] == "follow" else "Chỉ theo coin (custom)"),
                     " · Đòn bẩy: ", B(lev_label())])]
    rl = realized_lines()
    if rl:
        rz = cfg["realized"]
        blocks.append(r_table(["Realized PnL", "USDT"],
                              [["PnL (ước tính, chưa gồm phí)" if rz.get("est") else "PnL (đã gồm phí)",
                                B(f"{dot(rz['pnl'])}\u00a0{rz['pnl']:+.2f}")],
                               ["Total fee", B(f"{rz['fee']:.2f}")]], [None, "right"]))
    R, tot, has = [], 0.0, False
    for c in clients:
        st = status.get(c.name) or {}
        if st.get("error"):
            R.append([B(c.name), f"⚠️ {st['error']}", "", "", ""])
        elif not st.get("positions"):
            bal = f"No Position\nAvai {st['balance']:.2f} USDT" if st.get("balance") is not None else "No Position"
            R.append([B(c.name), bal, "", "", ""])
        else:
            for p in st["positions"]:
                has = True
                tot += p["pnl"]
                R.append([B(c.name), [B(f"{side_vn(p['side'])} {p['symbol']}"),
                                      f" x{p['lev']}\nSize {float(p['size']) * p['avg']:.2f} USDT\nEntry {num(p['avg'])}"],
                          f"{p.get('fee', 0):.2f}", f"{dot(p['pnl'])} {p['pct']:+.2f}%", B(f"{p['pnl']:+.2f}")])
    if has:
        R.append([B("Tổng"), "", "", dot(tot), B(f"{tot:+.2f}")])
    if R:
        blocks.append(r_table(POS_HEAD, R, POS_ALIGN))
    else:
        blocks.append(r_par("Chưa cài sub account nào."))
    if stamp:
        blocks.append(r_foot(stamp))
    return blocks


async def status_loop():
    async def one(c):
        try:
            bal, pos = await asyncio.gather(c.balance(), c.positions())
            status[c.name] = {"balance": bal, "positions": pos, "error": "", "t": time.time(),
                              "equity": getattr(c, "equity", None)}
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
            if clients and not busy["n"] and (cfg.get("realized") or {}).get("n") and not has_pos() \
                    and all((status.get(c.name) or {}).get("t", 0) > time.time() - 10 and
                            not (status.get(c.name) or {}).get("error") for c in clients):
                cfg["realized"] = {"pnl": 0.0, "fee": 0.0, "n": 0}   # dot position da dong het
                save_cfg()
            record_balance()
            if n % 20 == 0:    # ~1 phut: dong ho may co the bi Windows chinh lai bat cu luc nao
                await sync_time()
            if n % 200 == 0:   # ~10 phut
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


ALLIN_RE = re.compile(r"^/(?:buyall|sellall)(?:@\w+)?\s+#?([A-Za-z0-9]+)\s+(\d+(?:[.,]\d+)?)\s+(\d+(?:[.,]\d+)?)\s*$", re.I)


def parse_allin(text):
    m = ALLIN_RE.match((text or "").strip())
    if not m:
        return None
    f = lambda x: float(x.replace(",", "."))
    return {"coin": m.group(1).upper(), "tp": f(m.group(2)), "sl": f(m.group(3))}


HELP_ITEMS = [
    ("/start", "Chạy bot — bắt đầu nghe lệnh từ kênh"),
    ("/stop", "Dừng bot — position đang mở giữ nguyên"),
    ("/status", "Xem position, phí và PnL từng acc — tin tự cập nhật liên tục, kèm chart nến 1m khi có position"),
    ("/per", "Performance của các acc: 1 day / This week / This Month, và Position History"),
    ("/buy #coin size tp sl", "Mở Long ngay trên tất cả acc. size = USDT, tp/sl = % so với entry. Vd: /buy #eth 1000 10 2"),
    ("/sell #coin size tp sl", "Mở Short ngay trên tất cả acc (ngược với /buy). TP khi giá giảm tp%, SL khi giá tăng sl%. Vd: /sell #eth 1000 10 2"),
    ("/buyall #coin tp sl", "Mở Long toàn bộ vốn mỗi acc với đòn bẩy max của coin — size lớn nhất có thể. Vd: /buyall #evaa 10 2"),
    ("/sellall #coin tp sl", "Mở Short toàn bộ vốn mỗi acc với đòn bẩy max của coin (ngược với /buyall). Vd: /sellall #evaa 10 2"),
    ("/lev N", "Đặt đòn bẩy cho /buy, /sell và lệnh kênh. Vd: /lev 10 — hoặc /lev max = max của coin"),
    ("/close", "Market close toàn bộ position, báo phí và PnL"),
    ("/update", "Cập nhật tool lên bản mới nhất và gửi change log"),
    ("/help", "Hiện danh sách lệnh này"),
]
HELP_TEXT = "📖 Các lệnh:\n" + "\n".join(f"{c} — {d}" for c, d in HELP_ITEMS)


def help_blocks():
    return [r_head(f"📖 Các lệnh — v{VERSION}"),
            r_table(["Lệnh", "Tác dụng"], [[K(c), d] for c, d in HELP_ITEMS])]


BUY_RE = re.compile(r"^/(?:buy|sell)(?:@\w+)?\s+#?([A-Za-z0-9]+)\s+(\d+(?:[.,]\d+)?)\s+(\d+(?:[.,]\d+)?)\s+(\d+(?:[.,]\d+)?)\s*$", re.I)


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


async def _send(chat, text, kb=None):
    extra = {"reply_markup": kb} if kb else {}
    for attempt in range(1, 5):
        r = await bot_api("sendMessage", _quiet=True, chat_id=chat, text=text[:4000], **extra)
        if r.get("ok"):
            if attempt > 1:
                log(f"Bot đã gửi được tin sau {attempt} lần thử (mạng tới Telegram chập chờn)")
            return (r.get("result") or {}).get("message_id"), False
        desc = str(r.get("description"))
        if "Timeout" not in desc and "Connect" not in desc and "Disconnected" not in desc:
            break                      # loi tu Telegram (khong phai mang) -> thu lai vo ich
    log(f"⚠️ Bot không gửi được tin trả lời: {desc}")
    return None, False


async def _send_rich(chat, text, blocks, kb=None):
    """Thu gui Rich Message; khong duoc thi gui ban chu."""
    extra = {"reply_markup": kb} if kb else {}
    if cfg.get("widgets", True) and botst.get("rich") is not False:
        for _ in range(3):
            r = await bot_api("sendRichMessage", _quiet=True, chat_id=chat, rich_message={"blocks": blocks}, **extra)
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
    return await _send(chat, text, kb)


# --- /status tu cap nhat: tool sua thang vao tin /status moi nhat ---
live = {"chat": None, "mid": None, "rich": True, "sig": "", "t": 0.0, "wait": 0.0, "confirm": None}
CLOSE_PCTS = [10, 30, 50, 70, 100]
CONFIRM_SECS = 15


def live_kb():
    """Ban phim duoi tin /status: chon % -> hien nut Xac nhan trong 15 giay."""
    if not has_pos():
        return None
    cf = live.get("confirm")
    if cf and cf[1] > time.time():
        return {"inline_keyboard": [
            [{"text": f"⚠️ Đóng {cf[0]}% TẤT CẢ position?", "callback_data": "noop"}],
            [{"text": f"✅ Xác nhận đóng {cf[0]}%", "callback_data": f"ok:{cf[0]}"},
             {"text": "✖ Huỷ", "callback_data": "no"}]]}
    return {"inline_keyboard": [
        [{"text": "Close Partial Position", "callback_data": "noop"}],
        [{"text": f"{p}%", "callback_data": f"cp:{p}"} for p in CLOSE_PCTS]]}


def live_refresh_now():
    live.update(sig="", t=0.0, wait=0.0)


async def handle_callback(cq):
    """Bam nut duoi tin /status."""
    async def answer(text="", alert=False):
        await bot_api("answerCallbackQuery", _quiet=True, callback_query_id=cq["id"], text=text[:190], show_alert=alert)
    if str((cq.get("from") or {}).get("id")) != str(cfg["bot_owner_id"]).strip():
        return await answer("Bạn không có quyền dùng bot này", True)
    data = cq.get("data") or ""
    mid = (cq.get("message") or {}).get("message_id")
    if data == "noop":
        return await answer()
    if data == "ph" or data.startswith("pf:"):
        kind = "h" if data == "ph" else data[3:]
        if kind not in ("d", "w", "m", "h"):
            return await answer()
        await answer("Đang tải…")
        return await per_edit((cq.get("message") or {}).get("chat", {}).get("id") or cfg["bot_owner_id"], mid, kind)
    if mid != live["mid"]:
        return await answer("Tin này đã cũ — gõ /status để có tin mới", True)
    if data == "no":
        live["confirm"] = None
        live_refresh_now()
        return await answer("Đã huỷ")
    kind, _, val = data.partition(":")
    try:
        pct = int(val)
    except ValueError:
        return await answer()
    if pct not in CLOSE_PCTS:
        return await answer()
    if kind == "cp":
        live["confirm"] = (pct, time.time() + CONFIRM_SECS)
        live_refresh_now()
        return await answer(f"Bấm ✅ Xác nhận trong {CONFIRM_SECS} giây để đóng {pct}%")
    if kind == "ok":
        cf = live.get("confirm")
        if not cf or cf[0] != pct or cf[1] < time.time():
            live["confirm"] = None
            live_refresh_now()
            return await answer("Hết thời gian xác nhận — bấm lại % muốn đóng", True)
        live["confirm"] = None
        log(f"✂️ Đóng {pct}% position (nút dưới /status)")
        await answer(f"Đang đóng {pct}%…")
        if pct == 100:
            send_rich(live["chat"] or cfg["bot_owner_id"], *(await close_all()))
            live_refresh_now()
            return
        msg = await close_partial(pct)
        live_refresh_now()
        if "Lỗi" in msg or "Không có" in msg:
            send(live["chat"] or cfg["bot_owner_id"], "✂️ " + msg)

LIVE_EVERY = 3         # giay giua 2 lan sua tin (khi so lieu thay doi)
LIVE_BEAT = 60         # so lieu khong doi van sua moi 60s de thay gio cap nhat


def live_sig():
    return json.dumps([status_blocks(), live_kb()], ensure_ascii=False) + f"|{live.get('png_v', 0) if live.get('png') else 0}"


def live_stamp():
    return f"Last Update: {datetime.now().strftime('%H:%M:%S')}"


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
    live["confirm"] = None
    mid, rich = await _send_rich(chat, status_text() + "\n" + live_stamp(), status_blocks(stamp=live_stamp()), live_kb())
    if mid:
        live.update(chat=chat, mid=mid, rich=rich, t=time.time(), wait=0.0, chart_off=False,
                    sig=json.dumps([status_blocks(), live_kb()], ensure_ascii=False) + "|0")   # "|0": chua kem bieu do
        cfg["live_msg"] = [chat, mid, rich]
        save_cfg()


async def live_edit(chat, mid, rich, final=False):
    stamp = "⏹ Đã ngừng cập nhật — xem tin /status mới hơn" if final else live_stamp()
    p = {"chat_id": chat, "message_id": mid}
    kb = None if final else live_kb()
    if kb:
        p["reply_markup"] = kb             # sua tin ma khong gui kem thi Telegram xoa mat nut
    png = None if final else live.get("png")
    if rich and png and not live.get("chart_off"):         # kem bieu do nen 1m ngay duoi tieu de
        blocks = status_blocks(stamp=stamp)
        f = {"chat_id": str(chat), "message_id": str(mid), "rich_message": {"blocks": [blocks[0], PHOTO_BLOCK] + blocks[1:]}}
        if kb:
            f["reply_markup"] = kb
        r = await bot_form("editMessageText", f, {"chart": png})
        desc = str(r.get("description") or "")
        if r.get("ok") or "not modified" in desc or _net_err(desc) or "Too Many Requests" in desc or "retry after" in desc.lower():
            return r
        live["chart_off"] = True
        log(f"/status: Telegram không nhận biểu đồ trong tin ({desc[:100]}) — tiếp tục cập nhật không kèm biểu đồ")
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
            if live.get("confirm") and live["confirm"][1] < now:
                live["confirm"] = None     # het han xac nhan -> tra lai hang nut %
            if busy["n"] and live.get("png"):
                continue                   # dang vao/dong lenh: khong tai anh len luc nay
            sig = live_sig()
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


# --- Nhat ky balance (de ve bieu do trong /per) ---
BAL_LOG = os.path.join(BASE_DIR, "balance_log.csv")
BAL_EVERY = 300            # ghi 5 phut 1 lan
bal_hist = []              # [(unix_ts, total balance trung binh cua cac acc)]


def load_balance_log():
    bal_hist.clear()
    try:
        cutoff = time.time() - 45 * 86400
        with open(BAL_LOG, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    t, v = line.strip().split(",")[:2]
                    if float(t) >= cutoff:
                        bal_hist.append((float(t), float(v)))
                except Exception:
                    continue
    except FileNotFoundError:
        pass
    except Exception as e:
        log(f"Không đọc được balance_log.csv: {e}")


def record_balance():
    """Goi moi vong status: ghi trung binh total balance neu MOI acc deu vua co so lieu tot."""
    if not clients or (bal_hist and time.time() - bal_hist[-1][0] < BAL_EVERY):
        return
    vals = []
    for c in clients:
        st = status.get(c.name) or {}
        if st.get("error") or st.get("equity") is None or time.time() - st.get("t", 0) > 15:
            return                     # thieu 1 acc -> bo qua de duong bieu do khong bi tut gia
        vals.append(st["equity"])
    pt = (time.time(), sum(vals) / len(vals))
    bal_hist.append(pt)
    try:
        with open(BAL_LOG, "a", encoding="utf-8") as f:
            f.write(f"{pt[0]:.0f},{pt[1]:.4f}\n")
    except Exception as e:
        log(f"Không ghi được balance_log.csv: {e}")


# Font 5x7 cho chu so va vai ky tu, de ve nhan truc ma khong can thu vien ngoai
_FONT = {
    "0": "01110 10001 10011 10101 11001 10001 01110", "1": "00100 01100 00100 00100 00100 00100 01110",
    "2": "01110 10001 00001 00010 00100 01000 11111", "3": "11110 00001 00001 01110 00001 00001 11110",
    "4": "00010 00110 01010 10010 11111 00010 00010", "5": "11111 10000 11110 00001 00001 10001 01110",
    "6": "00110 01000 10000 11110 10001 10001 01110", "7": "11111 00001 00010 00100 01000 01000 01000",
    "8": "01110 10001 10001 01110 10001 10001 01110", "9": "01110 10001 10001 01111 00001 00010 01100",
    ".": "00000 00000 00000 00000 00000 01100 01100", ":": "00000 01100 01100 00000 01100 01100 00000",
    "/": "00001 00001 00010 00100 01000 10000 10000", "-": "00000 00000 00000 11111 00000 00000 00000",
    " ": "00000 00000 00000 00000 00000 00000 00000",
}


def render_chart(points, ticks, W=900, H=420):
    """points = [(ts, value)] tang dan theo ts; ticks = [(ts, nhan)] cho truc ngang. -> bytes PNG"""
    L, R, T, Bm = 104, 24, 22, 46            # le trai/phai/tren/duoi
    buf = bytearray(b"\xff" * (W * H * 3))

    def px(x, y, col):
        if 0 <= x < W and 0 <= y < H:
            i = (y * W + x) * 3
            buf[i:i + 3] = col

    def hline(x0, x1, y, col):
        for x in range(x0, x1 + 1):
            px(x, y, col)

    def vline(x, y0, y1, col):
        for y in range(y0, y1 + 1):
            px(x, y, col)

    def text(x, y, s, col, sc=2):
        for ch in s:
            g = _FONT.get(ch, _FONT[" "]).split()
            for r, row in enumerate(g):
                for c, bit in enumerate(row):
                    if bit == "1":
                        for dy in range(sc):
                            for dx in range(sc):
                                px(x + c * sc + dx, y + r * sc + dy, col)
            x += 6 * sc

    def tw(s, sc=2):
        return len(s) * 6 * sc

    GRID, AXIS, TXT, LINE, FILL = b"\xe6\xe9\xee", b"\x9a\xa3\xaf", b"\x4a\x52\x5e", b"\x2f\x7f\xe0", b"\xe6\xf0\xfc"
    t0, t1 = ticks[0][0], ticks[-1][0]
    vals = [v for _, v in points]
    lo, hi = min(vals), max(vals)
    pad = (hi - lo) * 0.15
    lo, hi = lo - pad, hi + pad
    span = max(abs(hi) * 0.01, 0.4)          # bien do toi thieu: balance gan nhu dung yen -> duong nam ngang, moc khong lap
    if hi - lo < span:
        mid = (hi + lo) / 2
        lo, hi = mid - span / 2, mid + span / 2
    X = lambda t: L + int((t - t0) / (t1 - t0) * (W - L - R))
    Y = lambda v: T + int((hi - v) / (hi - lo) * (H - T - Bm))
    dec = 2 if hi - lo < 50 else (1 if hi - lo < 500 else 0)
    for k in range(5):                       # luoi ngang + nhan truc doc
        v = lo + (hi - lo) * k / 4
        y = Y(v)
        hline(L, W - R, y, GRID)
        lab = f"{v:.{dec}f}"
        text(L - 10 - tw(lab), y - 7, lab, TXT)
    for ts, lab in ticks:                    # luoi doc + nhan truc ngang
        x = X(ts)
        vline(x, T, H - Bm, GRID)
        text(min(max(x - tw(lab) // 2, 2), W - tw(lab) - 2), H - Bm + 12, lab, TXT)
    hline(L, W - R, H - Bm, AXIS)
    vline(L, T, H - Bm, AXIS)
    pts = [(X(t), Y(v)) for t, v in points if t0 <= t <= t1]
    base = H - Bm - 1
    for (xa, ya), (xb, yb) in zip(pts, pts[1:]):         # to nhe phan duoi duong
        for x in range(xa, max(xb, xa + 1)):
            y = ya + (yb - ya) * (x - xa) // max(xb - xa, 1)
            for yy in range(y + 2, base + 1):
                i = (yy * W + x) * 3
                if buf[i:i + 3] == b"\xff\xff\xff":
                    buf[i:i + 3] = FILL
    for (xa, ya), (xb, yb) in zip(pts, pts[1:]):         # duong line day 3px
        n = max(abs(xb - xa), abs(yb - ya), 1)
        for k in range(n + 1):
            x, y = xa + (xb - xa) * k // n, ya + (yb - ya) * k // n
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    px(x + dx, y + dy, LINE)
    if pts:                                  # cham tron o diem cuoi + gia tri hien tai
        xe, ye = pts[-1]
        for dy in range(-4, 5):
            for dx in range(-4, 5):
                if dx * dx + dy * dy <= 16:
                    px(xe + dx, ye + dy, LINE)
        lab = f"{points[-1][1]:.2f}"
        text(min(max(xe - tw(lab) - 8, L + 4), W - R - tw(lab)), max(ye - 22, T + 2), lab, LINE)

    raw = b"".join(b"\x00" + bytes(buf[y * W * 3:(y + 1) * W * 3]) for y in range(H))

    def chunk(tag, data):
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xffffffff)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw, 6)) + chunk(b"IEND", b""))


def chart_for(kind):
    """-> (png | None, ghi chu). 1 day / history: 24h, moc 4 gio. Week / month: moc theo ngay."""
    now = datetime.now()
    if kind in ("d", "h"):
        end = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
        end += timedelta(hours=(-end.hour) % 4)                      # tron len moc 4 gio
        start = end - timedelta(hours=24)
        ticks = [(start + timedelta(hours=4 * i)) for i in range(7)]
        ticks = [(t.timestamp(), t.strftime("%H:%M")) for t in ticks]
    else:
        end = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        if kind == "w":
            start = end - timedelta(days=now.weekday() + 1)
            step = 1
        else:
            start = end.replace(day=1) if end.day != 1 else (end - timedelta(days=1)).replace(day=1)
            step = 5
        days = max((end - start).days, 1)
        ts = [start + timedelta(days=i) for i in range(0, days + 1, step)]
        if ts[-1] != end:
            ts.append(end)
        ticks = [(t.timestamp(), t.strftime("%d/%m")) for t in ts]
    pts = [(t, v) for t, v in bal_hist if ticks[0][0] <= t <= ticks[-1][0]]
    if len(pts) > 450:                       # gop bot diem cho nhe
        k = len(pts) // 400 + 1
        pts = [(sum(t for t, _ in pts[i:i + k]) / len(pts[i:i + k]), sum(v for _, v in pts[i:i + k]) / len(pts[i:i + k]))
               for i in range(0, len(pts), k)]
    if len(pts) < 2:
        since = datetime.fromtimestamp(bal_hist[0][0]).strftime("%d/%m %H:%M") if bal_hist else "bây giờ"
        return None, f"Biểu đồ: chưa đủ dữ liệu (ghi 5 phút/lần từ {since})"
    since = datetime.fromtimestamp(bal_hist[0][0]).strftime("%d/%m %H:%M")
    return render_chart(pts, ticks), f"Biểu đồ: balance TB mỗi acc, từ {since}"


# --- /status: bieu do nen 1 phut cua coin dang co position ---
_FONT.update({
    "A": "01110 10001 10001 11111 10001 10001 10001", "B": "11110 10001 10001 11110 10001 10001 11110",
    "C": "01110 10001 10000 10000 10000 10001 01110", "D": "11110 10001 10001 10001 10001 10001 11110",
    "E": "11111 10000 10000 11110 10000 10000 11111", "F": "11111 10000 10000 11110 10000 10000 10000",
    "G": "01110 10001 10000 10111 10001 10001 01111", "H": "10001 10001 10001 11111 10001 10001 10001",
    "I": "01110 00100 00100 00100 00100 00100 01110", "J": "00111 00010 00010 00010 00010 10010 01100",
    "K": "10001 10010 10100 11000 10100 10010 10001", "L": "10000 10000 10000 10000 10000 10000 11111",
    "M": "10001 11011 10101 10101 10001 10001 10001", "N": "10001 11001 10101 10011 10001 10001 10001",
    "O": "01110 10001 10001 10001 10001 10001 01110", "P": "11110 10001 10001 11110 10000 10000 10000",
    "Q": "01110 10001 10001 10001 10101 10010 01101", "R": "11110 10001 10001 11110 10100 10010 10001",
    "S": "01111 10000 10000 01110 00001 00001 11110", "T": "11111 00100 00100 00100 00100 00100 00100",
    "U": "10001 10001 10001 10001 10001 10001 01110", "V": "10001 10001 10001 10001 10001 01010 00100",
    "W": "10001 10001 10001 10101 10101 10101 01010", "X": "10001 10001 01010 00100 01010 10001 10001",
    "Y": "10001 10001 01010 00100 00100 00100 00100", "Z": "11111 00001 00010 00100 01000 10000 11111",
})
CHART_EVERY = 15           # giay giua 2 lan lay nen 1m + ve lai
CHART_BARS = 60            # so nen 1 phut tren bieu do
C_UP, C_DOWN, C_ENTRY = b"\x26\xa6\x9a", b"\xef\x53\x50", b"\x2f\x7f\xe0"
C_TP, C_SL = b"\x1b\x8a\x5a", b"\xd6\x3b\x3b"


def price_dec(symbol):
    """So chu so sau dau cham khi in gia: gia >= 1 -> 2; gia nho -> theo buoc gia cua san."""
    try:
        return min(8, max(2, -instruments[symbol]["tick"].as_tuple().exponent))
    except Exception:
        return 4


def render_candles(candles, marks, title, dec=2, W=900, H=480):
    """candles = [(ts, o, h, l, c)] tang dan; marks = [(nhan, gia, mau)] -> bytes PNG"""
    L, R, T, Bm = 14, 124, 44, 40
    buf = bytearray(b"\xff" * (W * H * 3))

    def px(x, y, col):
        if 0 <= x < W and 0 <= y < H:
            i = (y * W + x) * 3
            buf[i:i + 3] = col

    def rect(x0, y0, x1, y1, col):
        x0, x1 = max(0, x0), min(W - 1, x1)
        for y in range(max(0, y0), min(H - 1, y1) + 1):
            i = (y * W + x0) * 3
            buf[i:i + (x1 - x0 + 1) * 3] = col * (x1 - x0 + 1)

    def text(x, y, s, col, sc=2):
        for ch in s:
            g = _FONT.get(ch, _FONT[" "]).split()
            for r, row in enumerate(g):
                for c, bit in enumerate(row):
                    if bit == "1":
                        rect(x + c * sc, y + r * sc, x + c * sc + sc - 1, y + r * sc + sc - 1, col)
            x += 6 * sc

    tw = lambda s, sc=2: len(s) * 6 * sc
    pl = lambda v: f"{v:.2f}" if abs(v) >= 1 else f"{v:.{dec}f}"
    GRID, AXIS, TXT, WHITE = b"\xee\xf0\xf3", b"\x9a\xa3\xaf", b"\x4a\x52\x5e", b"\xff\xff\xff"
    lo, hi = min(c[3] for c in candles), max(c[2] for c in candles)
    span0 = max(hi - lo, abs(hi) * 0.001)
    for _, v, _ in marks:                    # vach Entry/TP/SL chi keo rong truc khi nam gan vung gia
        if lo - span0 * 1.5 <= v <= hi + span0 * 1.5:
            lo, hi = min(lo, v), max(hi, v)
    pad = max(hi - lo, abs(hi) * 0.001) * 0.08
    lo, hi = lo - pad, hi + pad
    pw, ph = W - L - R, H - T - Bm
    Y = lambda v: T + int((hi - v) / (hi - lo) * ph)
    slot = pw / max(len(candles), 1)
    bw = max(2, int(slot * 0.62))
    X = lambda i: L + int(slot * i + slot / 2)
    for k in range(5):                       # luoi ngang + gia ben phai
        v = lo + (hi - lo) * k / 4
        rect(L, Y(v), W - R, Y(v), GRID)
        text(W - R + 10, Y(v) - 7, pl(v), TXT)
    for i, c in enumerate(candles):          # luoi doc + gio moi 15 phut
        d = datetime.fromtimestamp(c[0])
        if d.minute % 15 == 0:
            rect(X(i), T, X(i), H - Bm, GRID)
            lab = d.strftime("%H:%M")
            text(min(max(X(i) - tw(lab) // 2, 2), W - R - tw(lab)), H - Bm + 12, lab, TXT)
    rect(L, H - Bm, W - R, H - Bm, AXIS)
    rect(W - R, T, W - R, H - Bm, AXIS)
    for i, (_, o, h, l, c) in enumerate(candles):
        col = C_UP if c >= o else C_DOWN
        x = X(i)
        rect(x, Y(h), x + 1, Y(l), col)                                 # rau nen
        ya, yb = sorted((Y(o), Y(c)))
        rect(x - bw // 2 + 1, ya, x - bw // 2 + bw, max(yb, ya + 1), col)   # than nen
    tags = [(lab, v, col) for lab, v, col in marks if lo <= v <= hi]
    last = candles[-1][4]
    tags.append(("", last, C_UP if last >= candles[-1][1] else C_DOWN))
    for lab, v, col in tags:
        y = Y(v)
        if lab:
            for x in range(L, W - R, 10):    # duong gach ngang
                rect(x, y, x + 5, y + 1, col)
            text(L + 6, y - 18 if y - 18 > T else y + 6, lab, col)
        rect(W - R + 1, y - 10, W - 2, y + 10, col)                     # nhan gia tren truc
        text(W - R + 10, y - 7, pl(v), WHITE)
    text(L + 2, 14, title, TXT)
    raw = b"".join(b"\x00" + bytes(buf[y * W * 3:(y + 1) * W * 3]) for y in range(H))

    def chunk(tag, data):
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xffffffff)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw, 6)) + chunk(b"IEND", b""))


def chart_target():
    """Coin de ve: coin co tong size (USDT) lon nhat trong cac position dang mo. -> dict | None"""
    agg = {}
    for c in clients:
        for p in (status.get(c.name) or {}).get("positions") or []:
            try:
                size = float(p["size"])
                a = agg.setdefault(p["symbol"], {"usd": 0.0, "qty": 0.0, "val": 0.0, "side": {}, "tp": [], "sl": []})
                a["usd"] += size * p["avg"]; a["qty"] += size; a["val"] += size * p["avg"]
                a["side"][p["side"]] = a["side"].get(p["side"], 0) + size * p["avg"]
                for k in ("tp", "sl"):
                    v = float(p.get(k) or 0)
                    if v > 0:
                        a[k].append(v)
            except Exception:
                continue
    if not agg:
        return None
    sym, a = max(agg.items(), key=lambda kv: kv[1]["usd"])
    avg = lambda xs: sum(xs) / len(xs) if xs else None
    return {"symbol": sym, "side": max(a["side"], key=a["side"].get), "entry": a["val"] / a["qty"] if a["qty"] else None,
            "tp": avg(a["tp"]), "sl": avg(a["sl"])}


def chart_png(tg, candles):
    dec = price_dec(tg["symbol"])
    pl = lambda v: f"{v:.2f}" if abs(v) >= 1 else f"{v:.{dec}f}"
    marks, title = [], f"{tg['symbol']} 1M  {side_vn(tg['side']).upper()}"
    for lab, key, col in (("ENTRY", "entry", C_ENTRY), ("TP", "tp", C_TP), ("SL", "sl", C_SL)):
        if tg.get(key):
            marks.append((lab, tg[key], col))
            title += f"  {lab} {pl(tg[key])}"
    return render_candles(candles, marks, title, dec)


async def fetch_candles(symbol):
    r = await asyncio.wait_for(public_client().req("GET", "/v5/market/kline", {
        "category": "linear", "symbol": symbol, "interval": "1", "limit": str(CHART_BARS)}, auth=False), 8)
    rows = sorted((r.get("result") or {}).get("list") or [], key=lambda x: int(x[0]))
    return [(int(x[0]) / 1000, float(x[1]), float(x[2]), float(x[3]), float(x[4])) for x in rows]


async def chart_loop():
    """Giu san anh bieu do nen 1m cho tin /status dang tu cap nhat. Het position -> bo anh."""
    nxt = 0.0
    while True:
        await asyncio.sleep(1)
        try:
            on = live["mid"] and live["rich"] and cfg["bot_token"] and not live.get("chart_off")
            tg = chart_target() if on else None
            if not tg:
                if live.get("png"):
                    live.update(png=None, png_sym=None, png_v=live.get("png_v", 0) + 1)
                nxt = 0.0
                continue
            now = time.time()
            if busy["n"] or (now < nxt and live.get("png_sym") == tg["symbol"]):
                continue                     # dang vao/dong lenh -> nhuong duong
            nxt = now + 5                    # loi thi 5 giay sau thu lai
            candles = await fetch_candles(tg["symbol"])
            if len(candles) < 2:
                continue
            if time.time() - prices["t"] <= PRICE_MAX_AGE and tg["symbol"] in prices["map"]:
                t, o, h, l, _ = candles[-1]  # nen cuoi theo gia moi nhat
                px = float(prices["map"][tg["symbol"]])
                candles[-1] = (t, o, max(h, px), min(l, px), px)
            png = await asyncio.to_thread(chart_png, tg, candles)
            live.update(png=png, png_sym=tg["symbol"], png_v=live.get("png_v", 0) + 1)
            nxt = time.time() + CHART_EVERY
        except Exception as e:
            log(f"chart 1m: {type(e).__name__}: {str(e)[:100]}")
            nxt = time.time() + 10


# --- /per: performance + lich su position (lay tu lich su dong lenh cua Bybit) ---
PER_LABEL = {"d": "1 day", "w": "This week", "m": "This Month"}
_per_cache = {}            # (ten acc, start_ms) -> (luc lay, records)
WEEK_MS = 7 * 86400 * 1000


def per_start(kind):
    """Moc bat dau (ms, gio Bybit) + mo ta."""
    now = datetime.now()
    if kind == "d":
        t, desc = time.time() - 86400, "24 giờ qua"
    elif kind == "w":
        d0 = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
        t, desc = d0.timestamp(), f"từ thứ Hai {d0.strftime('%d/%m')}"
    else:
        d0 = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        t, desc = d0.timestamp(), f"từ {d0.strftime('%d/%m')}"
    return int(t * 1000) + time_offset, desc


async def fetch_closed(c, start_ms):
    """Moi lan dong lenh cua 1 acc tu start_ms toi gio. Bybit chi cho hoi toi da 7 ngay moi lan."""
    key = (c.name, start_ms // 60000)
    hit = _per_cache.get(key)
    if hit and time.time() - hit[0] < 20:
        return hit[1]
    end = int(time.time() * 1000) + time_offset
    out, t = [], start_ms
    while t < end:
        e, cursor = min(t + WEEK_MS - 1000, end), ""
        for _ in range(10):                # toi da 1000 ban ghi moi tuan
            p = {"category": "linear", "startTime": str(t), "endTime": str(e), "limit": "100"}
            if cursor:
                p["cursor"] = cursor
            r = await c.req("GET", "/v5/position/closed-pnl", p)
            if r.get("retCode") != 0:
                raise RuntimeError(str(r.get("retMsg")))
            out += r["result"]["list"]
            cursor = r["result"].get("nextPageCursor") or ""
            if not cursor:
                break
        t = e + 1
    _per_cache[key] = (time.time(), out)
    return out


def _rec(it):
    return {"symbol": it["symbol"], "side": "Buy" if it.get("side") == "Sell" else "Sell",   # lenh dong Sell = position Long
            "size": float(it.get("cumEntryValue") or 0),     # gia tri USDT cua phan da dong, tinh theo gia entry
            "pnl": float(it.get("closedPnl") or 0),
            "fee": float(it.get("openFee") or 0) + float(it.get("closeFee") or 0),
            "t": int(it.get("updatedTime") or it.get("createdTime") or 0)}


def per_kb(sel):
    row = [{"text": ("• " if sel == k else "") + v, "callback_data": f"pf:{k}"} for k, v in PER_LABEL.items()]
    return {"inline_keyboard": [row, [{"text": ("• " if sel == "h" else "") + "Position History", "callback_data": "ph"}]]}


def per_view(kind, data, desc):
    """data = [(ten acc, records | Exception)] -> (ban chu, blocks)"""
    title = f"📈 Performance — {PER_LABEL[kind]}"
    T, R = [title + f" ({desc})"], []
    tn = tw = 0
    tp = tf = 0.0
    for name, recs in data:
        if isinstance(recs, Exception):
            T.append(f"{name}: ⚠️ {recs}")
            R.append([B(name), f"⚠️ {str(recs)[:60]}", "", ""])
            continue
        rs = [_rec(x) for x in recs]
        n, w = len(rs), sum(1 for x in rs if x["pnl"] > 0)
        pnl, fee = sum(x["pnl"] for x in rs), sum(x["fee"] for x in rs)
        tn, tw, tp, tf = tn + n, tw + w, tp + pnl, tf + fee
        wr = f"{w / n * 100:.0f}%" if n else "—"
        T.append(f"{name}: {n} lệnh | win {wr} | {dot(pnl)} {pnl:+.2f} USDT | fee {fee:.2f}")
        R.append([B(name), str(n), wr, B(f"{dot(pnl)}\u00a0{pnl:+.2f}")])
    wr = f"{tw / tn * 100:.0f}%" if tn else "—"
    T.append(f"Tổng: {tn} lệnh | win {wr} | {dot(tp)} {tp:+.2f} USDT | fee {tf:.2f}")
    R.append([B("Tổng"), B(str(tn)), B(wr), B(f"{dot(tp)}\u00a0{tp:+.2f}")])
    stamp = f"PnL đã gồm phí · USDT · Last Update: {datetime.now().strftime('%H:%M:%S')}"
    T.append(stamp)
    blocks = [r_head(title),
              r_table(["Acc", "Lệnh", "Win", "PnL"], R, [None, "right", "right", "right"]),
              r_foot(stamp)]
    return "\n".join(T), blocks


def history_view(data, limit=5):
    """Gop cac lan dong cung coin, cung chieu, cung luc (trong 60s) cua moi acc thanh 1 dong."""
    recs, errs = [], []
    for name, rs in data:
        if isinstance(rs, Exception):
            errs.append(f"{name}: ⚠️ {str(rs)[:60]}")
        else:
            recs += [dict(_rec(x), acc=name) for x in rs]
    recs.sort(key=lambda x: -x["t"])
    groups = []
    for x in recs:
        g = next((g for g in groups if g["symbol"] == x["symbol"] and g["side"] == x["side"]
                  and abs(g["t"] - x["t"]) <= 60000), None)
        if g is None:
            g = {"symbol": x["symbol"], "side": x["side"], "t": x["t"], "size": 0.0, "pnl": 0.0, "fee": 0.0, "accs": set()}
            groups.append(g)
        g["size"] += x["size"]; g["pnl"] += x["pnl"]; g["fee"] += x["fee"]; g["accs"].add(x["acc"])
    groups = groups[:limit]
    title = "🧾 Position History"
    T, R = [title], []
    for g in groups:
        when = datetime.fromtimestamp((g["t"] - time_offset) / 1000).strftime("%d/%m %H:%M")
        name = f"{side_vn(g['side'])} {g['symbol'][:-4] if g['symbol'].endswith('USDT') else g['symbol']}"
        who = f"{len(g['accs'])} acc"
        T.append(f"{name} ({when}, {who}) | size {g['size']:.2f} USDT | {dot(g['pnl'])} {g['pnl']:+.2f} USDT | fee {g['fee']:.2f}")
        R.append([[B(name), f"\n{when} · {who}"], f"{g['size']:.2f}", B(f"{dot(g['pnl'])}\u00a0{g['pnl']:+.2f}")])
    stamp = f"PnL đã gồm phí · USDT · Last Update: {datetime.now().strftime('%H:%M:%S')}"
    blocks = [r_head(title)]
    if R:
        blocks.append(r_table(["Position", "Size", "PnL"], R, [None, "right", "right"]))
    else:
        T.append("Chưa có position nào được đóng trong 30 ngày qua.")
        blocks.append(r_par("Chưa có position nào được đóng trong 30 ngày qua."))
    for e in errs:
        T.append(e)
        blocks.append(r_par(e))
    T.append(stamp)
    blocks.append(r_foot(stamp))
    return "\n".join(T), blocks


async def per_build(kind):
    """kind: d / w / m / h -> (ban chu, blocks, ban phim, png bieu do | None)"""
    if not clients:
        return "Chưa cài sub account nào.", [r_par("Chưa cài sub account nào.")], per_kb(kind), None

    async def one(c, start):
        try:
            return c.name, await fetch_closed(c, start)
        except Exception as e:
            return c.name, e
    if kind == "h":
        now = int(time.time() * 1000) + time_offset
        data = await asyncio.gather(*(one(c, now - WEEK_MS) for c in clients))
        text, blocks = history_view(data)
        if len(blocks[1].get("cells", [])) - 1 < 5:
            data = await asyncio.gather(*(one(c, now - 30 * 86400 * 1000) for c in clients))   # chua du 5 -> nhin xa hon
            text, blocks = history_view(data)
    else:
        start, desc = per_start(kind)
        data = await asyncio.gather(*(one(c, start) for c in clients))
        text, blocks = per_view(kind, data, desc)
    png, note = await asyncio.to_thread(chart_for, kind)
    if blocks and blocks[-1].get("type") == "footer":      # gop chu thich bieu do vao cung 1 dong
        blocks[-1] = r_foot(blocks[-1]["text"] + " · " + note)
    else:
        blocks.append(r_foot(note))
    return text + "\n" + note, blocks, per_kb(kind), png


per_msgs = {}              # message_id cua bang -> {"mode": "inline"} | {"mode": "sep", "photo": message_id anh}
PHOTO_BLOCK = {"type": "photo", "photo": {"type": "photo", "media": "attach://chart"}}


async def bot_form(method, fields, files, _timeout=25):
    """Goi Bot API kem file (multipart)."""
    if not cfg["bot_token"]:
        return {}
    form = aiohttp.FormData()
    for k, v in fields.items():
        form.add_field(k, v if isinstance(v, str) else json.dumps(v, ensure_ascii=False))
    for name, data in files.items():
        form.add_field(name, data, filename=name + ".png", content_type="image/png")
    try:
        async with tg_http.post(f"https://api.telegram.org/bot{cfg['bot_token']}/{method}", data=form,
                                timeout=aiohttp.ClientTimeout(total=_timeout, sock_connect=5)) as r:
            return await r.json()
    except Exception as e:
        return {"ok": False, "description": f"{type(e).__name__}: {str(e)[:100]}".rstrip(": ")}


def _net_err(desc):
    return "Timeout" in desc or "Connect" in desc or "Disconnected" in desc


async def per_send(chat, kind):
    text, blocks, kb, png = await per_build(kind)
    photo_mid = None
    if png:
        rich_on = cfg.get("widgets", True) and botst.get("rich") is not False
        if rich_on and botst.get("rich_photo") is not False:     # cach 1: anh nam ngay trong rich message
            r = await bot_form("sendRichMessage", {"chat_id": str(chat), "reply_markup": kb,
                                                   "rich_message": {"blocks": [blocks[0], PHOTO_BLOCK] + blocks[1:]}},
                               {"chart": png})
            if r.get("ok"):
                botst["rich_photo"] = True
                per_msgs[(r.get("result") or {}).get("message_id")] = {"mode": "inline"}
                return
            desc = str(r.get("description"))
            if not _net_err(desc):
                botst["rich_photo"] = False
                log(f"Telegram không nhận ảnh trong rich message ({desc[:100]}) — gửi biểu đồ thành ảnh riêng phía trên bảng")
        r = await bot_form("sendPhoto", {"chat_id": str(chat)}, {"photo": png})   # cach 2: anh rieng, ngay tren bang
        if r.get("ok"):
            photo_mid = (r.get("result") or {}).get("message_id")
        else:
            log(f"⚠️ Không gửi được biểu đồ: {str(r.get('description'))[:100]}")
    mid, _ = await _send_rich(chat, text, blocks, kb)
    if mid:
        per_msgs[mid] = {"mode": "sep", "photo": photo_mid}
    while len(per_msgs) > 30:
        per_msgs.pop(next(iter(per_msgs)))


async def per_edit(chat, mid, kind):
    text, blocks, kb, png = await per_build(kind)
    info = per_msgs.get(mid) or {}
    if png and info.get("mode") == "inline":
        r = await bot_form("editMessageText", {"chat_id": str(chat), "message_id": str(mid), "reply_markup": kb,
                                               "rich_message": {"blocks": [blocks[0], PHOTO_BLOCK] + blocks[1:]}},
                           {"chart": png})
        if r.get("ok") or "not modified" in str(r.get("description")):
            return
        log(f"/per: không sửa được tin có ảnh ({str(r.get('description'))[:100]}) — sửa bảng không kèm biểu đồ")
    if png and info.get("photo"):
        r = await bot_form("editMessageMedia", {"chat_id": str(chat), "message_id": str(info["photo"]),
                                                "media": {"type": "photo", "media": "attach://chart"}}, {"chart": png})
        if not r.get("ok") and "not modified" not in str(r.get("description")):
            log(f"/per: không cập nhật được ảnh biểu đồ ({str(r.get('description'))[:100]})")
    r = {}
    if cfg.get("widgets", True) and botst.get("rich") is not False:
        r = await bot_api("editMessageText", _quiet=True, chat_id=chat, message_id=mid,
                          rich_message={"blocks": blocks}, reply_markup=kb)
    if not r.get("ok") and "not modified" not in str(r.get("description")):
        r = await bot_api("editMessageText", _quiet=True, chat_id=chat, message_id=mid, text=text[:4000], reply_markup=kb)
        if not r.get("ok") and "not modified" not in str(r.get("description")):
            log(f"⚠️ /per: không sửa được tin ({str(r.get('description'))[:100]})")


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
            p = {"timeout": 25, "allowed_updates": ["message", "channel_post", "callback_query"]}
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
                note = cfg.get("update_note")
                if note and cfg["bot_owner_id"]:
                    m_old = re.search(r"(\d+(?:\.\d+)+) →", note)
                    if note.startswith("⬆️") and m_old:
                        send_rich(cfg["bot_owner_id"],
                                  *changelog_msg(f"⬆️ Đã cập nhật v{m_old.group(1)} → v{VERSION}",
                                                 changelog_since(m_old.group(1))))
                    else:
                        send(cfg["bot_owner_id"], note)
                    cfg["update_note"] = ""
                    save_cfg()
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
            if u.get("callback_query"):
                await handle_callback(u["callback_query"])
                return
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
                    log(f"⚙️ Đòn bẩy: {lev_label()} (từ Telegram)")
                    reply = (f"⚙️ Đã đặt đòn bẩy: {lev_label()} cho tất cả sub account.\n"
                             "Áp dụng cho /buy, /sell và lệnh từ kênh (/buyall, /sellall luôn dùng max của coin). Coin nào max thấp hơn thì tool tự hạ xuống max của coin đó; "
                             "size cần đòn bẩy cao hơn thì tool tự nâng lên.")
                else:
                    reply = f"Đòn bẩy hiện tại: {lev_label()}\nDùng: /lev 10 (từ 1 đến 200) hoặc /lev max"
            elif cmd in ("/buyall", "/sellall"):
                a = parse_allin(m.get("text") or "")
                if not a and cmd == "/buyall":
                    reply = ("Sai cú pháp. Dùng: /buyall #coin tp sl\n"
                             "Ví dụ: /buyall #evaa 10 2 → Long EVAAUSDT toàn bộ vốn ở đòn bẩy max, TP +10%, SL -2%")
                elif not a:
                    reply = ("Sai cú pháp. Dùng: /sellall #coin tp sl\n"
                             "Ví dụ: /sellall #evaa 10 2 → Short EVAAUSDT toàn bộ vốn ở đòn bẩy max, "
                             "TP khi giá giảm 10%, SL khi giá tăng 2%")
                else:
                    log(f"🛒 {cmd} {a['coin']} {a['tp']:g} {a['sl']:g} (từ Telegram)")
                    await execute_order(a["coin"], 0, a["tp"], a["sl"], cmd, allin=("max",),
                                        side="Buy" if cmd == "/buyall" else "Sell")
                    return
            elif cmd == "/per":
                asyncio.create_task(per_send(chat, "d"))
                return
            elif cmd == "/update":
                log("⬆️ /update (từ Telegram)")
                ok, msg, rs = await do_update("lệnh /update")
                if ok and not rs:      # dang la ban moi nhat -> gui change log cua ban hien tai
                    send_rich(chat, *changelog_msg(f"✅ Đang là bản mới nhất — v{VERSION}", changelog_since()))
                    return
                reply = ("⬆️ " if ok else "⚠️ ") + msg + ("\nBot sẽ gửi change log sau vài giây." if rs else "")
            elif cmd in ("/buy", "/sell"):
                b = parse_buy(m.get("text") or "")
                if not b and cmd == "/buy":
                    reply = ("Sai cú pháp. Dùng: /buy #coin size tp sl\n"
                             "Ví dụ: /buy #eth 1000 10 2 → Long ETHUSDT 1000 USDT, TP +10%, SL -2%")
                elif not b:
                    reply = ("Sai cú pháp. Dùng: /sell #coin size tp sl\n"
                             "Ví dụ: /sell #eth 1000 10 2 → Short ETHUSDT 1000 USDT, TP khi giá giảm 10%, SL khi giá tăng 2%")
                else:
                    log(f"🛒 {cmd} {b['coin']} {b['size']:g} {b['tp']:g} {b['sl']:g} (từ Telegram)")
                    await execute_order(b["coin"], b["size"], b["tp"], b["sl"], cmd,
                                        side="Buy" if cmd == "/buy" else "Sell")
                    return   # ket qua da duoc gui qua notify()
            else:
                send_rich(chat, HELP_TEXT, help_blocks())
                return
            send(chat, reply)


# ----------------------------------------------------------------------------
# Web UI
# ----------------------------------------------------------------------------
def public_cfg():
    c = {k: v for k, v in cfg.items() if k not in ("accounts", "bot_token", "live_msg", "update_note", "realized")}
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


busy = {"n": 0}            # so lenh dang vao/dong -> khong khoi dong lai giua chung
PENDING = os.path.join(BASE_DIR, "update_pending")   # danh dau "vua update, chua chay on dinh"


def _api_url(url):
    """Link raw.githubusercontent.com bi cache ~5 phut -> doi sang GitHub API (luon moi nhat)."""
    m = re.match(r"https://raw\.githubusercontent\.com/([^/]+)/([^/]+)/([^/]+)/(.+)$", url)
    return f"https://api.github.com/repos/{m.group(1)}/{m.group(2)}/contents/{m.group(4)}?ref={m.group(3)}" if m else None


async def fetch_latest():
    """-> (code, None) hoac (None, ly do loi)"""
    url = cfg["update_url"].strip()
    if not url:
        return None, "Chưa nhập link update (GitHub raw) trong Cài đặt"
    api = _api_url(url)
    tries = ([(api, {"Accept": "application/vnd.github.raw"})] if api else []) + \
            [(f"{url}{'&' if '?' in url else '?'}t={int(time.time())}", {})]
    err = ""
    for u, h in tries:
        try:
            async with http.get(u, headers=h) as r:
                if r.status == 200:
                    return await r.text(), None
                err = f"Tải file lỗi HTTP {r.status}"
        except Exception as e:
            err = f"{type(e).__name__}: {str(e)[:80]}"
    return None, err


def _selftest_file(path):
    import subprocess
    try:
        r = subprocess.run([sys.executable, path, "--selftest"], capture_output=True, timeout=60)
        out = (r.stdout + r.stderr).decode("utf-8", "replace").strip().splitlines()
        return r.returncode == 0, (out[-1] if out else f"exit {r.returncode}")
    except Exception as e:
        return False, str(e)


async def do_update(source="tool"):
    """Tai ban moi, kiem tra, thay file va khoi dong lai. -> (ok, msg, restart)"""
    code, err = await fetch_latest()
    if code is None:
        return False, err, False
    m = re.search(r'^VERSION\s*=\s*"([^"]+)"', code, re.M)
    if not m:
        return False, "File tải về không phải tool này (thiếu VERSION)", False
    new = m.group(1)
    if new == VERSION:
        return True, f"Đang là bản mới nhất ({VERSION})", False
    try:
        compile(code, "bybit_copy.py", "exec")
    except SyntaxError as e:
        return False, f"Bản {new} bị lỗi code, giữ bản {VERSION}: {e}", False
    me = os.path.abspath(__file__)
    tmp = os.path.join(BASE_DIR, "bybit_copy_new.py")
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        f.write(code)
    ok, why = await asyncio.to_thread(_selftest_file, tmp)   # chay thu ban moi truoc khi thay
    if not ok:
        try:
            os.remove(tmp)
        except Exception:
            pass
        return False, f"Bản {new} không qua được bước tự kiểm tra, giữ bản {VERSION}: {why[:150]}", False
    for _ in range(60):                # doi lenh dang vao/dong xong
        if not busy["n"]:
            break
        await asyncio.sleep(0.5)
    with open(me, "r", encoding="utf-8") as f:
        old = f.read()
    with open(me + ".bak", "w", encoding="utf-8", newline="\n") as f:
        f.write(old)
    os.replace(tmp, me)
    with open(PENDING, "w") as f:
        f.write(VERSION)
    cfg["update_note"] = f"⬆️ Đã cập nhật {VERSION} → {new} ({source})"
    save_cfg()
    log(f"⬆️ Update {VERSION} -> {new} ({source}), đang khởi động lại...")
    asyncio.get_event_loop().call_later(1.0, restart)
    return True, f"Đã update lên {new} — tool tự khởi động lại", True


async def h_update(req):
    ok, msg, rs = await do_update("bấm nút trên tool")
    return web.json_response({"ok": ok, "msg": msg, "restart": rs})


async def clear_pending_later():
    await asyncio.sleep(45)
    if os.path.exists(PENDING):        # ban moi da chay on dinh 45s -> xoa dau "cho kiem chung"
        try:
            os.remove(PENDING)
        except Exception:
            pass


def selftest():
    """Chay boi ban cu truoc khi thay file: ban moi phai tu chay duoc cac ham chinh."""
    assert parse_command("m #space 1 10 2") == {"coin": "SPACE", "size": 1, "tp": 10, "sl": 2}
    assert parse_buy("/sell #eth 500 5 1")["size"] == 500
    assert parse_buy("/buy #eth 1000 10 2")["size"] == 1000 and parse_allin("/buyall #x 1 2")["coin"] == "X"
    assert parse_allin("/sellall #x 1 2")["sl"] == 2 and parse_allin("/allin #x 1 2") is None
    assert num(2003.126) == "2003.13" and num("0.00432156") == "0.004322"
    assert calc_leverage(1000, 100, 50)[0] == 11 and allin_plan(100, 10, 4.0)[0] == 4
    global clients
    clients = [Bybit("Acc1", "k", "s", "x")]
    _cd = [(1700000000 + 60 * i, 100 + i % 7, 101.5 + i % 7, 99.2 + i % 5, 100.4 + (i * 3) % 7) for i in range(60)]
    assert chart_target() is None
    assert chart_png({"symbol": "ETHUSDT", "side": "Buy", "entry": 101.0, "tp": 104.0, "sl": 90.0}, _cd)[:4] == b"\x89PNG"
    status["Acc1"] = {"balance": 1.0, "error": "", "t": 0, "positions": [
        {"symbol": "ETHUSDT", "side": "Buy", "size": "0.01", "avg": 1.0, "pnl": -0.1, "pct": -1.0,
         "lev": "1", "idx": 0, "fee": 0.01}]}
    json.dumps([status_blocks(stamp="x"), help_blocks(), changelog_msg("x", changelog_since("1.0.0")), live_kb()])
    fake = [{"symbol": "ETHUSDT", "side": "Sell", "closedSize": "0.01", "cumEntryValue": "18.2", "closedPnl": "-0.01", "openFee": "0.01",
             "closeFee": "0.01", "updatedTime": str(int(time.time() * 1000))}]
    json.dumps([per_view("d", [("Acc1", fake), ("Acc2", RuntimeError("x"))], "x"), history_view([("Acc1", fake)]),
                per_kb("w"), per_start("w"), per_start("m")])
    t_now = time.time()
    png = render_chart([(t_now - 3600 * (24 - i), 100 + i * 0.01) for i in range(24)],
                       [(t_now - 3600 * 24 + 14400 * i, "08:00") for i in range(7)])
    assert png[:8] == b"\x89PNG\r\n\x1a\n" and len(png) > 500
    bal_hist[:] = [(t_now - 600, 100.0), (t_now - 300, 100.2)]
    for k in "dwmh":
        assert chart_for(k)[1]
    bal_hist.clear()
    cfg["realized"] = {"pnl": -0.5, "fee": 0.1, "n": 1}
    assert len(realized_lines()) == 3 and "Realized PnL" in status_text() and live_kb()
    cfg["realized"] = {"pnl": 0.0, "fee": 0.0, "n": 0}
    assert CHANGELOG[0][0] == VERSION, "CHANGELOG thieu ban hien tai"
    assert status_text() and HELP_TEXT and "__VERSION__" in HTML and chan_norm() is not None
    print("selftest ok", VERSION)


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
    load_balance_log()
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
    asyncio.create_task(clear_pending_later())
    asyncio.create_task(live_loop())
    asyncio.create_task(chart_loop())
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
    <label>Đòn bẩy cho mọi lệnh (số, hoặc max = max của coin; trống = tự tính thấp nhất)</label><input id="allin_lev" placeholder="chưa đặt">
    <div class="mut" style="font-size:12px;margin-top:6px">Lệnh: /buyall #coin tp sl · /sellall #coin tp sl · /lev N · /start · /stop · /status · /buy #coin size tp sl · /close · /help</div>
  </div>

  <div class="card"><h2>Update</h2>
    <label>Link GitHub raw của file bybit_copy.py</label><input id="update_url" placeholder="https://raw.githubusercontent.com/&lt;user&gt;/&lt;repo&gt;/main/bybit_copy.py">
    <div class="mut" style="font-size:12px;margin-top:6px">Tool chỉ cập nhật khi bạn gõ /update cho bot hoặc bấm nút Update New Ver.</div>
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
    if "--selftest" in sys.argv:
        selftest()
        sys.exit(0)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        # Ban vua update bi loi luc khoi dong -> tu quay ve ban cu roi chay lai
        import traceback
        traceback.print_exc()
        me = os.path.abspath(__file__)
        if os.path.exists(PENDING) and os.path.exists(me + ".bak"):
            try:
                with open(me + ".bak", "r", encoding="utf-8") as f:
                    old = f.read()
                with open(me, "w", encoding="utf-8", newline="\n") as f:
                    f.write(old)
                os.remove(PENDING)
                load_cfg()
                cfg["update_note"] = f"⚠️ Bản {VERSION} lỗi khi khởi động ({type(e).__name__}: {str(e)[:80]}) — đã tự quay về bản cũ"
                save_cfg()
                print("Da quay ve ban cu, dang chay lai...")
                restart()
            except Exception:
                traceback.print_exc()
        raise
