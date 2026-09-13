"""Merge the six researcher passes into the fixture library.

Researchers gathered and cited; they did not adjudicate. Conflicts came back
flagged and are preserved as flagged — this script does not resolve them either.
Where a researcher found no manufacturer figure, the field goes to `missing`
rather than keeping the old unsourced number as though it were fine.

Units: `value` stays in the library's working unit (VA/W for power, lb for
weight) so the existing tools keep working. `sourceValue`/`sourceUnit` record
what the document actually said, verbatim.
"""
import json, pathlib

HERE = pathlib.Path(__file__).parent
SEED = HERE / "seed"
OUT  = HERE / "verified"; OUT.mkdir(exist_ok=True)
D    = "2026-09-10"

def P(v, unit, label, url, status, note="", atV=None, srcV=None, srcU=None):
    r = {"value": v, "unit": unit, "sourceLabel": label, "sourceUrl": url,
         "retrieved": D, "status": status}
    if note: r["note"] = note
    if atV is not None: r["atVoltage"] = atV
    if srcV is not None: r["sourceValue"] = srcV; r["sourceUnit"] = srcU
    return r

def IN(conn, vr, label, url, status, note=""):
    r = {"connector": conn, "voltageRange": vr, "sourceLabel": label,
         "sourceUrl": url, "retrieved": D, "status": status}
    if note: r["note"] = note
    return r

def OUTP(present, conn, maxLinked, label, url, status, note=""):
    r = {"present": present, "connector": conn, "maxLinked": maxLinked,
         "sourceLabel": label, "sourceUrl": url, "retrieved": D, "status": status}
    if note: r["note"] = note
    return r

M = "https://adn.harmanpro.com/"
R = {}

# ── Martin ────────────────────────────────────────────────────────────────
R["martin-mac-ultra-performance"] = dict(
  power=P(1450,"W","Maximum total power consumption",M+"site_elements/resources/21843_1615993167/Martin_MACUltraPerformance_SpecSheet_original.pdf","verified",
          "Typical by voltage: 1380 W at 208/230/240 V. Idle 100 W."),
  powerIn=IN("powerCON TRUE1 TOP (Neutrik NAC3FX-W)","200-240 V, 50/60 Hz","AC power",M+"site_elements/resources/21843_1615993167/Martin_MACUltraPerformance_SpecSheet_original.pdf","verified"),
  powerOut=OUTP(False,None,None,"Connections lists only AC power input; no output entry",
          "https://www.christielites.com/file_uploads/SFTY_MACUltraPerformance_EN_B.pdf","verified",
          "NO PASS-THRU. Manual: 'Connect directly to AC mains power.' Needs its own home run or a two-fer."))

R["martin-mac-viper-profile"] = dict(
  power=P(1225,"W",'Typical power and current (120 V row: "1225 W, 10.3 A")',
          "https://www.fullcompass.com/common/files/17102-MACViperSpecificationSheet.pdf","verified",
          "1190 W at 208 V, 1186 W at 230 V. Library's 1225 matches the 120 V figure.",atV=120),
  powerIn=IN("powerCON (Neutrik, variant not named by Martin)","120-240 V, 50/60 Hz","AC power input",
          "https://www.fullcompass.com/common/files/17102-MACViperSpecificationSheet.pdf","verified"),
  powerOut=OUTP(False,None,None,"No power output entry found in spec sheet",
          "https://www.fullcompass.com/common/files/17102-MACViperSpecificationSheet.pdf","interpreted",
          "Likely no pass-thru but the full user guide could not be read end to end. Confirm before ordering."))

R["martin-mac-encore-performance"] = dict(
  power=P(596,"W",'Typical power and current (120 V row: "5.0 A, 596 W")',
          "https://www.fullcompass.com/common/files/30786-MartinMACEncorePerformanceCLDSpecSheet.pdf","verified",
          "581 W at 208 V, 580 W at 230 V. Idle 64 W. Library had 600 — close, now sourced.",atV=120),
  powerIn=IN("powerCON TRUE1 (Neutrik NAC3FX-W)","120-240 V, 50/60 Hz","AC power input",
          "https://www.fullcompass.com/common/files/86983-MACEncorePerformanceSafetyandInstallationManual.pdf","verified"),
  powerOut=OUTP(False,None,None,'No AC power output entry; "Connect directly to AC power."',
          "https://www.fullcompass.com/common/files/86983-MACEncorePerformanceSafetyandInstallationManual.pdf","verified",
          "NO PASS-THRU, confirmed in two Martin documents."))

