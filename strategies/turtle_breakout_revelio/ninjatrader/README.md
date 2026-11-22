# Turtle Breakout - Revelio on NinjaTrader 8, simulation accounts

`TurtleBreakoutRevelio.cs` trades the tested rules (day-trading schedule off) by itself in a NinjaTrader sim account.
It is for simulation only. It has not been compiled or run in NinjaTrader yet: the first compile and the first
week on sim are the test. Report any compile error or odd order and it gets fixed.

## What was checked
`scripts/check_ninjatrader_logic.py` replays the strategy's order flow (orders placed at each candle close, filled on
later candles) on the same data as the backtests:

| market | backtest signals | same entry candle | P&L per trade vs backtest |
|---|---|---|---|
| MNQ | 53 | 53 | 1 to 2 ticks worse |
| Bitcoin (BTC prices) | 42 | 42 | 0 to 2 ticks worse |
| S&P 500 (ES prices) | 66 | 66 | 1 to 2 ticks worse |

The tick difference is on purpose: the rules need price to trade *beyond* a level (high > entry band, low < stop),
so the buy stop sits 1 tick above the entry band and the sell stop on the first tick below the exit. The backtest
filled exactly at the level and charged slippage on top. That check tests the logic, not the C# or NinjaTrader's fills.

## Setup
1. **Data.** You need a real-time CME futures feed for MBT, MES and MNQ in NinjaTrader (the built-in "Simulated
   Data Feed" is random prices and will not do). Set Tools > Options > Market data > Merge policy to
   *Merge back adjusted*, the same back-adjustment the backtests used.
2. **Install.** Copy `TurtleBreakoutRevelio.cs` to `Documents\NinjaTrader 8\bin\Custom\Strategies\`, open
   New > NinjaScript Editor, and press F5 to compile.
3. **Three sim accounts, one per strategy.** Sizing reads each account's cash balance as closed equity, so the
   accounts must not be shared. Add three simulation accounts (for example `SimMBT`, `SimMES`, `SimMNQ`) and reset
   each to $10,000. Give each a commission template matching the backtest's fees (round trip, per contract):
   MBT $5.00, MES $1.50, MNQ $1.50. Slippage comes from the sim fills and the one-tick-through orders.
4. **Three charts**, 30-minute bars, front-month contract, the instrument's full electronic (ETH, not RTH) trading
   hours, at least 120 days loaded. Add the strategy to each:

| chart | Account | Sizing | Risk % | Contracts | Max contracts |
|---|---|---|---|---|---|
| MBT | SimMBT | PercentOfEquity | 10 | – | 100 |
| MES | SimMES | PercentOfEquity | 10 | – | 100 |
| MNQ | SimMNQ | FixedContracts | – | 1 | 1 |

   Leave the rule inputs at 20 / 10 / 20 / 2. Start behavior: *Wait until flat*. If history shows a signal already
   running, the strategy waits for it to end and takes the next breakout. Joining a signal late is not in the rules.

## Running it
- **Restarts while in a trade.** Disabling the strategy cancels its stop. To restart with a position open, enable it
  with Start behavior *Adopt account position*, then check the sell stop is back on the chart.
- **Rolls.** NinjaTrader trades one contract month. MES and MNQ roll quarterly, MBT monthly. On roll day: if flat,
  move the chart and strategy to the new month. If in a trade: disable the strategy, close the old month, buy the
  same quantity in the new month, then enable it with *Adopt account position*. That is the extra round trip the
  backtests charged for each roll.
- **Margin.** At 10% risk the MBT account grew to 71 contracts in the backtest. Check the sim's margin. A rejected
  order is a finding to record, not something to work around by changing the rules mid-test.
- **Journal.** Each strategy appends to `Documents\NinjaTrader 8\TurtleRevelio_<market>_<account>.csv`: breakouts
  (with the contracts it would size), fills, signal exits, and each trade's R and P&L before costs. Add your own
  column for rule violations. Any manual order or setting change during a trade makes that trade *invalid*.

## Reading the forward test
The three markets together produced about 19 trades a year in the backtest, so 50 trades takes about 2.5 years.
Compare each trade's R with the backtest's distribution rather than judging the first few results. Bitcoin's edge
came from a few very large winners, so months of small losses are what the backtest says to expect.
