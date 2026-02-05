"""
AI Trading Bot System - Index Manager (Multi-Market Architecture)

Purpose: Manages stock index constituents with live updates and caching.
Supports ASX (ASX 50, ASX 200), USA (S&P 500, NASDAQ 100), and
Taiwan Stock Exchange (TSEC 50, TSEC 100) indices.

Author: Yannick
Copyright (c) 2026 Yannick
"""

import pandas as pd
import json
import os
import re
import requests
from typing import List, Dict

CACHE_FILE = "models/index_cache.json"

# Reliable sources for ASX Indices
SOURCE_URLS = {
    "ASX 50": "https://www.asx50list.com/",
    "ASX 200": "https://www.asx200list.com/",
}

DEFAULT_INDEX_DATA = {
    "ASX 50": [
        "ALL.AX",
        "AMC.AX",
        "ANZ.AX",
        "BHP.AX",
        "BXB.AX",
        "CAR.AX",
        "CBA.AX",
        "COH.AX",
        "COL.AX",
        "CPU.AX",
        "CSL.AX",
        "EVN.AX",
        "FMG.AX",
        "FPH.AX",
        "GMG.AX",
        "IAG.AX",
        "JBH.AX",
        "JHX.AX",
        "LYC.AX",
        "MIN.AX",
        "MPL.AX",
        "MQG.AX",
        "NAB.AX",
        "NEM.AX",
        "NST.AX",
        "NWS.AX",
        "ORG.AX",
        "PME.AX",
        "QAN.AX",
        "QBE.AX",
        "REA.AX",
        "RIO.AX",
        "RMD.AX",
        "S32.AX",
        "SCG.AX",
        "SGH.AX",
        "SGP.AX",
        "SHL.AX",
        "SIG.AX",
        "SOL.AX",
        "STO.AX",
        "SUN.AX",
        "TCL.AX",
        "TLS.AX",
        "VAS.AX",
        "WBC.AX",
        "WDS.AX",
        "WES.AX",
        "WOW.AX",
        "XRO.AX",
    ],
    "ASX 200": [
        "A2M.AX",
        "AAA.AX",
        "ABC.AX",
        "ABP.AX",
        "AFI.AX",
        "AGL.AX",
        "AIA.AX",
        "ALD.AX",
        "ALL.AX",
        "ALQ.AX",
        "ALU.AX",
        "ALX.AX",
        "AMC.AX",
        "AMP.AX",
        "ANN.AX",
        "ANZ.AX",
        "APA.AX",
        "APE.AX",
        "APT.AX",
        "APX.AX",
        "ARB.AX",
        "ARG.AX",
        "AST.AX",
        "ASX.AX",
        "AWC.AX",
        "AZJ.AX",
        "BAP.AX",
        "BEN.AX",
        "BGA.AX",
        "BHP.AX",
        "BIN.AX",
        "BKW.AX",
        "BLD.AX",
        "BOQ.AX",
        "BPT.AX",
        "BRG.AX",
        "BSL.AX",
        "BWP.AX",
        "BXB.AX",
        "CAR.AX",
        "CBA.AX",
        "CCL.AX",
        "CCP.AX",
        "CDA.AX",
        "CGF.AX",
        "CHC.AX",
        "CHN.AX",
        "CIA.AX",
        "CIM.AX",
        "CLW.AX",
        "CMW.AX",
        "CNU.AX",
        "COH.AX",
        "COL.AX",
        "CPU.AX",
        "CQR.AX",
        "CSL.AX",
        "CSR.AX",
        "CTD.AX",
        "CWN.AX",
        "CWY.AX",
        "DEG.AX",
        "DHG.AX",
        "DMP.AX",
        "DOW.AX",
        "DRR.AX",
        "DXS.AX",
        "EBO.AX",
        "ELD.AX",
        "EML.AX",
        "EVN.AX",
        "EVT.AX",
        "FBU.AX",
        "FLT.AX",
        "FMG.AX",
        "FPH.AX",
        "GMG.AX",
        "GNE.AX",
        "GOZ.AX",
        "GPT.AX",
        "GXY.AX",
        "HLS.AX",
        "HVN.AX",
        "IAG.AX",
        "IEL.AX",
        "IFL.AX",
        "IFT.AX",
        "IGO.AX",
        "ILU.AX",
        "IOO.AX",
        "IOZ.AX",
        "IPL.AX",
        "IRE.AX",
        "IVV.AX",
        "JBH.AX",
        "JHX.AX",
        "LFG.AX",
        "LFS.AX",
        "LLC.AX",
        "LNK.AX",
        "LYC.AX",
        "MCY.AX",
        "MEZ.AX",
        "MFG.AX",
        "MGF.AX",
        "MGOC.AX",
        "MGR.AX",
        "MIN.AX",
        "MLT.AX",
        "MP1.AX",
        "MPL.AX",
        "MQG.AX",
        "MTS.AX",
        "NAB.AX",
        "NCM.AX",
        "NEC.AX",
        "NHF.AX",
        "NIC.AX",
        "NSR.AX",
        "NST.AX",
        "NUF.AX",
        "NWL.AX",
        "NXT.AX",
        "ORA.AX",
        "ORE.AX",
        "ORG.AX",
        "ORI.AX",
        "OSH.AX",
        "OZL.AX",
        "PBH.AX",
        "PDL.AX",
        "PLS.AX",
        "PME.AX",
        "PMGOLD.AX",
        "PMV.AX",
        "PNI.AX",
        "PNV.AX",
        "PPT.AX",
        "PTM.AX",
        "QAN.AX",
        "QBE.AX",
        "QUB.AX",
        "REA.AX",
        "REH.AX",
        "RHC.AX",
        "RIO.AX",
        "RMD.AX",
        "RRL.AX",
        "RWC.AX",
        "S32.AX",
        "SCG.AX",
        "SCP.AX",
        "SDF.AX",
        "SEK.AX",
        "SGM.AX",
        "SGP.AX",
        "SGR.AX",
        "SHL.AX",
        "SKC.AX",
        "SKI.AX",
        "SLK.AX",
        "SNZ.AX",
        "SOL.AX",
        "SPK.AX",
        "STO.AX",
        "STW.AX",
        "SUL.AX",
        "SUN.AX",
        "SVW.AX",
        "SYD.AX",
        "TAH.AX",
        "TCL.AX",
        "TLS.AX",
        "TLT.AX",
        "TNE.AX",
        "TPG.AX",
        "TWE.AX",
        "TYR.AX",
        "VAP.AX",
        "VAS.AX",
        "VCX.AX",
        "VEA.AX",
        "VEU.AX",
        "VGS.AX",
        "VOC.AX",
        "VTS.AX",
        "VUK.AX",
        "WAM.AX",
        "WBC.AX",
        "WEB.AX",
        "WES.AX",
        "WOR.AX",
        "WOW.AX",
        "WPL.AX",
        "WPR.AX",
        "WTC.AX",
        "XRO.AX",
        "YAL.AX",
        "Z1P.AX",
        "ZIM.AX",
    ],
}


