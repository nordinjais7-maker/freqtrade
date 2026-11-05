"""
SessionMomentum1h - the SessionMomentum rules on 1-hour candles.

Same logic, parameters and callbacks as SessionMomentum (see that file); only
the base timeframe changes. On 1h candles a breakout is the first HOURLY close
beyond the Asia range during London (candles opening 07:00-11:00) or New York
(candles opening 13:00-16:00; set ny_start_min to 720 to include the 12:00
candle). Displacement and volume are measured against hourly ATR / volume, with
softer defaults (0.5 ATR body, 1.2x volume) than the 5m version.
Needs 1h and 4h data only.
"""

import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).parent))
from SessionMomentum import SessionMomentum

from freqtrade.strategy import DecimalParameter


class SessionMomentum1h(SessionMomentum):
    timeframe = "1h"
    # 4h EMA(50) needs 200h; 300 x 1h candles gives headroom.
    startup_candle_count = 300

    # An hourly candle rarely has a body of a full hourly ATR, and hourly volume
    # is far less spiky than 5m volume, so the confirmation thresholds are softer.
    displacement_atr_mult = DecimalParameter(
        0.0, 3.0, default=0.5, decimals=2, space="buy", optimize=False
    )
    volume_mult = DecimalParameter(0.0, 5.0, default=1.2, decimals=2, space="buy", optimize=False)
