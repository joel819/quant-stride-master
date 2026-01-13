"""
Report Parser
Parse MT5 backtest HTML/XML reports.
"""

import re
from dataclasses import dataclass
from typing import Optional
from bs4 import BeautifulSoup


@dataclass
class ParsedMetrics:
    """Metrics extracted from a backtest report."""
    # Basic info
    symbol: str = ""
    timeframe: str = ""
    start_date: str = ""
    end_date: str = ""
    initial_deposit: float = 0.0
    
    # Trade statistics
    total_trades: int = 0
    short_trades: int = 0
    short_won: int = 0
    long_trades: int = 0
    long_won: int = 0
    
    # Profit/Loss
    total_net_profit: float = 0.0
    gross_profit: float = 0.0
    gross_loss: float = 0.0
    
    # Ratios
    profit_factor: float = 0.0
    expected_payoff: float = 0.0
    recovery_factor: float = 0.0
    sharpe_ratio: float = 0.0
    
    # Drawdown
    balance_drawdown_abs: float = 0.0
    balance_drawdown_max: float = 0.0
    balance_drawdown_max_percent: float = 0.0
    equity_drawdown_abs: float = 0.0
    equity_drawdown_max: float = 0.0
    equity_drawdown_max_percent: float = 0.0
    
    # Consecutive
    max_consecutive_wins: int = 0
    max_consecutive_wins_amount: float = 0.0
    max_consecutive_losses: int = 0
    max_consecutive_losses_amount: float = 0.0
    
    # Averages
    avg_profit_trade: float = 0.0
    avg_loss_trade: float = 0.0
    largest_profit_trade: float = 0.0
    largest_loss_trade: float = 0.0
    
    @property
    def win_rate(self) -> float:
        if self.total_trades == 0:
            return 0.0
        won = self.short_won + self.long_won
        return (won / self.total_trades) * 100


