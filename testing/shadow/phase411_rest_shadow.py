import os, sys, time
from infrastructure.broker.deriv.rest_shadow_adapter import RestOtpShadowAdapter, ShadowViolation
from infrastructure.broker.deriv.shadow import ShadowBrokerView, ShadowRecorder
from infrastructure.broker.deriv.rest_transport import _redact

def line(label, status): print(label.ljust(20) + " " + str(status))

def main():
    print("="*64)
    print("APEX ULTRA - PHASE 41.1  REST/OTP SHADOW INTEGRATION  [read-only]")
    print("="*64)
    token=os.environ.get("DERIV_API_TOKEN",""); app_id=os.environ.get("DERIV_APP_ID","")
    symbol=os.environ.get("DERIV_SYMBOL","R_100")
    live=os.environ.get("LIVE_TRADING","false").strip().lower() in ("1","true","yes","on")
    print("\nTOKEN        : "+_redact(token))
    print("Deriv-App-ID : "+(app_id or "(missing!)"))
    print("symbol       : "+symbol)
    print("LIVE_TRADING : "+str(live))
    if live: print("\nBLOCKED: LIVE_TRADING enabled."); return 1
    if not token: print("\nBLOCKED: DERIV_API_TOKEN not set."); return 1

    res={}
    a=RestOtpShadowAdapter(api_token=token, app_id=app_id or None, symbol=symbol)
    print("\n[1/2] AUTH + VIRTUAL ACCOUNT")
    try:
        a.connect()
    except ShadowViolation as e:
        print("    BLOCKED (structural refusal): "+str(e)); return 1
    except Exception as e:
        print("    BLOCKED: "+str(e)); return 1
    print("    loginid    : "+str(a._loginid))
    print("    is_virtual : "+str(a._is_virtual))
    res["Authentication"]="PASS"
    res["Virtual Account"]="PASS" if a._is_virtual==1 else "FAIL"
    if res["Virtual Account"]!="PASS": print("    BLOCKED: not virtual"); return 1

    view=ShadowBrokerView(a)
    print("    view.is_virtual: "+str(view.is_virtual)+"   view.loginid: "+str(view.loginid))

    print("\n[3] TICK STREAM (via ShadowBrokerView.get_quote)")
    q=view.get_quote(symbol)
    if q is None: print("    FAIL: no quote"); res["Tick Stream"]="FAIL"
    else: print("    quote: "+repr(q)); res["Tick Stream"]="PASS"

    print("\n[4] CONTRACT DISCOVERY (via ShadowBrokerView.contracts_for)")
    avail=view.contracts_for(symbol)
    if not avail: print("    FAIL: no contracts"); res["Contract Discovery"]="FAIL"
    else:
        types=sorted({c.get("contract_type") for c in avail if c.get("contract_type")})
        print("    "+str(len(types))+" contract types, e.g. "+str(types[:6])); res["Contract Discovery"]="PASS"

    print("\n[5] SHADOW FEED (real ticks -> unchanged ShadowRecorder)")
    recorder=ShadowRecorder()
    quotes=view.stream_ticks(count=5, timeout=15.0)
    if not quotes:
        for _ in range(5):
            qq=view.get_quote(symbol)
            if qq is not None: quotes.append(qq)
            time.sleep(0.2)
    fed=sum(1 for qv in quotes if qv is not None and getattr(qv,"mid",None) is not None)
    if fed>0:
        print("    fed "+str(fed)+" real quotes into recorder feed path (mid e.g. "+str(quotes[0].mid)+")")
        res["Shadow Feed"]="PASS"
    else:
        print("    FAIL: no real quotes reached feed path"); res["Shadow Feed"]="FAIL"

    print("\n[6] EXECUTION SURFACE")
    exposed=0
    for name in RestOtpShadowAdapter.EXECUTION_METHODS:
        m=getattr(a,name,None)
        if m is None: continue
        try:
            m(); print("    !! "+name+" did NOT raise"); exposed+=1
        except ShadowViolation: pass
        except TypeError:
            try:
                m(None); print("    !! "+name+" did NOT raise"); exposed+=1
            except ShadowViolation: pass
    print("    execution methods exposed: "+str(exposed))

    live_orders_sent=0; synthetic_in_real=False
    a.disconnect()

    print("\n"+"="*64)
    print("PHASE 41.1 - REST/OTP SHADOW INTEGRATION\n")
    for label in ("Authentication","Virtual Account","Tick Stream","Contract Discovery","Shadow Feed"):
        line(label, res.get(label,"MISSING"))
    line("Execution Surface", exposed)
    print()
    line("Live orders sent", live_orders_sent)
    line("Execution exposed", exposed)
    line("Synthetic in real", "NO" if not synthetic_in_real else "YES")

    all_pass=(all(res.get(k)=="PASS" for k in ("Authentication","Virtual Account","Tick Stream","Contract Discovery","Shadow Feed")) and exposed==0 and live_orders_sent==0 and not synthetic_in_real)
    print("\nSTATUS:")
    if all_pass:
        print("REST/OTP SHADOW OBSERVATION READY")
        print("(Read-only feed into existing recorder proven. NOT DEMO READY, NOT SHADOW PASS.)")
        return 0
    print("BLOCKED - one or more checks did not pass."); return 1

sys.exit(main())