R["martin-mac-aura-pxl"] = dict(
  power=P(500,"W","Typical power data, full intensity at 6500 K",
          "https://www.avc-group.com/assets/products/Martin/pdfs/martin-ds-mac_aura_pxl.pdf","verified",
          "Flat ~500 W across 100-240 V. Idle 77 W."),
  powerIn=IN("powerCON TRUE1","100-240 V, 50/60 Hz","AC power",
          "https://www.avc-group.com/assets/products/Martin/pdfs/martin-ds-mac_aura_pxl.pdf","verified"),
  powerOut=OUTP(True,"powerCON TRUE1",None,"AC power throughput",
          "https://www.avc-group.com/assets/products/Martin/pdfs/martin-ds-mac_aura_pxl.pdf","verified",
          "HAS PASS-THRU. Martin does not publish a fixtures-per-circuit figure for this model — "
          "five manual mirrors checked. Do not confuse with the DMX limit of 32 devices per link."))

R["martin-mac-aura-xb"] = dict(
  power=P(400,"W","Maximum power consumption",M+"site_elements/executables/6742_1526699551/35000280b_UM_MACAuraXB_EN_B_original.pdf","verified",
          "Typical 349-359 W by voltage."),
  powerIn=IN("powerCON TRUE1 (Neutrik NAC3FX-W)","100-240 V, 50/60 Hz","AC power input",M+"site_elements/executables/6742_1526699551/35000280b_UM_MACAuraXB_EN_B_original.pdf","verified"),
  powerOut=OUTP(True,"powerCON TRUE1 (Neutrik NAC3MX-W)",[[120,3],[240,8]],
          '"you can link: Maximum three (3) MAC Aura XB fixtures in total at 100-120 V, or Maximum eight (8) at 200-240 V."',
          M+"site_elements/executables/6742_1526699551/35000280b_UM_MACAuraXB_EN_B_original.pdf","verified",
          "HAS PASS-THRU. Martin states voltage BANDS, not per-voltage points: 3 across 100-120 V, 8 across 200-240 V."))

R["martin-jem-zr45-fogger"] = dict(
  power=P(1800,"W",'Power Consumption (US model: "1800 W, 15 A")',
          "https://www.christielites.com/file_uploads/UM_JEMZR25-35-45_EN_E_original.pdf","verified",
          "US and EU are DIFFERENT HARDWARE, not one rating restated: US 1800 W at 100-130 V; "
          "EU 2100 W at 220-240 V. Library's 1800 is the US unit.",atV=120),
  powerIn=IN("powerCON TRUE1","US: 100-130 V; EU: 220-240 V, 50/60 Hz","AC Power",
          "https://www.christielites.com/file_uploads/UM_JEMZR25-35-45_EN_E_original.pdf","verified"),
  powerOut=OUTP(False,None,None,'"The machines are interconnected with DMX cabling"',
          "https://www.christielites.com/file_uploads/UM_JEMZR25-35-45_EN_E_original.pdf","verified",
          "NO PASS-THRU. Units link for master/slave CONTROL over DMX; each needs its own mains feed."))

# ── Robe — every one of the five has NO power pass-thru ───────────────────
RB = "https://www.robe.cz/res/downloads/user_manuals/"
R["robe-bmfl-blade"] = dict(
  power=P(2000,"W","Power consumption: 2000 W at 230 V / 50 Hz","https://cdn.aws.robe.cz/print/en_product_1063.pdf","verified",
          "1820 W in the 1500 W lamp mode. Lamp is 1700 W — NOT the draw.",atV=230),
  powerIn=IN("powerCON A-type, blue (Neutrik NAC3MPA)","200-240 V, 50-60 Hz","AC power IN: Chassis connector Neutrik PowerCon, A-type, NAC3MPA",RB+"User_manual_Robin_BMFL_Blade.pdf","verified",
          "Blue A-type, NOT TRUE1 — different cable."),
  powerOut=OUTP(False,None,None,"Connection list names only a power IN connector",RB+"User_manual_Robin_BMFL_Blade.pdf","verified",
          "NO PASS-THRU."))