def load_index_constituents() -> Dict[str, List[str]]:
    """Loads constituents from local cache or defaults."""
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return DEFAULT_INDEX_DATA
    return DEFAULT_INDEX_DATA


def update_index_data() -> Dict[str, str]:
    """Fetches latest constituents from HTML tables and updates cache."""
    updated_counts = {}
    new_data = {}

    for name, url in SOURCE_URLS.items():
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            html = response.text

            # Look for patterns like <td>ABC</td> or <tr><td>ABC</td>
            # Most ASX list sites use simple tables
            potential_tickers = re.findall(r"<td>([A-Z0-9]{3,6})</td>", html)

            # Filter and append .AX
            tickers = sorted(
                list(
                    set(
                        [
                            f"{t.strip()}.AX"
                            for t in potential_tickers
                            if len(t.strip()) >= 3 and len(t.strip()) <= 6
                        ]
                    )
                )
            )

            if len(tickers) > 5:  # Sanity check
                new_data[name] = tickers
                updated_counts[name] = f"Updated {len(tickers)} tickers"
            else:
                updated_counts[name] = "Failed: No tickers found in HTML"
                new_data[name] = DEFAULT_INDEX_DATA.get(name, [])
        except Exception as e:
            updated_counts[name] = f"Failed: {str(e)}"
            new_data[name] = DEFAULT_INDEX_DATA.get(name, [])

    # Save to cache
    os.makedirs("models", exist_ok=True)
    with open(CACHE_FILE, "w") as f:
        json.dump(new_data, f)

    return updated_counts
