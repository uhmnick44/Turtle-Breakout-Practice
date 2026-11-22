// Turtle Breakout - Revelio, NinjaTrader 8 strategy for SIMULATED accounts.
// Same rules as scripts/backtest.py with the day-trading schedule off (the tested "pure" system):
//   Trading days run 17:00 to 17:00 New York. Bands and ATR use completed days only; the first loaded day is discarded.
//   Entry: resting buy stop one tick above the highest daily high of the last N completed days (or the open on a gap).
//   Initial stop: max(entry level, open of the breakout candle) - ATR multiple x ATR (20-day, Wilder), fixed for the signal.
//   Exit: sell stop on the first tick below the higher of that stop and the lowest daily low of the last M completed days.
//   One position at a time, long only, no re-entry until the signal has ended.
// Sizing, decided when the entry order is placed:
//   PercentOfEquity: contracts = floor(risk% x closed equity / (ATR multiple x ATR x point value)); 0 = signal skipped.
//   FixedContracts:  the same number of contracts on every signal, whatever the stop.
// Not financial advice. Built for a simulation account; check every setting before enabling it.

#region Using declarations
using System;
using System.ComponentModel;
using System.ComponentModel.DataAnnotations;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Windows.Media;
using NinjaTrader.Cbi;
using NinjaTrader.Data;
using NinjaTrader.Gui;
using NinjaTrader.NinjaScript;
using NinjaTrader.NinjaScript.Strategies;
#endregion

namespace NinjaTrader.NinjaScript.Strategies
{
    public enum TurtleSizingMode { PercentOfEquity, FixedContracts }

    public class TurtleBreakoutRevelio : Strategy
    {
        private const string EntryName = "TB Entry";
        private const string ExitName = "TB Exit";
        private TimeZoneInfo ny;

        // daily aggregation
        private readonly List<double> highs = new List<double>();
        private readonly List<double> lows = new List<double>();
        private double atr = double.NaN, atrSeed = 0, prevClose = double.NaN;
        private int atrCount = 0;
        private double dHigh = double.NaN, dLow = double.NaN, dClose = double.NaN;
        private DateTime curSession = DateTime.MinValue;
        private bool dayCompleted = false, skipFirst = true;

        // signal state (mirrors the indicator, independent of whether an order filled)
        private bool signalLong = false;
        private double stop = double.NaN;

        // orders and journal
        private Order entryOrder, exitOrder;
        private double entryFill = double.NaN, riskPtsAtEntry = double.NaN, equityAtEntry = double.NaN;
        private int qtyAtEntry = 0;
        private DateTime entryTime;
        private string journalPath;

        protected override void OnStateChange()
        {
            if (State == State.SetDefaults)
            {
                Name = "TurtleBreakoutRevelio";
                Description = "Turtle Breakout - Revelio, overnight (day-trading schedule off), for simulation accounts.";
                Calculate = Calculate.OnBarClose;
                EntriesPerDirection = 1;
                EntryHandling = EntryHandling.AllEntries;
                IsExitOnSessionCloseStrategy = false;
                IsFillLimitOnTouch = false;
                BarsRequiredToTrade = 0;
                MaximumBarsLookBack = MaximumBarsLookBack.TwoHundredFiftySix;
                OrderFillResolution = OrderFillResolution.Standard;
                StartBehavior = StartBehavior.WaitUntilFlat;
                IsAdoptAccountPositionAware = true;
                RealtimeErrorHandling = RealtimeErrorHandling.StopCancelClose;
                StopTargetHandling = StopTargetHandling.PerEntryExecution;
                TraceOrders = true;
                IncludeCommission = true;

                EntryDays = 20; ExitDays = 10; AtrDays = 20; AtrMultiple = 2.0;
                Sizing = TurtleSizingMode.PercentOfEquity;
                RiskPercent = 10.0; FixedQuantity = 1; MaxContracts = 100;
                StartingCapital = 10000; UseAccountCashValue = true; WriteJournal = true;

                AddPlot(new Stroke(Brushes.Teal, 2), PlotStyle.Square, "Entry band");
                AddPlot(new Stroke(Brushes.Orange, 1), PlotStyle.Square, "Exit band");
                AddPlot(new Stroke(Brushes.Red, 2), PlotStyle.Square, "Active exit");
            }
            else if (State == State.DataLoaded)
            {
                ny = TimeZoneInfo.FindSystemTimeZoneById("Eastern Standard Time");
                journalPath = Path.Combine(NinjaTrader.Core.Globals.UserDataDir, "TurtleRevelio_" + Instrument.MasterInstrument.Name + "_" + Account.Name + ".csv");
            }
        }