R["robe-megapointe"] = dict(
  power=P(670,"W","Max. power consumption: 670 W (power factor 0.97)",RB+"User_manual_Robin_MegaPointe.pdf","verified",
          "Lamp is 470 W Osram Sirius HRI — NOT the draw. Library value confirmed."),
  powerIn=IN("powerCON TRUE1 (Neutrik NAC3MPX)","100-240 V, 50-60 Hz","Power in connector: Neutrik powerCON TRUE1","https://cdn.aws.robe.cz/print/en_product_635.pdf","verified"),
  powerOut=OUTP(False,None,None,"Connection list names only Power IN",RB+"User_manual_Robin_MegaPointe.pdf","verified","NO PASS-THRU."))
R["robe-pointe"] = dict(
  power=P(470,"W","Max. power consumption: 470 W at 230V",RB+"User_manual_Robin_Pointe.pdf","verified",
          "Typical 390 W. Lamp is 280 W — NOT the draw. Library value confirmed.",atV=230),
  powerIn=IN("powerCON A-type, blue (Neutrik NAC3MPA)","100-240 V, 50/60 Hz","Power In: Chassis connector Neutrik PowerCon, A-type, NAC3MPA",RB+"User_manual_Robin_Pointe.pdf","verified",
          "Blue A-type has no through-wiring by design."),
  powerOut=OUTP(False,None,None,"Connection list names only Power In",RB+"User_manual_Robin_Pointe.pdf","verified","NO PASS-THRU."))
R["robe-spiider"] = dict(
  power=P(660,"W","Max. power consumption ... 660W (power factor 0.99)",RB+"User_manual_Robin_Spiider.pdf","verified",
          "Library value confirmed."),
  powerIn=IN("powerCON TRUE1 (Neutrik NAC3MPX)","100-240 V, 50-60 Hz","AC power IN: Neutrik TrueOne NAC3MPX",RB+"User_manual_Robin_Spiider.pdf","verified"),
  powerOut=OUTP(False,None,None,"Connection list names only AC power IN",RB+"User_manual_Robin_Spiider.pdf","verified",
          "NO PASS-THRU. Its published 'max 8 fixtures per Ethernet line' is a DATA limit, not power."))
R["robe-t1-profile"] = dict(
  power=P(750,"W","Power consumption: maximum 750 W at 230 V / 50 Hz (all LEDs On)","https://cdn.aws.robe.cz/print/en_product_654.pdf","verified",
          "LIBRARY WAS WRONG: it carried 650. The MSL LED engine is 550 W — the classic engine-vs-draw trap — "
          "and the fixture draws 750 W. 650 matches neither figure.",atV=230),
  powerIn=IN("powerCON TRUE1 (Neutrik NAC3MPX)","100-240 V, 50-60 Hz","AC power input: Chassis connector Neutrik PowerCon TRUE 1, NAC3MPX",RB+"User_manual_Robin_T1_Profile.pdf","verified"),
  powerOut=OUTP(False,None,None,"Connection list names only AC power input",RB+"User_manual_Robin_T1_Profile.pdf","verified",
          "NO PASS-THRU. The EP variant's 'max 8 per Ethernet line' is a DATA limit, not power."))

# ── Claypaky + Ayrton ─────────────────────────────────────────────────────
R["claypaky-mythos-2"] = dict(
  power=P(700,"VA","Max Power consumption","https://www.claypaky.it/products/mythos2/","verified",
          "Library value confirmed. Lamp is 440 W per the current product page (the 470 W figure "
          "circulating elsewhere may be a lamp revision) — either way, lamp is not draw."),
  powerIn=IN("powerCON TRUE1","100-240 V, 50/60 Hz","Operating Voltage / Power connector: PowerCon True1","https://www.claypaky.it/products/mythos2/","verified"),
  powerOut=OUTP(None,None,None,None,None,"missing",
          "UNKNOWN. Claypaky's electrical detail sits behind the login-gated e-assist.tech portal; "
          "the 2015 manual PDF and datasheet URLs both 404. Not inferring a pass-thru from the connector type."))
