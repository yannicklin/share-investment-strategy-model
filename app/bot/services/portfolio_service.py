"""
AI Trading Bot System - Portfolio Resource Management Service

Purpose: Track portfolio holdings, validate resource availability, and manage transactions.

Author: Yannick
Copyright (c) 2026 Yannick
"""

from datetime import datetime, date
from typing import Dict, Optional, Tuple
from app.bot.shared.models import Portfolio, Position, Transaction, db
import logging

logger = logging.getLogger(__name__)


class PortfolioService:
    """
    Manages portfolio holdings and resource availability for trading bot.
    
    Ensures:
    - Sufficient cash before BUY signals
    - Sufficient stock holdings before SELL signals
    - Complete transaction audit trail
    - Market isolation (ASX/USA/TWN independent)
    """
    
    def __init__(self, market: str):
        """
        Initialize portfolio service for specific market.
        
        Args:
            market: Market code ('ASX', 'USA', 'TWN')
        """
        self.market = market
    
    def get_or_create_portfolio(self, initial_cash: float = 0.0) -> Portfolio:
        """
        Get existing portfolio or create new one with initial cash.
        
        Args:
            initial_cash: Starting capital (only used if creating new portfolio)
        
        Returns:
            Portfolio instance for this market
        """
        portfolio = Portfolio.for_market(self.market).first()
        
        if portfolio is None:
            logger.info(f"{self.market}: Creating new portfolio with ${initial_cash:.2f}")
            portfolio = Portfolio(market=self.market, cash=initial_cash)
            db.session.add(portfolio)
            db.session.commit()
        
        return portfolio
    
    def get_cash(self) -> float:
        """
        Get current cash balance.
        
        Returns:
            Cash amount in portfolio
        """
        portfolio = self.get_or_create_portfolio()
        return portfolio.cash
    
    def get_position(self, ticker: str) -> Optional[Position]:
        """
        Get current position for a ticker.
        
        Args:
            ticker: Stock symbol (without suffix, e.g., 'BHP')
        
        Returns:
            Position instance or None if no position
        """
        return Position.for_market(self.market).filter_by(ticker=ticker).first()
    
    def get_all_positions(self) -> Dict[str, float]:
        """
        Get all current positions as a dictionary.
        
        Returns:
            {ticker: quantity} mapping
        """
        positions = Position.for_market(self.market).all()
        return {pos.ticker: pos.quantity for pos in positions}
    
    def can_buy(self, ticker: str, price: float, quantity: int = 1) -> Tuple[bool, str]:
        """
        Check if portfolio has sufficient cash to buy stock.
        
        Args:
            ticker: Stock symbol
            price: Current price per unit
            quantity: Number of units to buy (default: 1)
        
        Returns:
            (can_trade: bool, reason: str)
        
        Examples:
            >>> service = PortfolioService('ASX')
            >>> service.can_buy('BHP', 45.50, 100)
            (True, '')  # If cash >= $4,550
            >>> service.can_buy('BHP', 45.50, 1000)
            (False, 'Insufficient cash: $10,000 < required $45,500')
        """
        portfolio = self.get_or_create_portfolio()
        cash = portfolio.cash
        
        # Calculate total cost (price * quantity)
        # Note: Commission fees handled separately in transaction
        total_cost = price * quantity
        
        if cash < total_cost:
            return False, f"Insufficient cash: ${cash:.2f} < required ${total_cost:.2f}"
        
        return True, ""
    
    def can_sell(self, ticker: str, quantity: int = 1) -> Tuple[bool, str]:
        """
        Check if portfolio has sufficient stock holdings to sell.
        
        Args:
            ticker: Stock symbol
            quantity: Number of units to sell (default: 1)
        
        Returns:
            (can_trade: bool, reason: str)
        
        Examples:
            >>> service = PortfolioService('ASX')
            >>> service.can_sell('BHP', 50)
            (True, '')  # If position >= 50 units
            >>> service.can_sell('BHP', 200)
            (False, 'Insufficient holdings: 100 < required 200')
        """
        position = self.get_position(ticker)
        
        if position is None or position.quantity == 0:
            return False, f"No position in {ticker}"
        
        if position.quantity < quantity:
            return False, f"Insufficient holdings: {position.quantity} < required {quantity}"
        
        return True, ""
    
    def execute_buy(
        self,
        ticker: str,
        price: float,
        quantity: int,
        commission: float = 0.0,
        strategy: str = "",
        confidence: float = 0.0,
        trade_date: Optional[date] = None
    ) -> Transaction:
        """
        Execute BUY transaction and update portfolio.
        
        Args:
            ticker: Stock symbol
            price: Price per unit
            quantity: Number of units to buy
            commission: Transaction fee
            strategy: Strategy name (e.g., 'consensus-30d')
            confidence: Signal confidence (0-1)
            trade_date: Transaction date (defaults to today)
        
        Returns:
            Transaction record
        
        Raises:
            ValueError: If insufficient cash
        """
        if trade_date is None:
            trade_date = date.today()
        
        # Validate cash availability
        can_trade, reason = self.can_buy(ticker, price, quantity)
        if not can_trade:
            raise ValueError(f"Cannot execute BUY: {reason}")
        
        # Get current state
        portfolio = self.get_or_create_portfolio()
        cash_before = portfolio.cash
        
        # Calculate costs
        total_cost = (price * quantity) + commission
        cash_after = cash_before - total_cost
        
        # Update cash
        portfolio.cash = cash_after
        
        # Update or create position
        position = self.get_position(ticker)
        if position is None:
            position = Position(
                market=self.market,
                ticker=ticker,
                quantity=quantity,
                avg_price=price
            )
            db.session.add(position)
        else:
            # Update average price
            total_cost_before = position.avg_price * position.quantity
            new_cost = price * quantity
            new_total_quantity = position.quantity + quantity
            position.avg_price = (total_cost_before + new_cost) / new_total_quantity
            position.quantity = new_total_quantity
        
        # Create transaction record
        transaction = Transaction(
            market=self.market,
            date=trade_date,
            ticker=ticker,
            action='BUY',
            quantity=quantity,
            price=price,
            commission=commission,
            cash_before=cash_before,
            cash_after=cash_after,
            strategy=strategy,
            confidence=confidence,
            notes=f"Bought {quantity} units @ ${price:.2f}"
        )
        db.session.add(transaction)
        db.session.commit()
        
        logger.info(f"{self.market}: BUY {quantity} {ticker} @ ${price:.2f} (cash: ${cash_after:.2f})")
        
        return transaction
    
    def execute_sell(
        self,
        ticker: str,
        price: float,
        quantity: int,
        commission: float = 0.0,
        strategy: str = "",
        confidence: float = 0.0,
        trade_date: Optional[date] = None
    ) -> Transaction:
        """
        Execute SELL transaction and update portfolio.
        
        Args:
            ticker: Stock symbol
            price: Price per unit
            quantity: Number of units to sell
            commission: Transaction fee
            strategy: Strategy name
            confidence: Signal confidence (0-1)
            trade_date: Transaction date (defaults to today)
        
        Returns:
            Transaction record
        
        Raises:
            ValueError: If insufficient holdings
        """
        if trade_date is None:
            trade_date = date.today()
        
        # Validate position availability
        can_trade, reason = self.can_sell(ticker, quantity)
        if not can_trade:
            raise ValueError(f"Cannot execute SELL: {reason}")
        
        # Get current state
        portfolio = self.get_or_create_portfolio()
        position = self.get_position(ticker)
        cash_before = portfolio.cash
        
        # Calculate proceeds
        total_proceeds = (price * quantity) - commission
        cash_after = cash_before + total_proceeds
        
        # Update cash
        portfolio.cash = cash_after
        
        # Update position
        position.quantity -= quantity
        if position.quantity == 0:
            # Remove position if fully sold
            db.session.delete(position)
        
        # Create transaction record
        transaction = Transaction(
            market=self.market,
            date=trade_date,
            ticker=ticker,
            action='SELL',
            quantity=quantity,
            price=price,
            commission=commission,
            cash_before=cash_before,
            cash_after=cash_after,
            strategy=strategy,
            confidence=confidence,
            notes=f"Sold {quantity} units @ ${price:.2f}"
        )
        db.session.add(transaction)
        db.session.commit()
        
        logger.info(f"{self.market}: SELL {quantity} {ticker} @ ${price:.2f} (cash: ${cash_after:.2f})")
        
        return transaction
    
    def get_portfolio_summary(self) -> Dict:
        """
        Get complete portfolio summary.
        
        Returns:
            {
                'cash': float,
                'positions': {ticker: {'quantity': float, 'avg_price': float}},
                'total_value': float (cash + estimated position value)
            }
        """
        portfolio = self.get_or_create_portfolio()
        positions = Position.for_market(self.market).all()
        
        position_dict = {}
        position_value = 0.0
        
        for pos in positions:
            position_dict[pos.ticker] = {
                'quantity': pos.quantity,
                'avg_price': pos.avg_price
            }
            # Estimate value at average purchase price
            position_value += pos.quantity * (pos.avg_price or 0)
        
        return {
            'cash': portfolio.cash,
            'positions': position_dict,
            'total_value': portfolio.cash + position_value
        }
