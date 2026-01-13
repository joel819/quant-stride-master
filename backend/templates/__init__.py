"""
QuantStride MQL5 Templates
Modular template generators for EA components.
"""

from .base_ea import BaseEATemplate
from .indicators import IndicatorTemplates
from .risk_management import RiskManagementTemplates
from .trend_filters import TrendFilterTemplates
from .order_management import OrderManagementTemplates
from .filters import FilterTemplates
from .advanced_ea_generator import AdvancedEAGenerator, EAConfiguration
from .custom_ea_generator import CustomEAGenerator, EASettings
from .custom_ea_generator import (
    create_xauusd_scalper,
    create_eurusd_scalper,
    create_us30_trader,
    create_volatility_75_trader,
)
from .blocks import EntryBlocks, ExitBlocks, ProtectionBlocks

__all__ = [
    "BaseEATemplate",
    "IndicatorTemplates",
    "RiskManagementTemplates",
    "TrendFilterTemplates",
    "OrderManagementTemplates",
    "FilterTemplates",
    "AdvancedEAGenerator",
    "EAConfiguration",
    "CustomEAGenerator",
    "EASettings",
    "create_xauusd_scalper",
    "create_eurusd_scalper",
    "create_us30_trader",
    "create_volatility_75_trader",
    "EntryBlocks",
    "ExitBlocks",
    "ProtectionBlocks",
]