R["claypaky-scenius-unico"] = dict(
  power=P(None,None,"Light can be run at 1400W or 1200W","https://www.claypaky.it/wp-content/uploads/2023/04/Claypaky_SceniusUnico.pdf","missing",
          "LIBRARY FIGURE UNSUPPORTED: it carried 1800 VA. No manufacturer figure for total fixture draw "
          "could be found in any accessible source. The only published wattage is the dual-mode LAMP "
          "(1400/1200 W) — exactly the trap. Model is discontinued and the product page 404s. "
          "1800 is not being kept as though it were sourced.",srcV=1800,srcU="VA (previous unsourced library value)"),
  powerIn=IN("powerCON TRUE1 (IP65)","200-240 V, 50/60 Hz","Power Input Connector","https://www.showtech.com.au/product/scenius-unico/","interpreted",
          "Distributor page, not a Claypaky spec table."),
  powerOut=OUTP(None,None,None,None,None,"missing","UNKNOWN. No source found."))
R["claypaky-sharpy"] = dict(
  power=P(350,"VA","Power consumption: 350VA at 230V, 50 Hz","https://www.claypaky.it/wp-content/uploads/2022/10/Claypaky_sharpy_leaflet.pdf","conflicting",
          "LIBRARY WAS WRONG: it carried 440. Claypaky's own leaflet says 350 VA at 230 V. An independent "
          "bench test measured 301 W stationary / 320 W peak at 115 V. Lamp is ~189 W. 440 matches nothing.",atV=230),
  powerIn=IN("powerCON (variant not named by Claypaky)","115-230 V, 50/60 Hz","Power supply: 115-230 V; 50/60 Hz","https://www.claypaky.it/wp-content/uploads/2022/10/Claypaky_sharpy_leaflet.pdf","interpreted",
          "Leaflet gives the voltage range but never names the connector. Field-check before ordering."),
  powerOut=OUTP(None,None,None,None,None,"missing",
          "UNKNOWN. No source mentions an output. Plausibly none on a 2011 fixture, but unconfirmed."))
AY = "https://www.ayrton.eu/wp-content/uploads/2020/03/"
R["ayrton-diablo-s"] = dict(
  power=P(550,"W","Max Power Consumption",AY+"DiabloS-Specification-Sheet.pdf","verified",
          "Typical 490.8 W at 230 V. The '300 W' in the marketing copy is the LED source class, not draw. Library confirmed."),
  powerIn=IN("powerCON TRUE1 TOP","100-240 V, 50-60 Hz","Voltage Range 100-240 V 50-60 Hz / Connector PowerCon True1 TOP",AY+"DiabloS-Specification-Sheet-V7.pdf","verified"),
  powerOut=OUTP(True,"powerCON TRUE1 (In/Thru)",[[110,4],[230,6]],"Total Fixtures per Circuit 6 @ 220/230 V / 4 @ 110 V",AY+"DiabloS-Specification-Sheet.pdf","verified",
          "HAS PASS-THRU, and Ayrton publishes the per-circuit count outright — the cleanest record in this pass."))
R["ayrton-khamsin-s"] = dict(
  power=P(1150,"W","Power: 1,150 W maximum","https://www.ayrton.eu/produit/khamsin/","verified","Library confirmed."),
  powerIn=IN("powerCON TRUE1","120-240 V, 50/60 Hz","powerCON TRUE1 connector","https://shop.bmisupply.com/Resources/en/ItemDocuments/39A1010/BMI.Ayrton.Khamsin.Datasheet.pdf","verified"),
  powerOut=OUTP(False,None,None,"No power output listed across two sources","https://shop.bmisupply.com/Resources/en/ItemDocuments/39A1010/BMI.Ayrton.Khamsin.Datasheet.pdf","interpreted",
          "Probably no pass-thru — inferred from consistent absence, not an explicit statement."))

