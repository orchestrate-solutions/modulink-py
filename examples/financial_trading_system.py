"""
Complex Financial Trading System Example

This example demonstrates ModuLink's capabilities in a sophisticated financial trading environment,
showcasing real-time data processing, risk management, automated trading strategies, and compliance.

Key Features:
- Real-time market data processing with multiple feeds
- Risk management and position sizing algorithms
- Multi-strategy trading execution with backtesting
- Portfolio management with rebalancing
- Compliance and regulatory reporting
- Performance analytics and monitoring
- Trade settlement and clearing processes
"""

import asyncio
import time
import random
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

# Import ModuLink components
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from modulink import ModuLink, Chain
from modulink.middleware import timing_middleware, logging_middleware

# Export all components for testing
__all__ = [
    # Enums
    'OrderType', 'OrderSide', 'OrderStatus',
    # Data Models
    'MarketData', 'Position', 'Order', 'Trade', 'Portfolio', 'RiskMetrics',
    # Services
    'MarketDataService', 'DatabaseService', 'RiskManager', 'TradingStrategyEngine',
    'OrderExecutionEngine', 'PortfolioManager', 'ComplianceManager', 'PerformanceAnalyzer',
    'TradingSystemOrchestrator',
    # Demo Functions
    'demo_single_trade', 'demo_risk_management', 'demo_performance_analytics', 'demo_full_trading_session',
    # Utility Functions for Testing
    'reset_trading_system_state', 'get_trading_system_metrics', 'create_trading_test_context'
]


