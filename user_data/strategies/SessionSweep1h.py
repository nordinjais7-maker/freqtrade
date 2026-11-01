"""
SessionSweep1h - the SessionSweep rules on 1-hour candles.

Same logic, parameters and callbacks as SessionSweep (see that file); only the
base timeframe and a few candle-count defaults change:

* Asia range = 1h candles opening 00:00-06:00 (window [00:00, 07:00)).
* London = candles opening 07:00-11:00. New York = candles opening 13:00-16:00,
  because the 12:00 candle opens before the 12:30 session start; set
  ny_start_min to 720 to include it.
* sweep_lookback / confirm_window / entry_wait_candles default to 2 candles
  (2 hours) instead of 6 (30 minutes on 5m).

The 1h informative merge is a no-op on a 1h base (same timeframe), the 4h one
still shifts correctly. Needs 1h and 4h data only.
"""

import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).parent))
from SessionSweep import SessionSweep

from freqtrade.strategy import IntParameter


class SessionSweep1h(SessionSweep):
    timeframe = "1h"
    # 4h EMA(50) needs 200h; 300 x 1h candles gives headroom.
    startup_candle_count = 300

    sweep_lookback = IntParameter(1, 12, default=2, space="buy", optimize=True)
    confirm_window = IntParameter(1, 12, default=2, space="buy", optimize=False)
    entry_wait_candles = IntParameter(1, 12, default=2, space="buy", optimize=False)
    mss_lookback = IntParameter(2, 12, default=3, space="buy", optimize=False)