# ── ETC + Chauvet ─────────────────────────────────────────────────────────
R["etc-source-four-led-s3-lustr"] = dict(
  power=P(307,"W","Wattage typical","https://www.fullcompass.com/common/files/60243-S4LEDS3LS0S4LEDSeries3DataSheet.pdf","verified",
          "305 W at 230 V. Whole-fixture draw, not the array rating. Library confirmed.",atV=120),
  powerIn=IN("powerCON TRUE1 TOP","100-240 V, 50/60 Hz","Input method: AC via Neutrik powerCON TRUE1 TOP","https://www.fullcompass.com/common/files/60243-S4LEDS3LS0S4LEDSeries3DataSheet.pdf","verified"),
  powerOut=OUTP(True,'powerCON TRUE1 TOP ("Power Thru")',None,
          "Fixtures per circuit: 5 (link up to 4 via Power Thru connector)","https://www.fullcompass.com/common/files/60243-S4LEDS3LS0S4LEDSeries3DataSheet.pdf","verified",
          "HAS PASS-THRU. ETC gives one total (5 per circuit, i.e. 4 chained beyond the home run), not a per-voltage table."))
R["etc-colorsource-par"] = dict(
  power=P(90,"W","Power Consumption at Full Intensity (120 V column)","https://www.fullcompass.com/common/files/22759-ETCColorSourceParDataSheet.pdf","conflicting",
          "ETC'S OWN DOCS DISAGREE THREE WAYS: datasheet 90 W at 120 V / 89 W at 240 V; install guide "
          "'Typical, Direct at Full' 106 W at 120 V; install guide prose 'Maximum power consumption is 120W'. "
          "Library carried 90. Size cable and breakers off 120 W until this is settled.",atV=120),
  powerIn=IN("powerCON (ETC does not name the variant)","100-240 V, 50/60 Hz","PowerCon in and thru","https://www.etcconnect.com/workarea/DownloadAsset.aspx?id=10737478060","interpreted",
          "ETC names 'TRUE1 TOP' explicitly on the Source Four LED S3 but NOT on this fixture. "
          "Do not assume TRUE1 cable fits — check the physical unit."),
  powerOut=OUTP(True,"powerCON (same unnamed family, 'thru')",None,
          "Up to nine luminaires (15A max) may be linked via power thru connector (10 total per circuit)","https://www.fullcompass.com/common/files/22759-ETCColorSourceParDataSheet.pdf","verified",
          "HAS PASS-THRU. The 9-linked figure is conditioned on an ETC R20 relay module — not universal."))
R["etc-source-four-750-w"] = dict(
  power=P(750,"W","Source Four is rated for 750W maximum / LAMP: 750W maximum","https://www.etcconnect.com/workarea/DownloadAsset.aspx?id=10737460423","verified",
          "THE ONE CASE WHERE LAMP WATTAGE IS THE RIGHT ANSWER: a conventional dimmer-fed fixture with "
          "no electronics. Library confirmed."),
  powerIn=IN("Varies by order suffix: -A Edison (parallel blade), -B 20 A stage pin, -C 20 A twistlock, -M NEMA L515P dimmer-doubling, or bare leads","115-240 V, 50/60 Hz","Connector Designation table","https://www.etcconnect.com/workarea/DownloadAsset.aspx?id=10737460423","verified",
          "NOT a fixed connector — it is chosen at order time. Confirm which suffix these units are."),
  powerOut=OUTP(False,None,None,"No output connector; single 3-conductor lead to one connector","https://www.etcconnect.com/workarea/DownloadAsset.aspx?id=10737460423","verified",
          "NO PASS-THRU. Do not confuse with ETC Dimmer Doubling (-M): that is a dimmer-side Y-splitter, "
          "not a fixture-to-fixture jumper."))