# Data Models
class OrderType(Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


class OrderSide(Enum):
    BUY = "buy"
    SELL = "sell"


class OrderStatus(Enum):
    PENDING = "pending"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


@dataclass
class MarketData:
    symbol: str
    price: float
    volume: int
    bid: float
    ask: float
    timestamp: datetime
    exchange: str


@dataclass
class Position:
    symbol: str
    quantity: int
    avg_cost: float
    market_value: float
    unrealized_pnl: float
    realized_pnl: float


@dataclass
class Order:
    order_id: str
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: int
    price: Optional[float]
    stop_price: Optional[float]
    status: OrderStatus
    filled_quantity: int = 0
    avg_fill_price: float = 0.0
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class Trade:
    trade_id: str
    order_id: str
    symbol: str
    side: OrderSide
    quantity: int
    price: float
    timestamp: datetime
    commission: float


@dataclass
class Portfolio:
    cash: float
    positions: Dict[str, Position]
    total_value: float
    day_pnl: float
    total_pnl: float


@dataclass
class RiskMetrics:
    var_95: float  # Value at Risk 95%
    max_drawdown: float
    sharpe_ratio: float
    beta: float
    leverage: float
    concentration_risk: float


# Mock Market Data Service
class MarketDataService:
    def __init__(self):
        self.symbols = ["AAPL", "GOOGL", "MSFT", "TSLA", "NVDA", "META", "AMZN"]
        self.prices = {symbol: random.uniform(100, 500) for symbol in self.symbols}
        self.feeds = ["NYSE", "NASDAQ", "BATS", "IEX"]
    
    async def get_market_data(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate real-time market data retrieval"""
        symbols = context.get("symbols", self.symbols)
        market_data = []
        
        for symbol in symbols:
            # Simulate price movement
            current_price = self.prices[symbol]
            change_percent = random.uniform(-0.05, 0.05)  # ±5% max change
            new_price = current_price * (1 + change_percent)
            self.prices[symbol] = new_price
            
            # Create market data
            spread = new_price * 0.001  # 0.1% spread
            data = MarketData(
                symbol=symbol,
                price=new_price,
                volume=random.randint(1000, 100000),
                bid=new_price - spread/2,
                ask=new_price + spread/2,
                timestamp=datetime.now(),
                exchange=random.choice(self.feeds)
            )
            market_data.append(data)
        
        context["market_data"] = market_data
        context["market_timestamp"] = datetime.now()
        
        await asyncio.sleep(0.1)  # Simulate network latency
        return context


# Mock Database Services
class DatabaseService:
    def __init__(self):
        self.orders = {}
        self.trades = {}
        self.positions = {
            "AAPL": Position("AAPL", 100, 150.0, 15000.0, 0.0, 0.0),
            "GOOGL": Position("GOOGL", 50, 2500.0, 125000.0, 0.0, 0.0),
        }
        self.portfolio = Portfolio(
            cash=100000.0,
            positions=self.positions,
            total_value=240000.0,
            day_pnl=0.0,
            total_pnl=0.0
        )
    
    async def save_order(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Save order to database"""
        order = context.get("order")
        if order:
            self.orders[order.order_id] = order
            context["order_saved"] = True
        
        await asyncio.sleep(0.01)  # Simulate DB write
        return context
    
    async def save_trade(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Save trade to database"""
        trade = context.get("trade")
        if trade:
            self.trades[trade.trade_id] = trade
            context["trade_saved"] = True
        
        await asyncio.sleep(0.01)
        return context
    
    async def update_position(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Update position in database"""
        position = context.get("position")
        if position:
            self.positions[position.symbol] = position
            context["position_updated"] = True
        
        await asyncio.sleep(0.01)
        return context


# Risk Management System
class RiskManager:
    def __init__(self):
        self.max_position_size = 1000000  # $1M max position
        self.max_portfolio_leverage = 2.0
        self.max_daily_loss = 50000  # $50K max daily loss
        self.concentration_limit = 0.20  # 20% max concentration per position
    
    async def validate_order(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate order against risk limits"""
        order = context.get("order")
        portfolio = context.get("portfolio")
        
        if not order or not portfolio:
            context["risk_check_passed"] = False
            context["risk_rejection_reason"] = "Missing order or portfolio data"
            return context
        
        # Calculate position value
        market_data = context.get("market_data", {})
        current_price = next((md.price for md in market_data if md.symbol == order.symbol), 0)
        position_value = order.quantity * current_price
        
        # Check position size limit
        if position_value > self.max_position_size:
            context["risk_check_passed"] = False
            context["risk_rejection_reason"] = f"Position size ${position_value:,.2f} exceeds limit ${self.max_position_size:,.2f}"
            return context
        
        # Check concentration limit
        total_portfolio_value = portfolio.total_value
        if position_value / total_portfolio_value > self.concentration_limit:
            context["risk_check_passed"] = False
            context["risk_rejection_reason"] = f"Position concentration {position_value/total_portfolio_value:.2%} exceeds limit {self.concentration_limit:.2%}"
            return context
        
        # Check daily loss limit
        if portfolio.day_pnl < -self.max_daily_loss:
            context["risk_check_passed"] = False
            context["risk_rejection_reason"] = f"Daily loss ${abs(portfolio.day_pnl):,.2f} exceeds limit ${self.max_daily_loss:,.2f}"
            return context
        
        context["risk_check_passed"] = True
        context["position_value"] = position_value
        
        await asyncio.sleep(0.05)  # Simulate risk calculation time
        return context
    
    async def calculate_position_size(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate optimal position size based on risk metrics"""
        signal = context.get("trading_signal")
        portfolio = context.get("portfolio")
        
        if not signal or not portfolio:
            context["position_size"] = 0
            return context
        
        # Kelly Criterion for position sizing
        win_rate = signal.get("confidence", 0.5)
        avg_win = signal.get("expected_return", 0.02)
        avg_loss = 0.01  # Assume 1% avg loss
        
        if win_rate > 0 and avg_win > avg_loss:
            kelly_fraction = (win_rate * avg_win - (1 - win_rate) * avg_loss) / avg_win
            kelly_fraction = max(0, min(kelly_fraction, 0.25))  # Cap at 25%
        else:
            kelly_fraction = 0
        
        # Calculate position size
        available_capital = portfolio.cash * 0.8  # Use 80% of available cash
        position_size = int(available_capital * kelly_fraction / signal.get("entry_price", 1))
        
        context["position_size"] = position_size
        context["kelly_fraction"] = kelly_fraction
        
        await asyncio.sleep(0.02)
        return context


# Trading Strategy Engine
class TradingStrategyEngine:
    def __init__(self):
        self.strategies = ["momentum", "mean_reversion", "arbitrage", "pairs_trading"]
        self.lookback_period = 20
    
    async def generate_signals(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate trading signals based on market data"""
        market_data = context.get("market_data", [])
        
        signals = []
        for data in market_data:
            # Simulate momentum strategy
            momentum_signal = self._momentum_strategy(data)
            
            # Simulate mean reversion strategy
            mean_reversion_signal = self._mean_reversion_strategy(data)
            
            # Combine signals
            combined_signal = {
                "symbol": data.symbol,
                "strategy": "combined",
                "signal_strength": (momentum_signal["strength"] + mean_reversion_signal["strength"]) / 2,
                "direction": momentum_signal["direction"] if momentum_signal["strength"] > mean_reversion_signal["strength"] else mean_reversion_signal["direction"],
                "confidence": random.uniform(0.3, 0.9),
                "entry_price": data.price,
                "expected_return": random.uniform(0.01, 0.05),
                "timestamp": datetime.now()
            }
            
            signals.append(combined_signal)
        
        context["trading_signals"] = signals
        
        await asyncio.sleep(0.1)  # Simulate strategy computation time
        return context
    
    def _momentum_strategy(self, data: MarketData) -> Dict[str, Any]:
        """Simple momentum strategy simulation"""
        # Simulate historical price comparison
        momentum = random.uniform(-0.1, 0.1)  # ±10% momentum
        
        return {
            "strength": abs(momentum),
            "direction": "buy" if momentum > 0 else "sell",
            "momentum_value": momentum
        }
    
    def _mean_reversion_strategy(self, data: MarketData) -> Dict[str, Any]:
        """Simple mean reversion strategy simulation"""
        # Simulate deviation from mean
        deviation = random.uniform(-0.05, 0.05)  # ±5% deviation
        
        return {
            "strength": abs(deviation),
            "direction": "sell" if deviation > 0 else "buy",  # Opposite of momentum
            "deviation_value": deviation
        }


# Order Execution Engine
class OrderExecutionEngine:
    def __init__(self):
        self.execution_venues = ["NYSE", "NASDAQ", "BATS", "IEX", "DARK_POOL"]
        self.fill_rate = 0.95  # 95% fill rate
    
    async def create_order(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Create order from trading signal"""
        signal = context.get("trading_signal")
        position_size = context.get("position_size", 0)
        
        if not signal or position_size <= 0:
            context["order"] = None
            return context
        
        order_id = f"ORD_{int(time.time() * 1000)}"
        
        order = Order(
            order_id=order_id,
            symbol=signal["symbol"],
            side=OrderSide.BUY if signal["direction"] == "buy" else OrderSide.SELL,
            order_type=OrderType.MARKET,
            quantity=position_size,
            price=signal["entry_price"],
            stop_price=None,
            status=OrderStatus.PENDING
        )
        
        context["order"] = order
        
        await asyncio.sleep(0.01)
        return context
    
    async def execute_order(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute order in the market"""
        order = context.get("order")
        market_data = context.get("market_data", [])
        
        if not order:
            return context
        
        # Find current market price
        current_data = next((md for md in market_data if md.symbol == order.symbol), None)
        if not current_data:
            order.status = OrderStatus.REJECTED
            context["execution_error"] = "No market data available"
            return context
        
        # Simulate order execution
        execution_success = random.random() < self.fill_rate
        
        if execution_success:
            # Simulate partial or full fill
            fill_percentage = random.uniform(0.7, 1.0)
            filled_quantity = int(order.quantity * fill_percentage)
            
            # Simulate slippage
            slippage = random.uniform(-0.001, 0.001)  # ±0.1% slippage
            fill_price = current_data.price * (1 + slippage)
            
            order.filled_quantity = filled_quantity
            order.avg_fill_price = fill_price
            order.status = OrderStatus.FILLED if fill_percentage == 1.0 else OrderStatus.PARTIALLY_FILLED
            
            # Create trade record
            trade_id = f"TRD_{int(time.time() * 1000)}"
            trade = Trade(
                trade_id=trade_id,
                order_id=order.order_id,
                symbol=order.symbol,
                side=order.side,
                quantity=filled_quantity,
                price=fill_price,
                timestamp=datetime.now(),
                commission=filled_quantity * fill_price * 0.001  # 0.1% commission
            )
            
            context["trade"] = trade
            context["execution_successful"] = True
        else:
            order.status = OrderStatus.REJECTED
            context["execution_error"] = "Order rejected by market"
            context["execution_successful"] = False
        
        context["order"] = order
        
        await asyncio.sleep(0.05)  # Simulate execution time
        return context


# Portfolio Management System
class PortfolioManager:
    def __init__(self, db_service: DatabaseService):
        self.db_service = db_service
    
    async def update_portfolio(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Update portfolio based on executed trades"""
        trade = context.get("trade")
        portfolio = self.db_service.portfolio
        
        if not trade:
            context["portfolio"] = portfolio
            return context
        
        # Update position
        symbol = trade.symbol
        if symbol in portfolio.positions:
            position = portfolio.positions[symbol]
        else:
            position = Position(symbol, 0, 0.0, 0.0, 0.0, 0.0)
        
        # Calculate new position metrics
        if trade.side == OrderSide.BUY:
            new_quantity = position.quantity + trade.quantity
            new_avg_cost = ((position.quantity * position.avg_cost) + (trade.quantity * trade.price)) / new_quantity
            portfolio.cash -= trade.quantity * trade.price + trade.commission
        else:  # SELL
            new_quantity = position.quantity - trade.quantity
            new_avg_cost = position.avg_cost if new_quantity > 0 else 0.0
            portfolio.cash += trade.quantity * trade.price - trade.commission
            
            # Calculate realized PnL
            realized_pnl = trade.quantity * (trade.price - position.avg_cost)
            position.realized_pnl += realized_pnl
        
        # Update position
        position.quantity = new_quantity
        position.avg_cost = new_avg_cost
        
        # Update market value and unrealized PnL
        market_data = context.get("market_data", [])
        current_price = next((md.price for md in market_data if md.symbol == symbol), trade.price)
        position.market_value = position.quantity * current_price
        position.unrealized_pnl = position.quantity * (current_price - position.avg_cost)
        
        portfolio.positions[symbol] = position
        
        # Recalculate portfolio totals
        portfolio.total_value = portfolio.cash + sum(pos.market_value for pos in portfolio.positions.values())
        portfolio.day_pnl = sum(pos.unrealized_pnl for pos in portfolio.positions.values())
        portfolio.total_pnl = sum(pos.realized_pnl + pos.unrealized_pnl for pos in portfolio.positions.values())
        
        context["portfolio"] = portfolio
        context["position"] = position
        
        await asyncio.sleep(0.02)
        return context
    
    async def calculate_risk_metrics(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate portfolio risk metrics"""
        portfolio = context.get("portfolio")
        
        if not portfolio:
            return context
        
        # Simulate risk calculations
        risk_metrics = RiskMetrics(
            var_95=portfolio.total_value * 0.05,  # 5% VaR
            max_drawdown=random.uniform(0.02, 0.15),  # 2-15% max drawdown
            sharpe_ratio=random.uniform(0.5, 2.0),  # Sharpe ratio
            beta=random.uniform(0.8, 1.2),  # Market beta
            leverage=portfolio.total_value / (portfolio.cash + sum(pos.market_value for pos in portfolio.positions.values())),
            concentration_risk=max(pos.market_value / portfolio.total_value for pos in portfolio.positions.values()) if portfolio.positions else 0
        )
        
        context["risk_metrics"] = risk_metrics
        
        await asyncio.sleep(0.1)  # Simulate complex risk calculations
        return context


# Compliance and Reporting System
class ComplianceManager:
    def __init__(self):
        self.regulations = ["MiFID II", "Dodd-Frank", "Basel III", "CCAR"]
        self.reporting_requirements = ["T+1 Settlement", "Best Execution", "Market Making"]
    
    async def compliance_check(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Perform compliance checks on trades"""
        trade = context.get("trade")
        order = context.get("order")
        
        compliance_results = {
            "trade_reporting_required": True,
            "best_execution_verified": True,
            "market_manipulation_check": "passed",
            "position_limit_check": "passed",
            "client_suitability_check": "passed",
            "timestamp": datetime.now()
        }
        
        # Simulate compliance validation
        if trade and trade.quantity > 10000:  # Large trade
            compliance_results["large_trade_notification"] = True
        
        context["compliance_results"] = compliance_results
        context["compliance_passed"] = True
        
        await asyncio.sleep(0.05)
        return context
    
    async def generate_reports(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate regulatory reports"""
        portfolio = context.get("portfolio")
        trades = context.get("all_trades", [])
        
        reports = {
            "daily_trading_report": {
                "date": datetime.now().date(),
                "total_trades": len(trades),
                "total_volume": sum(t.quantity * t.price for t in trades),
                "total_commission": sum(t.commission for t in trades),
                "net_pnl": portfolio.day_pnl if portfolio else 0
            },
            "position_report": {
                "timestamp": datetime.now(),
                "positions": [
                    {
                        "symbol": symbol,
                        "quantity": pos.quantity,
                        "market_value": pos.market_value,
                        "unrealized_pnl": pos.unrealized_pnl
                    }
                    for symbol, pos in (portfolio.positions.items() if portfolio else [])
                ]
            },
            "risk_report": context.get("risk_metrics", {}).__dict__ if context.get("risk_metrics") else {}
        }
        
        context["regulatory_reports"] = reports
        
        await asyncio.sleep(0.1)
        return context


# Performance Analytics System
class PerformanceAnalyzer:
    def __init__(self):
        self.benchmarks = ["SPY", "QQQ", "IWM"]
    
    async def calculate_performance(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate detailed performance analytics"""
        portfolio = context.get("portfolio")
        trades = context.get("all_trades", [])
        
        if not portfolio:
            return context
        
        # Calculate performance metrics
        total_return = portfolio.total_pnl / (portfolio.total_value - portfolio.total_pnl)
        win_trades = [t for t in trades if self._is_winning_trade(t, portfolio)]
        lose_trades = [t for t in trades if not self._is_winning_trade(t, portfolio)]
        
        performance_metrics = {
            "total_return": total_return,
            "total_trades": len(trades),
            "winning_trades": len(win_trades),
            "losing_trades": len(lose_trades),
            "win_rate": len(win_trades) / len(trades) if trades else 0,
            "avg_win": sum(self._calculate_trade_pnl(t, portfolio) for t in win_trades) / len(win_trades) if win_trades else 0,
            "avg_loss": sum(self._calculate_trade_pnl(t, portfolio) for t in lose_trades) / len(lose_trades) if lose_trades else 0,
            "profit_factor": abs(sum(self._calculate_trade_pnl(t, portfolio) for t in win_trades) / 
                               sum(self._calculate_trade_pnl(t, portfolio) for t in lose_trades)) if lose_trades else float('inf'),
            "max_consecutive_wins": self._calculate_max_consecutive(win_trades),
            "max_consecutive_losses": self._calculate_max_consecutive(lose_trades)
        }
        
        context["performance_metrics"] = performance_metrics
        
        await asyncio.sleep(0.1)
        return context
    
    def _is_winning_trade(self, trade: Trade, portfolio: Portfolio) -> bool:
        """Determine if a trade was profitable"""
        # Simplified logic - in reality would track position cost basis
        return random.choice([True, False])  # Random for simulation
    
    def _calculate_trade_pnl(self, trade: Trade, portfolio: Portfolio) -> float:
        """Calculate P&L for a trade"""
        # Simplified calculation
        return random.uniform(-100, 200)  # Random P&L for simulation
    
    def _calculate_max_consecutive(self, trades: List[Trade]) -> int:
        """Calculate maximum consecutive wins/losses"""
        return min(len(trades), 5)  # Simplified for simulation


# Main Trading System Orchestrator
class TradingSystemOrchestrator:
    def __init__(self):
        # Initialize all components
        self.market_data_service = MarketDataService()
        self.db_service = DatabaseService()
        self.risk_manager = RiskManager()
        self.strategy_engine = TradingStrategyEngine()
        self.execution_engine = OrderExecutionEngine()
        self.portfolio_manager = PortfolioManager(self.db_service)
        self.compliance_manager = ComplianceManager()
        self.performance_analyzer = PerformanceAnalyzer()
        
        # Initialize ModuLink with middleware
        self.modulink = ModuLink()
        self.modulink.use(timing_middleware())
        self.modulink.use(logging_middleware())
        
        # Track all trades for reporting
        self.all_trades = []
        
        self._setup_chains()
    
    def _setup_chains(self):
        """Setup all trading system chains"""
        
        # Main trading chain
        self.main_trading_chain = Chain([
            self.market_data_service.get_market_data,
            self.strategy_engine.generate_signals,
            self._process_signals,
            self.portfolio_manager.calculate_risk_metrics,
            self.compliance_manager.generate_reports,
            self.performance_analyzer.calculate_performance
        ])
        
        # Signal processing chain (runs for each signal)
        self.signal_processing_chain = Chain([
            self._prepare_signal_context,
            self.risk_manager.calculate_position_size,
            self.execution_engine.create_order,
            self.risk_manager.validate_order,
            self._execute_if_approved,
            self.portfolio_manager.update_portfolio,
            self.compliance_manager.compliance_check,
            self.db_service.save_order,
            self.db_service.save_trade,
            self.db_service.update_position
        ])
    
    async def _process_signals(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Process all trading signals"""
        signals = context.get("trading_signals", [])
        portfolio = self.db_service.portfolio
        context["portfolio"] = portfolio
        
        executed_trades = []
        
        for signal in signals:
            # Create individual context for each signal
            signal_context = {
                "trading_signal": signal,
                "portfolio": portfolio,
                "market_data": context.get("market_data", [])
            }
            
            # Process signal through the signal processing chain
            try:
                result = await self.modulink.execute(self.signal_processing_chain, signal_context)
                
                if result.get("trade") and result.get("execution_successful"):
                    executed_trades.append(result["trade"])
                    self.all_trades.append(result["trade"])
                    
                    # Update portfolio reference
                    portfolio = result.get("portfolio", portfolio)
                    
            except Exception as e:
                print(f"Error processing signal for {signal['symbol']}: {e}")
        
        context["executed_trades"] = executed_trades
        context["all_trades"] = self.all_trades
        context["portfolio"] = portfolio
        
        return context
    
    async def _prepare_signal_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare context for signal processing"""
        # Ensure we have the latest portfolio and market data
        return context
    
    async def _execute_if_approved(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute order only if risk checks passed"""
        if context.get("risk_check_passed", False):
            return await self.execution_engine.execute_order(context)
        else:
            context["execution_successful"] = False
            context["execution_error"] = context.get("risk_rejection_reason", "Risk check failed")
            return context
    
    async def run_trading_session(self, duration_minutes: int = 60, symbols: List[str] = None) -> Dict[str, Any]:
        """Run a complete trading session"""
        print(f"Starting trading session for {duration_minutes} minutes...")
        
        session_context = {
            "symbols": symbols or self.market_data_service.symbols,
            "session_start": datetime.now(),
            "session_duration": duration_minutes
        }
        
        session_results = []
        start_time = time.time()
        end_time = start_time + (duration_minutes * 60)
        
        cycle_count = 0
        while time.time() < end_time:
            cycle_count += 1
            print(f"\n--- Trading Cycle {cycle_count} ---")
            
            try:
                # Execute main trading chain
                result = await self.modulink.execute(self.main_trading_chain, session_context.copy())
                session_results.append(result)
                
                # Print cycle summary
                self._print_cycle_summary(result, cycle_count)
                
                # Wait before next cycle
                await asyncio.sleep(10)  # 10-second cycles
                
            except Exception as e:
                print(f"Error in trading cycle {cycle_count}: {e}")
                await asyncio.sleep(5)
        
        # Generate final session report
        final_report = self._generate_session_report(session_results)
        print("\n" + "="*50)
        print("TRADING SESSION COMPLETE")
        print("="*50)
        self._print_session_summary(final_report)
        
        return final_report
    
    def _print_cycle_summary(self, result: Dict[str, Any], cycle: int):
        """Print summary of trading cycle"""
        executed_trades = result.get("executed_trades", [])
        portfolio = result.get("portfolio")
        performance = result.get("performance_metrics", {})
        
        print(f"Cycle {cycle} Summary:")
        print(f"  Trades Executed: {len(executed_trades)}")
        if executed_trades:
            print(f"  Trade Symbols: {[t.symbol for t in executed_trades]}")
        
        if portfolio:
            print(f"  Portfolio Value: ${portfolio.total_value:,.2f}")
            print(f"  Day P&L: ${portfolio.day_pnl:,.2f}")
            print(f"  Cash: ${portfolio.cash:,.2f}")
        
        if performance:
            print(f"  Total Trades: {performance.get('total_trades', 0)}")
            print(f"  Win Rate: {performance.get('win_rate', 0):.1%}")
    
    def _generate_session_report(self, session_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate comprehensive session report"""
        if not session_results:
            return {}
        
        final_result = session_results[-1]
        
        total_trades = sum(len(r.get("executed_trades", [])) for r in session_results)
        total_cycles = len(session_results)
        
        return {
            "session_summary": {
                "total_cycles": total_cycles,
                "total_trades": total_trades,
                "avg_trades_per_cycle": total_trades / total_cycles if total_cycles > 0 else 0
            },
            "final_portfolio": final_result.get("portfolio"),
            "final_performance": final_result.get("performance_metrics", {}),
            "final_risk_metrics": final_result.get("risk_metrics"),
            "regulatory_reports": final_result.get("regulatory_reports", {}),
            "all_trades": self.all_trades
        }
    
    def _print_session_summary(self, report: Dict[str, Any]):
        """Print final session summary"""
        session = report.get("session_summary", {})
        portfolio = report.get("final_portfolio")
        performance = report.get("final_performance", {})
        risk = report.get("final_risk_metrics")
        
        print(f"Session Summary:")
        print(f"  Total Cycles: {session.get('total_cycles', 0)}")
        print(f"  Total Trades: {session.get('total_trades', 0)}")
        print(f"  Avg Trades/Cycle: {session.get('avg_trades_per_cycle', 0):.1f}")
        
        if portfolio:
            print(f"\nFinal Portfolio:")
            print(f"  Total Value: ${portfolio.total_value:,.2f}")
            print(f"  Cash: ${portfolio.cash:,.2f}")
            print(f"  Total P&L: ${portfolio.total_pnl:,.2f}")
            print(f"  Positions: {len(portfolio.positions)}")
        
        if performance:
            print(f"\nPerformance Metrics:")
            print(f"  Total Return: {performance.get('total_return', 0):.2%}")
            print(f"  Win Rate: {performance.get('win_rate', 0):.1%}")
            print(f"  Profit Factor: {performance.get('profit_factor', 0):.2f}")
        
        if risk:
            print(f"\nRisk Metrics:")
            print(f"  VaR (95%): ${risk.var_95:,.2f}")
            print(f"  Sharpe Ratio: {risk.sharpe_ratio:.2f}")
            print(f"  Max Drawdown: {risk.max_drawdown:.2%}")


# Utility Functions for Testing
def reset_trading_system_state():
    """Reset all system state for clean testing"""
    return {
        "orders": {},
        "trades": {},
        "positions": {
            "AAPL": Position("AAPL", 100, 150.0, 15000.0, 0.0, 0.0),
            "GOOGL": Position("GOOGL", 50, 2500.0, 125000.0, 0.0, 0.0),
        },
        "portfolio": Portfolio(
            cash=100000.0,
            positions={
                "AAPL": Position("AAPL", 100, 150.0, 15000.0, 0.0, 0.0),
                "GOOGL": Position("GOOGL", 50, 2500.0, 125000.0, 0.0, 0.0),
            },
            total_value=240000.0,
            day_pnl=0.0,
            total_pnl=0.0
        ),
        "system_status": "ready",
        "timestamp": datetime.now()
    }


def get_trading_system_metrics(orchestrator: 'TradingSystemOrchestrator') -> Dict[str, Any]:
    """Get comprehensive trading system metrics"""
    portfolio = orchestrator.db_service.portfolio
    return {
        "portfolio_value": portfolio.total_value,
        "cash_balance": portfolio.cash,
        "active_positions": len(portfolio.positions),
        "day_pnl": portfolio.day_pnl,
        "total_pnl": portfolio.total_pnl,
        "total_orders": len(orchestrator.db_service.orders),
        "total_trades": len(orchestrator.all_trades),
        "system_uptime": datetime.now(),
        "risk_limits": {
            "max_position_size": orchestrator.risk_manager.max_position_size,
            "max_daily_loss": orchestrator.risk_manager.max_daily_loss,
            "concentration_limit": orchestrator.risk_manager.concentration_limit
        },
        "compliance_status": "active",
        "performance_data": {
            "total_volume": sum(t.quantity * t.price for t in orchestrator.all_trades),
            "total_commissions": sum(t.commission for t in orchestrator.all_trades)
        }
    }


def create_trading_test_context(symbols: List[str] = None, portfolio_cash: float = 100000.0) -> Dict[str, Any]:
    """Create standardized test context for trading operations"""
    if symbols is None:
        symbols = ["AAPL", "GOOGL", "MSFT"]
    
    return {
        "symbols": symbols,
        "test_mode": True,
        "session_start": datetime.now(),
        "portfolio": Portfolio(
            cash=portfolio_cash,
            positions={},
            total_value=portfolio_cash,
            day_pnl=0.0,
            total_pnl=0.0
        ),
        "market_data": [
            MarketData(symbol, 100.0 + random.uniform(-10, 10), 1000, 99.5, 100.5, datetime.now(), "NYSE")
            for symbol in symbols
        ],
        "trading_signals": [],
        "risk_parameters": {
            "max_position_size": 50000.0,
            "concentration_limit": 0.15,
            "max_daily_loss": 10000.0
        }
    }


# Demo Functions
async def demo_single_trade():
    """Demonstrate a single trade execution"""
    print("="*50)
    print("DEMO: Single Trade Execution")
    print("="*50)
    
    orchestrator = TradingSystemOrchestrator()
    
    # Create a simple context for single trade
    context = {
        "symbols": ["AAPL"],
        "demo_mode": True
    }
    
    try:
        result = await orchestrator.modulink.execute(orchestrator.main_trading_chain, context)
        
        print("\nTrade Execution Results:")
        executed_trades = result.get("executed_trades", [])
        print(f"Trades executed: {len(executed_trades)}")
        
        for trade in executed_trades:
            print(f"  {trade.symbol}: {trade.side.value} {trade.quantity} @ ${trade.price:.2f}")
        
        portfolio = result.get("portfolio")
        if portfolio:
            print(f"\nPortfolio Status:")
            print(f"  Total Value: ${portfolio.total_value:,.2f}")
            print(f"  Cash: ${portfolio.cash:,.2f}")
            print(f"  Day P&L: ${portfolio.day_pnl:,.2f}")
        
    except Exception as e:
        print(f"Error in demo: {e}")


async def demo_risk_management():
    """Demonstrate risk management features"""
    print("="*50)
    print("DEMO: Risk Management System")
    print("="*50)
    
    orchestrator = TradingSystemOrchestrator()
    
    # Test various risk scenarios
    test_scenarios = [
        {"name": "Normal Trade", "quantity": 100, "price": 150.0},
        {"name": "Large Position", "quantity": 10000, "price": 150.0},
        {"name": "High Concentration", "quantity": 5000, "price": 500.0},
    ]
    
    for scenario in test_scenarios:
        print(f"\nTesting: {scenario['name']}")
        
        # Create test order
        order = Order(
            order_id=f"TEST_{int(time.time())}",
            symbol="AAPL",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=scenario["quantity"],
            price=scenario["price"],
            stop_price=None,
            status=OrderStatus.PENDING
        )
        
        context = {
            "order": order,
            "portfolio": orchestrator.db_service.portfolio,
            "market_data": [MarketData("AAPL", scenario["price"], 1000, scenario["price"]-0.5, scenario["price"]+0.5, datetime.now(), "NYSE")]
        }
        
        try:
            result = await orchestrator.risk_manager.validate_order(context)
            passed = result.get("risk_check_passed", False)
            reason = result.get("risk_rejection_reason", "")
            
            print(f"  Risk Check: {'PASSED' if passed else 'FAILED'}")
            if not passed:
                print(f"  Reason: {reason}")
                
        except Exception as e:
            print(f"  Error: {e}")


async def demo_full_trading_session():
    """Demonstrate a full trading session"""
    print("="*50)
    print("DEMO: Full Trading Session")
    print("="*50)
    
    orchestrator = TradingSystemOrchestrator()
    
    # Run short trading session
    symbols = ["AAPL", "GOOGL", "MSFT"]
    duration = 2  # 2 minutes for demo
    
    try:
        final_report = await orchestrator.run_trading_session(duration, symbols)
        
        print("\nDemo completed successfully!")
        print(f"Check the detailed logs above for complete trading activity.")
        
    except Exception as e:
        print(f"Error in trading session: {e}")


async def demo_performance_analytics():
    """Demonstrate performance analytics"""
    print("="*50)
    print("DEMO: Performance Analytics")
    print("="*50)
    
    orchestrator = TradingSystemOrchestrator()
    
    # Generate some sample trades
    sample_trades = [
        Trade(f"T{i}", f"O{i}", "AAPL", OrderSide.BUY if i % 2 == 0 else OrderSide.SELL, 
              100, 150.0 + random.uniform(-5, 5), datetime.now(), 1.5)
        for i in range(10)
    ]
    orchestrator.all_trades = sample_trades
    
    context = {
        "portfolio": orchestrator.db_service.portfolio,
        "all_trades": sample_trades
    }
    
    try:
        result = await orchestrator.performance_analyzer.calculate_performance(context)
        
        performance = result.get("performance_metrics", {})
        print("\nPerformance Analytics:")
        print(f"  Total Trades: {performance.get('total_trades', 0)}")
        print(f"  Win Rate: {performance.get('win_rate', 0):.1%}")
        print(f"  Profit Factor: {performance.get('profit_factor', 0):.2f}")
        print(f"  Average Win: ${performance.get('avg_win', 0):.2f}")
        print(f"  Average Loss: ${performance.get('avg_loss', 0):.2f}")
        
    except Exception as e:
        print(f"Error in performance demo: {e}")


# Main execution
async def main():
    """Run all financial trading system demos"""
    print("FINANCIAL TRADING SYSTEM - ModuLink Demonstration")
    print("This example showcases sophisticated trading workflows with real-time processing,")
    print("risk management, compliance, and performance analytics.\n")
    
    demos = [
        ("Single Trade Execution", demo_single_trade),
        ("Risk Management System", demo_risk_management),
        ("Performance Analytics", demo_performance_analytics),
        ("Full Trading Session", demo_full_trading_session),
    ]
    
    for demo_name, demo_func in demos:
        try:
            await demo_func()
            print("\n" + "-"*50 + "\n")
            await asyncio.sleep(1)  # Brief pause between demos
        except Exception as e:
            print(f"Error in {demo_name}: {e}")
            print("-"*50 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
