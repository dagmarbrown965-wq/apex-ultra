from __future__ import annotations
from typing import Optional
from .rest_transport import DerivRestOtpTransport, ExecutionForbiddenError, DerivTransportError

class ShadowViolation(Exception):
    pass

class _Quote:
    __slots__ = ("symbol","bid","ask","mid","quote","epoch")
    def __init__(self, symbol, bid, ask, quote, epoch):
        self.symbol=symbol; self.bid=bid; self.ask=ask; self.quote=quote
        if isinstance(bid,(int,float)) and isinstance(ask,(int,float)): self.mid=(bid+ask)/2.0
        else: self.mid=quote
        self.epoch=epoch
    def __repr__(self):
        return "Quote(symbol="+repr(self.symbol)+", bid="+str(self.bid)+", ask="+str(self.ask)+", mid="+str(self.mid)+", epoch="+str(self.epoch)+")"

class RestOtpShadowAdapter:
    EXECUTION_METHODS = ("buy","sell","proposal","place_order","send_order","sell_contract","buy_contract")
    def __init__(self, api_token, *, app_id=None, symbol="R_100"):
        self._t = DerivRestOtpTransport(api_token=api_token, app_id=app_id)
        self.symbol=symbol; self.current_mid=None
        self._is_virtual=None; self._loginid=None; self._connected=False
        self.safety={"mode":"REAL_SHADOW","execution":"BLOCKED","live_orders_sent":0,"transport":"rest_otp_readonly"}
    def connect(self):
        self._t.connect()
        auth = self._t.call({"authorize": self._t.api_token}, timeout=20.0)
        if "error" in auth:
            e=auth["error"]; raise DerivTransportError("REST authorize failed: "+str(e.get("code"))+": "+str(e.get("message")))
        a=auth["authorize"]; self._is_virtual=a.get("is_virtual"); self._loginid=a.get("loginid")
        if self._is_virtual != 1:
            raise ShadowViolation("account "+str(self._loginid)+" is not virtual/demo; refusing")
        self._connected=True; return True
    def disconnect(self):
        self._connected=False
        try: self._t.close()
        except Exception: pass
    def is_connected(self): return self._connected and self._t.is_open()
    def heartbeat(self):
        r=self._t.call({"ping":1}); return bool(r.get("ping")=="pong")
    def getBalance(self):
        b=self._t.get_balance()
        if "error" in b: return None
        return b.get("balance",{}).get("balance")
    def get_quote(self, symbol=None):
        sym=symbol or self.symbol
        res=self._t.get_tick(sym)
        if "error" in res or not res.get("tick"): return None
        t=res["tick"]; q=_Quote(sym,t.get("bid"),t.get("ask"),t.get("quote"),t.get("epoch"))
        self.current_mid=q.mid; return q
    def stream_ticks(self, count=5, timeout=10.0):
        res=self._t.subscribe_ticks(self.symbol, count=count)
        if "error" in res: return []
        out=[]
        for t in res.get("ticks",[]):
            out.append(_Quote(t.get("symbol") or self.symbol,t.get("bid"),t.get("ask"),t.get("quote"),t.get("epoch")))
        if out: self.current_mid=out[-1].mid
        return out
    def contracts_for(self, symbol=None):
        sym=symbol or self.symbol
        res=self._t.get_contract_availability(sym)
        if "error" in res: return None
        return res.get("available")
    def force_drop(self):
        self._connected=False
        try: self._t.close()
        except Exception: pass
    def _violation(self, name):
        raise ShadowViolation(name+"() blocked: REST/OTP SHADOW adapter is READ-ONLY (Phase 41.1)")
    def buy(self,*a,**k): self._violation("buy")
    def sell(self,*a,**k): self._violation("sell")
    def proposal(self,*a,**k): self._violation("proposal")
    def place_order(self,*a,**k): self._violation("place_order")
    def send_order(self,*a,**k): self._violation("send_order")
    def sell_contract(self,*a,**k): self._violation("sell_contract")
    def buy_contract(self,*a,**k): self._violation("buy_contract")