CH = "https://chauvetprofessional.com/wp-content/uploads/"
R["chauvet-maverick-force-s-profile"] = dict(
  power=P(563,"W","Power and Current: 563 W, 4.75 A @ 120 V, 60 Hz",CH+"pdf/en/MAVERICKFORCESPROFILE.pdf","verified",
          "547 W at 208 V, 546 W at 230 V. The 350 W LED source rating is not the draw. Library confirmed.",atV=120),
  powerIn=IN("Seetronic Powerkon IP65 (TRUE1-compatible, Seetronic not Neutrik)","100-240 V, 50/60 Hz","Power Input: Seetronic Powerkon IP65",CH+"pdf/en/MAVERICKFORCESPROFILE.pdf","verified"),
  powerOut=OUTP(True,"Seetronic Powerkon IP65",[[120,2],[208,4],[230,4]],"Power Linking: 2 units @ 120 V; 4 units @ 208 V; 4 units @ 230 V",CH+"pdf/en/MAVERICKFORCESPROFILE.pdf","verified",
          "HAS PASS-THRU with a published per-voltage table."))
R["chauvet-rogue-r2-wash"] = dict(
  power=P(339,"W","Consumption (Technical Specifications, Power table)",CH+"2015/06/ROGUE_R2_Wash_UM_Rev4_WO2.pdf","verified",
          "324 W at 230 V. Library confirmed.",atV=120),
  powerIn=IN("powerCON A-type, blue (Neutrik powerCON A)","100-240 V, 50/60 Hz","Power input connector: Neutrik powerCON A",CH+"2015/06/ROGUE_R2_Wash_UM_Rev4_WO2.pdf","verified",
          "Blue A-type, explicitly NOT TRUE1 — different cable from the Maverick."),
  powerOut=OUTP(True,"powerCON (rear panel 'Power Out')",[[120,4],[208,8],[230,9]],
          '"You can power link up to 4 products at 120 V; up to 8 at 208 V; or up to 9 at 230 V"',CH+"2015/06/ROGUE_R2_Wash_UM_Rev4_WO2.pdf","verified",
          "HAS PASS-THRU. Also: no RDM anywhere in the manual — a confirmed negative, correcting the "
          "library's load-time default."))

# ── GLP / SGM / Elation ───────────────────────────────────────────────────
GL = "https://germanlightproducts.com/wp-content/uploads/"
R["glp-jdc1"] = dict(
  power=P(1200,"W","Power (@ 230V)",GL+"2018/03/JDC1-User-Manual-EN-v1.0.pdf","verified",
          "No separate peak/strobe figure is published despite the heavy strobe draw — searched for one. Library confirmed.",atV=230),
  powerIn=IN("powerCON TRUE1","100-240 V, 50-60 Hz","Power Input Neutrik powerCON TRUE1",GL+"2018/03/JDC1-User-Manual-EN-v1.0.pdf","verified"),
  powerOut=OUTP(False,None,None,"Electrical tables list only a Power Input with no output entry",GL+"2018/03/JDC1-User-Manual-EN-v1.0.pdf","verified",
          "NO PASS-THRU — confirmed across manual and spec sheet. Its 5-pin XLR in/out is data."))
R["glp-impression-x4-bar-20"] = dict(
  power=P(450,"W","Power consumption",GL+"2019/02/impression_X4Bar20_manual_v1.9_EN.pdf","conflicting",
          "LIBRARY CARRIED 400. GLP's manual says 450 W; GLP's own website says 400 W 'Typical Power (@ 230 V)'. "
          "Two manufacturer sources, two numbers. Not adjudicated."),
  powerIn=IN("powerCON, blue (Neutrik locking 3-conductor; GLP does NOT say TRUE1)","100-240 V, 50-60 Hz","NEUTRIK powerCON locking 3 conductor AC connectors",GL+"2019/02/impression_X4Bar20_manual_v1.9_EN.pdf","verified",
          "Blue in / grey out. Manual never says TRUE1 — this generation may predate it. Check the unit."),
  powerOut=OUTP(True,"powerCON, grey (throughput socket)",None,'"the grey connector must be used to draw AC mains power from the fixtures\' throughput sockets"',GL+"2019/02/impression_X4Bar20_manual_v1.9_EN.pdf","verified",
          "HAS PASS-THRU, built for daisy-chaining. No fixture-count table; instead a hard cap: "
          "'never connect more than a total load of 20A'."))