        protected override void OnBarUpdate()
        {
            if (BarsInProgress != 0) return;
            if (BarsPeriod.BarsPeriodType != BarsPeriodType.Minute || 30 % BarsPeriod.Value != 0)
            {
                if (CurrentBar == 0) Log("TurtleBreakoutRevelio: use a 1, 5, 15 or 30-minute chart (30 matches the backtest).", LogLevel.Error);
                return;
            }

            // NinjaTrader stamps a bar with its close time in the platform's time zone.
            DateTime closeNy = TimeZoneInfo.ConvertTime(Time[0], NinjaTrader.Core.Globals.GeneralOptions.TimeZoneInfo, ny);
            DateTime openNy = closeNy.AddMinutes(-BarsPeriod.Value);
            DateTime session = openNy.TimeOfDay < TimeSpan.FromHours(17) ? openNy.Date.AddDays(-1) : openNy.Date; // session starts at 17:00 on this date
            DateTime sessionEnd = session.AddDays(1).AddHours(17);

            if (session != curSession)
            {
                if (!double.IsNaN(dHigh) && !dayCompleted) CompleteDay(); // early close or missing candles: day ends at the next session's first candle
                dHigh = High[0]; dLow = Low[0]; dClose = Close[0];
                curSession = session; dayCompleted = false;
            }
            else
            {
                dHigh = Math.Max(dHigh, High[0]); dLow = Math.Min(dLow, Low[0]); dClose = Close[0];
            }

            double entryLevel = highs.Count == EntryDays ? highs.Max() : double.NaN;
            double exitLevel = lows.Count == ExitDays ? lows.Min() : double.NaN;
            bool ready = !double.IsNaN(entryLevel) && !double.IsNaN(exitLevel) && !double.IsNaN(atr);

            // ---- signal logic, same order as the indicator, at this candle's close ----
            if (ready)
            {
                bool wasLong = signalLong;
                bool breakout = !wasLong && High[0] > entryLevel;
                bool exitEvent = false;
                if (breakout)
                {
                    stop = Math.Max(entryLevel, Open[0]) - AtrMultiple * atr;
                    signalLong = true;
                    exitEvent = Low[0] < stop;
                    Journal("breakout", entryLevel, stop, exitLevel, ComputeQuantity(), "");
                }
                else if (wasLong)
                    exitEvent = Low[0] < Math.Max(stop, exitLevel);
                if (exitEvent)
                {
                    signalLong = false;
                    Journal("signal_exit", entryLevel, stop, exitLevel, 0, "");
                }
            }

            // The candle that closes the trading day completes it now, so the next candle trades on the new bands.
            if (closeNy >= sessionEnd && !dayCompleted) { CompleteDay(); dayCompleted = true; }

            entryLevel = highs.Count == EntryDays ? highs.Max() : double.NaN;
            exitLevel = lows.Count == ExitDays ? lows.Min() : double.NaN;
            ready = !double.IsNaN(entryLevel) && !double.IsNaN(exitLevel) && !double.IsNaN(atr);
            if (!ready) return;
            Values[0][0] = entryLevel; Values[1][0] = exitLevel;
            if (signalLong) Values[2][0] = Math.Max(stop, exitLevel);

            // ---- orders for the next candle ----
            if (Position.MarketPosition == MarketPosition.Long)
            {
                CancelIfWorking(entryOrder);
                double sellStop = signalLong ? TickBelow(Math.Max(stop, exitLevel)) : double.NaN;
                if (!signalLong || Close[0] <= sellStop)
                    ExitLong(Position.Quantity, ExitName, EntryName);
                else
                    ExitLongStopMarket(0, true, Position.Quantity, sellStop, ExitName, EntryName);
            }
            else if (Position.MarketPosition == MarketPosition.Flat)
            {
                if (signalLong) { CancelIfWorking(entryOrder); return; } // a signal is running (taken and closed, or skipped): wait for it to end
                int qty = ComputeQuantity();
                if (qty <= 0) { CancelIfWorking(entryOrder); return; }   // stop too wide for the risk budget: the next breakout is skipped
                double level = TickAbove(entryLevel);
                if (Close[0] >= level)
                {
                    CancelIfWorking(entryOrder);
                    EnterLong(qty, EntryName);
                }                             // bands moved below the price at the day change: buy the next open
                else
                    EnterLongStopMarket(0, true, qty, level, EntryName);
            }
        }