class ReportParser:
    """
    Parse MT5 backtest reports in HTML and XML formats.
    
    Supports:
    - HTML reports from Strategy Tester
    - XML reports from Strategy Tester
    - Optimization result files
    """
    
    # Metric label mappings (English)
    LABEL_MAPPINGS = {
        "Total Net Profit": "total_net_profit",
        "Gross Profit": "gross_profit",
        "Gross Loss": "gross_loss",
        "Profit Factor": "profit_factor",
        "Expected Payoff": "expected_payoff",
        "Recovery Factor": "recovery_factor",
        "Sharpe Ratio": "sharpe_ratio",
        "Total Trades": "total_trades",
        "Short Trades (won %)": "short_trades",
        "Long Trades (won %)": "long_trades",
        "Balance Drawdown Absolute": "balance_drawdown_abs",
        "Balance Drawdown Maximal": "balance_drawdown_max",
        "Equity Drawdown Absolute": "equity_drawdown_abs",
        "Equity Drawdown Maximal": "equity_drawdown_max",
        "Maximal consecutive wins": "max_consecutive_wins",
        "Maximal consecutive losses": "max_consecutive_losses",
        "Average profit trade": "avg_profit_trade",
        "Average loss trade": "avg_loss_trade",
        "Largest profit trade": "largest_profit_trade",
        "Largest loss trade": "largest_loss_trade",
        "Initial Deposit": "initial_deposit",
    }
    
    def __init__(self):
        self.metrics = ParsedMetrics()
    
    def parse_html(self, html_content: str) -> ParsedMetrics:
        """
        Parse HTML backtest report.
        
        Args:
            html_content: Raw HTML content
            
        Returns:
            ParsedMetrics with extracted values
        """
        self.metrics = ParsedMetrics()
        
        try:
            soup = BeautifulSoup(html_content, 'lxml')
        except:
            # Fallback to html.parser
            soup = BeautifulSoup(html_content, 'html.parser')
        
        # Find all tables
        tables = soup.find_all('table')
        
        for table in tables:
            self._parse_table(table)
        
        # Also try to find metrics in plain text
        self._parse_text(soup.get_text())
        
        return self.metrics
    
    def parse_xml(self, xml_content: str) -> ParsedMetrics:
        """
        Parse XML backtest report.
        
        Args:
            xml_content: Raw XML content
            
        Returns:
            ParsedMetrics with extracted values
        """
        self.metrics = ParsedMetrics()
        
        try:
            from lxml import etree
            root = etree.fromstring(xml_content.encode())
            
            # Find result elements
            for elem in root.iter():
                tag = elem.tag.lower()
                text = elem.text
                
                if text is None:
                    continue
                
                try:
                    if 'profit' in tag and 'net' in tag:
                        self.metrics.total_net_profit = self._parse_number(text)
                    elif 'profit' in tag and 'gross' in tag:
                        self.metrics.gross_profit = self._parse_number(text)
                    elif 'loss' in tag and 'gross' in tag:
                        self.metrics.gross_loss = abs(self._parse_number(text))
                    elif tag == 'profitfactor' or 'profit_factor' in tag:
                        self.metrics.profit_factor = self._parse_number(text)
                    elif 'trades' in tag and 'total' in tag:
                        self.metrics.total_trades = int(self._parse_number(text))
                    elif 'drawdown' in tag:
                        self.metrics.equity_drawdown_max = self._parse_number(text)
                    elif 'sharpe' in tag:
                        self.metrics.sharpe_ratio = self._parse_number(text)
                    elif 'recovery' in tag:
                        self.metrics.recovery_factor = self._parse_number(text)
                except (ValueError, AttributeError):
                    pass
        
        except Exception as e:
            # Fallback to regex parsing
            self._parse_text(xml_content)
        
        return self.metrics
    
    def _parse_table(self, table):
        """Parse a table element for metrics."""
        rows = table.find_all('tr')
        
        for row in rows:
            cells = row.find_all(['td', 'th'])
            
            if len(cells) >= 2:
                label = cells[0].get_text(strip=True)
                value = cells[1].get_text(strip=True)
                
                self._set_metric(label, value)
    
    def _parse_text(self, text: str):
        """Parse plain text for metrics using regex."""
        patterns = {
            r"Total Net Profit[\s:]+(-?[\d\s,\.]+)": "total_net_profit",
            r"Gross Profit[\s:]+(-?[\d\s,\.]+)": "gross_profit",
            r"Gross Loss[\s:]+(-?[\d\s,\.]+)": "gross_loss",
            r"Profit Factor[\s:]+(-?[\d\.]+)": "profit_factor",
            r"Expected Payoff[\s:]+(-?[\d\.]+)": "expected_payoff",
            r"Recovery Factor[\s:]+(-?[\d\.]+)": "recovery_factor",
            r"Sharpe Ratio[\s:]+(-?[\d\.]+)": "sharpe_ratio",
            r"Total Trades[\s:]+(\d+)": "total_trades",
            r"Maximal Drawdown[\s:]+(-?[\d\s,\.]+)\s*\(([\d\.]+)%\)": "equity_drawdown_max",
            r"Balance Drawdown[\s:]+(-?[\d\s,\.]+)\s*\(([\d\.]+)%\)": "balance_drawdown_max",
        }
        
        for pattern, metric_name in patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    value = self._parse_number(match.group(1))
                    setattr(self.metrics, metric_name, value)
                    
                    # Handle percentage in drawdown
                    if 'drawdown' in metric_name and match.lastindex >= 2:
                        pct_attr = metric_name + "_percent"
                        if hasattr(self.metrics, pct_attr):
                            setattr(self.metrics, pct_attr, float(match.group(2)))
                except (ValueError, AttributeError):
                    pass
    
    def _set_metric(self, label: str, value: str):
        """Set a metric value based on label."""
        # Clean label
        label = label.strip()
        
        # Find matching attribute
        attr_name = None
        for key, attr in self.LABEL_MAPPINGS.items():
            if key.lower() in label.lower():
                attr_name = attr
                break
        
        if attr_name is None:
            return
        
        try:
            # Parse value
            numeric_value = self._parse_number(value)
            
            # Handle special cases
            if attr_name in ["total_trades", "short_trades", "long_trades",
                            "short_won", "long_won", "max_consecutive_wins",
                            "max_consecutive_losses"]:
                numeric_value = int(numeric_value)
            
            # Handle percentage extraction
            if "%" in value:
                pct_match = re.search(r"([\d\.]+)%", value)
                if pct_match:
                    pct_attr = attr_name + "_percent"
                    if hasattr(self.metrics, pct_attr):
                        setattr(self.metrics, pct_attr, float(pct_match.group(1)))
            
            # Handle trades with won percentage
            if "Trades" in label and "won" in label.lower():
                parts = value.split()
                if len(parts) >= 1:
                    numeric_value = int(self._parse_number(parts[0]))
                
                # Extract won count
                won_match = re.search(r"\((\d+)", value)
                if won_match:
                    won_count = int(won_match.group(1))
                    if "Short" in label:
                        self.metrics.short_won = won_count
                    elif "Long" in label:
                        self.metrics.long_won = won_count
            
            setattr(self.metrics, attr_name, numeric_value)
            
        except (ValueError, AttributeError):
            pass
    
    def _parse_number(self, value: str) -> float:
        """Parse a number from string, handling various formats."""
        if not value:
            return 0.0
        
        # Remove spaces, currency symbols, and normalize
        cleaned = re.sub(r'[^\d\.\-,]', '', value)
        
        # Handle comma as thousands separator or decimal
        if ',' in cleaned and '.' in cleaned:
            # Assume comma is thousands separator
            cleaned = cleaned.replace(',', '')
        elif ',' in cleaned:
            # Comma might be decimal separator
            parts = cleaned.split(',')
            if len(parts) == 2 and len(parts[1]) <= 2:
                cleaned = cleaned.replace(',', '.')
            else:
                cleaned = cleaned.replace(',', '')
        
        return float(cleaned) if cleaned else 0.0
    
    def get_summary(self, metrics: ParsedMetrics = None) -> str:
        """Generate a text summary of parsed metrics."""
        m = metrics or self.metrics
        
        return f"""
Backtest Report Summary
========================
Symbol: {m.symbol} | Timeframe: {m.timeframe}
Period: {m.start_date} to {m.end_date}
Initial Deposit: ${m.initial_deposit:,.2f}

Performance
-----------
Net Profit: ${m.total_net_profit:,.2f}
Profit Factor: {m.profit_factor:.2f}
Win Rate: {m.win_rate:.1f}%

Trade Statistics
----------------
Total Trades: {m.total_trades}
Long: {m.long_trades} (won: {m.long_won})
Short: {m.short_trades} (won: {m.short_won})

Risk Metrics
------------
Max Drawdown: ${m.equity_drawdown_max:,.2f} ({m.equity_drawdown_max_percent:.1f}%)
Recovery Factor: {m.recovery_factor:.2f}
Sharpe Ratio: {m.sharpe_ratio:.2f}

Consecutive Trades
------------------
Max Wins: {m.max_consecutive_wins} (${m.max_consecutive_wins_amount:,.2f})
Max Losses: {m.max_consecutive_losses} (${m.max_consecutive_losses_amount:,.2f})
""".strip()