R["sgm-q-7"] = dict(
  power=P(465,"W","Max power consumption","https://www.sgmlighting.com/products/q%c2%b77","verified",
          "Standby 8 W. Library confirmed."),
  powerIn=IN("powerCON twist-lock inlet, fed by a supplied cable with BARE ENDS on the mains side","208-240 V, 50/60 Hz","Connect the powercon twist-lock connector side to the fixture","https://www.stageeventlight.se/upl/files/199018/sgm-q-7-user-manual-rev-f-.pdf","interpreted",
          "TWO GOTCHAS: SGM never names the powerCON family, and the supplied cable is bare-ended — "
          "someone terminates it. Also 208-240 V ONLY, not 100-240 V: a standard Edison circuit will not do."),
  powerOut=OUTP(False,None,None,'"The fixture is designed as an end-use device only"',"https://www.stageeventlight.se/upl/files/199018/sgm-q-7-user-manual-rev-f-.pdf","verified",
          "NO PASS-THRU, explicitly stated. SGM does publish breaker loading: max 4 fixtures on a 10 A "
          "type C breaker, 7 on a 16 A. Its DMX 'thru' is passive data, not power."))
R["elation-proteus-maximus"] = dict(
  power=P(1400,"W","Max Power Consumption","https://shop.bmisupply.com/Resources/en/ItemDocuments/39E1019/ELATION%20PROTEUS%20MAXIMUS%20-%20SPEC%20SHEET.pdf","verified",
          "The 950 W figure is the LED engine, not the draw. Library confirmed."),
  powerIn=IN('"IP65 Locking Power Cable In" — Elation never names the connector family',"120-240 V, 50/60 Hz","IP65 Locking Power Cable In","https://shop.bmisupply.com/Resources/en/ItemDocuments/39E1019/ELATION%20PROTEUS%20MAXIMUS%20-%20USER%20MANUAL.pdf","interpreted",
          "REAL GAP: neither the spec sheet nor the full manual names the connector. Physically confirm before ordering."),
  powerOut=OUTP(False,None,None,"Only 'IP65 Locking Power Cable In' listed; no output entry in either document","https://shop.bmisupply.com/Resources/en/ItemDocuments/39E1019/ELATION%20PROTEUS%20MAXIMUS%20-%20USER%20MANUAL.pdf","verified",
          "NO PASS-THRU, confirmed across two Elation documents. Its RJ45 and XLR in/out are data."))

# ── Atmospherics + control ────────────────────────────────────────────────
R["mdg-theone-hazer"] = dict(
  power=P(1480,"W","Power consumption","https://mdgfog.s3.amazonaws.com/uploads/docs/theONE-User-Guide-Rev-Af.pdf","verified",
          "1100 W at 100 VAC, 1480 W at 250 VAC. NOT a peak-vs-standby split — these are the two ends of "
          "the accepted line-voltage range. Library confirmed.",atV=250),
  powerIn=IN(None,"100-250 VAC, 50/60 Hz, single phase","Operating voltage","https://mdgfog.s3.amazonaws.com/uploads/docs/theONE-User-Guide-Rev-Af.pdf","missing",
          "MDG publishes only the mains cable gauge (1.5 mm2 / 14 AWG, 3-wire) and never names a plug."),
  powerOut=OUTP(False,None,None,"No power output in any connection diagram","https://mdgfog.s3.amazonaws.com/uploads/docs/theONE-User-Guide-Rev-Af.pdf","verified",
          "NO PASS-THRU."))
R["look-viper-nt-fogger"] = dict(
  power=P(1300,"W","Power requirement","https://shop.bmisupply.com/Resources/en/ItemDocuments/190VI0194/BMI.Viper.NT.Manual.pdf","verified",
          "Two factory voltage variants (230 V/50 Hz or 120 V/60 Hz), not auto-ranging. No separate "
          "heat-up vs running figure is published. Library confirmed."),
  powerIn=IN(None,"230 V/50 Hz or 120 V/60 Hz (two factory variants)","Voltage","https://shop.bmisupply.com/Resources/en/ItemDocuments/190VI0194/BMI.Viper.NT.Manual.pdf","missing",
          "Manual says only 'Mains cable' and never names the plug."),
  powerOut=OUTP(False,None,None,"Pin 3 = 12 V + DC out, max. 50 mA","https://shop.bmisupply.com/Resources/en/ItemDocuments/190VI0194/BMI.Viper.NT.Manual.pdf","verified",
          "NO MAINS PASS-THRU. It has a 3-pin XLR accessory socket supplying 12 V DC at 50 mA — a "
          "low-voltage accessory feed, not a mains output. Do not mistake one for the other."))