        private void CompleteDay()
        {
            if (skipFirst) { skipFirst = false; return; }
            highs.Add(dHigh); if (highs.Count > EntryDays) highs.RemoveAt(0);
            lows.Add(dLow); if (lows.Count > ExitDays) lows.RemoveAt(0);
            double tr = double.IsNaN(prevClose) ? dHigh - dLow
                : Math.Max(dHigh - dLow, Math.Max(Math.Abs(dHigh - prevClose), Math.Abs(dLow - prevClose)));
            if (double.IsNaN(atr))
            {
                atrSeed += tr; atrCount++;
                if (atrCount == AtrDays) atr = atrSeed / AtrDays;
            }
            else atr = (atr * (AtrDays - 1) + tr) / AtrDays;
            prevClose = dClose;
        }

        private double ClosedEquity()
        {
            if (State == State.Realtime)
                return UseAccountCashValue ? Account.Get(AccountItem.CashValue, Currency.UsDollar)
                                           : StartingCapital + SystemPerformance.RealTimeTrades.TradesPerformance.Currency.CumProfit;
            return StartingCapital + SystemPerformance.AllTrades.TradesPerformance.Currency.CumProfit;
        }

        private int ComputeQuantity()
        {
            if (Sizing == TurtleSizingMode.FixedContracts) return FixedQuantity;
            if (double.IsNaN(atr) || atr <= 0) return 0;
            double perContract = AtrMultiple * atr * Instrument.MasterInstrument.PointValue;
            int q = (int)Math.Floor(ClosedEquity() * RiskPercent / 100.0 / perContract);
            return Math.Max(0, Math.Min(q, MaxContracts));
        }

        // The rules need a price to trade beyond a level, not just touch it ("high > entry level", "low < stop").
        // So the buy stop sits one tick above the entry level and the sell stop on the first tick below the exit level.
        private double TickAbove(double level)
        {
            double t = TickSize;
            return Instrument.MasterInstrument.RoundToTickSize((Math.Floor(level / t + 1e-9) + 1) * t);
        }

        private double TickBelow(double level)
        {
            double t = TickSize;
            return Instrument.MasterInstrument.RoundToTickSize((Math.Ceiling(level / t - 1e-9) - 1) * t);
        }

        private void CancelIfWorking(Order o)
        {
            if (o != null && (o.OrderState == OrderState.Working || o.OrderState == OrderState.Accepted || o.OrderState == OrderState.Submitted))
                CancelOrder(o);
        }

        protected override void OnOrderUpdate(Order order, double limitPrice, double stopPrice, int quantity, int filled,
            double averageFillPrice, OrderState orderState, DateTime time, ErrorCode error, string comment)
        {
            if (order.Name == EntryName) entryOrder = order;
            if (order.Name == ExitName) exitOrder = order;
            if (orderState == OrderState.Filled || orderState == OrderState.Cancelled || orderState == OrderState.Rejected)
            {
                if (order == entryOrder) entryOrder = null;
                if (order == exitOrder) exitOrder = null;
            }
        }

        protected override void OnExecutionUpdate(Execution execution, string executionId, double price, int quantity,
            MarketPosition marketPosition, string orderId, DateTime time)
        {
            if (execution.Order == null || execution.Order.OrderState != OrderState.Filled) return;
            if (execution.Order.Name == EntryName)
            {
                // Protect the position at once. The candle-close logic then sets the exact stop from the breakout candle's open.
                double level = highs.Count == EntryDays ? highs.Max() : price;
                double exitLevel = lows.Count == ExitDays ? lows.Min() : double.NaN;
                if (!signalLong) stop = Math.Max(level, price) - AtrMultiple * atr;
                double active = double.IsNaN(exitLevel) ? stop : Math.Max(stop, exitLevel);
                ExitLongStopMarket(0, true, execution.Order.Filled, TickBelow(active), ExitName, EntryName);
                entryFill = execution.Order.AverageFillPrice; riskPtsAtEntry = AtrMultiple * atr; qtyAtEntry = execution.Order.Filled;
                equityAtEntry = ClosedEquity(); entryTime = time;
                Journal("entry_fill", level, stop, exitLevel, qtyAtEntry, "fill " + entryFill);
            }
            else if (execution.Order.OrderAction == OrderAction.Sell && !double.IsNaN(entryFill))
            {
                double exitFill = execution.Order.AverageFillPrice;
                double r = (exitFill - entryFill) / riskPtsAtEntry;
                double pnl = (exitFill - entryFill) * Instrument.MasterInstrument.PointValue * qtyAtEntry;
                Journal("exit_fill", double.NaN, stop, double.NaN, qtyAtEntry,
                    string.Format("fill {0}; R before costs {1:0.00}; P&L before costs {2:0.00}; risk at entry {3:0.00}% of {4:0.00}",
                        exitFill, r, pnl, 100.0 * riskPtsAtEntry * Instrument.MasterInstrument.PointValue * qtyAtEntry / equityAtEntry, equityAtEntry));
                entryFill = double.NaN;
            }
        }

        private void Journal(string evt, double entryLevel, double stopPx, double exitLevel, int qty, string note)
        {
            if (!WriteJournal || State != State.Realtime) return;
            try
            {
                if (!File.Exists(journalPath))
                    File.AppendAllText(journalPath, "time_ny,account,instrument,event,entry_level,stop,exit_level,atr,contracts,closed_equity,note" + Environment.NewLine);
                DateTime nowNy = TimeZoneInfo.ConvertTime(Time[0], NinjaTrader.Core.Globals.GeneralOptions.TimeZoneInfo, ny);
                File.AppendAllText(journalPath, string.Join(",", nowNy.ToString("yyyy-MM-dd HH:mm"), Account.Name, Instrument.FullName, evt,
                    F(entryLevel), F(stopPx), F(exitLevel), F(atr), qty, F(ClosedEquity()), "\"" + note + "\"") + Environment.NewLine);
            }
            catch (Exception ex) { Print("TurtleBreakoutRevelio journal: " + ex.Message); }
        }

        private static string F(double v) { return double.IsNaN(v) ? "" : v.ToString("0.#####"); }

        #region Properties
        [NinjaScriptProperty, Range(2, 400)]
        [Display(Name = "Entry: highest high of last N days", Order = 1, GroupName = "Rules")]
        public int EntryDays { get; set; }

        [NinjaScriptProperty, Range(2, 400)]
        [Display(Name = "Exit: lowest low of last M days", Order = 2, GroupName = "Rules")]
        public int ExitDays { get; set; }

        [NinjaScriptProperty, Range(2, 400)]
        [Display(Name = "ATR length (days)", Order = 3, GroupName = "Rules")]
        public int AtrDays { get; set; }

        [NinjaScriptProperty, Range(0.5, 10)]
        [Display(Name = "Stop: ATR multiple below entry", Order = 4, GroupName = "Rules")]
        public double AtrMultiple { get; set; }

        [NinjaScriptProperty]
        [Display(Name = "Sizing", Order = 1, GroupName = "Sizing")]
        public TurtleSizingMode Sizing { get; set; }

        [NinjaScriptProperty, Range(0.1, 100)]
        [Display(Name = "Risk % of closed equity (PercentOfEquity)", Order = 2, GroupName = "Sizing")]
        public double RiskPercent { get; set; }

        [NinjaScriptProperty, Range(1, 1000)]
        [Display(Name = "Contracts per signal (FixedContracts)", Order = 3, GroupName = "Sizing")]
        public int FixedQuantity { get; set; }

        [NinjaScriptProperty, Range(1, 10000)]
        [Display(Name = "Max contracts (safety cap)", Order = 4, GroupName = "Sizing")]
        public int MaxContracts { get; set; }

        [NinjaScriptProperty]
        [Display(Name = "Closed equity = account cash value", Description = "Use a sim account dedicated to this one strategy, reset to the starting balance.", Order = 5, GroupName = "Sizing")]
        public bool UseAccountCashValue { get; set; }

        [NinjaScriptProperty, Range(100, 100000000)]
        [Display(Name = "Starting capital (if not using account cash)", Order = 6, GroupName = "Sizing")]
        public double StartingCapital { get; set; }

        [NinjaScriptProperty]
        [Display(Name = "Write CSV journal", Order = 1, GroupName = "Journal")]
        public bool WriteJournal { get; set; }
        #endregion
    }
}