R["ma-lighting-grandma3-full-size"] = dict(
  power=P(300,"VA","Power max.","https://www.fullcompass.com/common/files/88658-grandMA3fullsizeSpecSheet.pdf","verified",
          "Total through the single inlet, not per-supply. Library confirmed."),
  powerIn=IN("powerCON TRUE1 (Neutrik NAC3FX-W-TOP), 1 inlet","100-240 V, 50/60 Hz","1 x powerCON TRUE1","https://www.fullcompass.com/common/files/88658-grandMA3fullsizeSpecSheet.pdf","verified"),
  powerOut=OUTP(False,None,None,"1 x powerCON TRUE1","https://www.fullcompass.com/common/files/88658-grandMA3fullsizeSpecSheet.pdf","verified",
          "FOH PLANNING: exactly ONE mains inlet. This is NOT a dual-feed console. The built-in UPS is "
          "internal ride-through against one feed dropping, not licence to split the load across two circuits."))
R["cm-lodestar-1-ton-hoist"] = dict(
  power=P(1450,"VA","Full load amps / Full Load Current","https://tsriggingequipment.com/pdf/cm-et-lodestar-nh-manual.pdf","conflicting",
          "THREE-PHASE MOTOR, not a fixture circuit. CM's own documents disagree on 1-ton Model L full-load "
          "current: 3.7/2.2 A (230/460 V) in the general catalog vs 3.0/1.5 A in the Entertainment manual. "
          "The library's 1450 VA is roughly consistent with 3.7 A at 230 V three-phase, but is not itself "
          "a published figure. Inrush on start is far higher and CM publishes no figure for it.",atV=230),
  powerIn=IN("Not specified by CM — ships for hardwire/bare-lead termination","230/460-3-60 (also 220/380-3-50, 220/415-3-50), THREE PHASE","230/460-3-60","https://tsriggingequipment.com/pdf/cm-et-lodestar-nh-manual.pdf","verified",
          "Fed from a motor distro, not a branch circuit. Rental houses commonly build their own control "
          "cable (a 7-pin Socapex-family cable is common practice) but that is convention, not a CM spec."),
  powerOut=OUTP(False,None,None,"Not a pass-through device","https://tsriggingequipment.com/pdf/cm-et-lodestar-nh-manual.pdf","verified",
          "Fed one leg per hoist from a motor control distro. Not daisy-chained."))

# ── merge onto the seeded records ─────────────────────────────────────────
batch, stats = [], {"verified":0,"conflicting":0,"missing":0,"interpreted":0}
passthru = {"yes":[], "no":[], "unknown":[]}

for f in sorted(SEED.glob("*.json")):
    fid = f.stem
    doc = json.loads(f.read_text())
    r = R.get(fid)
    if not r:
        print("  no research for", fid); continue
    doc["power"]    = r["power"]
    doc["powerIn"]  = r["powerIn"]
    doc["powerOut"] = r["powerOut"]
    doc["researchedAt"] = D
    doc.pop("seededFrom", None)
    doc["updatedAt"] = D + "T12:00:00.000Z"

    stats[r["power"]["status"]] = stats.get(r["power"]["status"], 0) + 1
    p = r["powerOut"]["present"]
    passthru["yes" if p is True else "no" if p is False else "unknown"].append(fid)

    out = OUT / f.name
    out.write_text(json.dumps(doc, indent=1, ensure_ascii=False))
    batch.append({"op":"set","collection":"fixtures","doc_id":fid,"file_path":str(out.resolve())})

(HERE/"verified_batch.json").write_text(json.dumps(batch, indent=1))
print(f"\nmerged {len(batch)} fixtures")
print("power status:", stats)
print(f"\nPASS-THRU: {len(passthru['yes'])} yes / {len(passthru['no'])} no / {len(passthru['unknown'])} unknown")
print("  has pass-thru:", ", ".join(passthru["yes"]))
print("  unknown     :", ", ".join(passthru["unknown"]))
