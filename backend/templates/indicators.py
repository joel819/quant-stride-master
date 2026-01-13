"""
Indicator Templates
MQL5 template blocks for various indicators.
"""


class IndicatorTemplates:
    """
    Generates MQL5 code blocks for technical indicators.
    
    Supports: EMA, SMA, RSI, MACD, ATR, BB, Stochastic, ADX
    """
    
    @staticmethod
    def generate_handle_declaration(
        indicator_type: str,
        handle_name: str,
        htf: bool = False
    ) -> str:
        """Generate indicator handle declaration."""
        suffix = "_htf" if htf else ""
        return f"int {handle_name}{suffix};"
    
    @staticmethod
    def generate_ema_init(
        handle_name: str,
        period: int,
        timeframe: str = "PERIOD_CURRENT",
        htf: bool = False
    ) -> str:
        """Generate EMA initialization code."""
        suffix = "_htf" if htf else ""
        tf = "PERIOD_H1" if htf else timeframe
        return f'''   {handle_name}{suffix} = iMA(_Symbol, {tf}, {period}, 0, MODE_EMA, PRICE_CLOSE);
   if({handle_name}{suffix} == INVALID_HANDLE)
   {{
      Print("Failed to create EMA indicator handle");
      return(INIT_FAILED);
   }}'''

    @staticmethod
    def generate_sma_init(
        handle_name: str,
        period: int,
        timeframe: str = "PERIOD_CURRENT",
        htf: bool = False
    ) -> str:
        """Generate SMA initialization code."""
        suffix = "_htf" if htf else ""
        tf = "PERIOD_H1" if htf else timeframe
        return f'''   {handle_name}{suffix} = iMA(_Symbol, {tf}, {period}, 0, MODE_SMA, PRICE_CLOSE);
   if({handle_name}{suffix} == INVALID_HANDLE)
   {{
      Print("Failed to create SMA indicator handle");
      return(INIT_FAILED);
   }}'''

    @staticmethod
    def generate_rsi_init(
        handle_name: str,
        period: int,
        timeframe: str = "PERIOD_CURRENT",
        htf: bool = False
    ) -> str:
        """Generate RSI initialization code."""
        suffix = "_htf" if htf else ""
        tf = "PERIOD_H1" if htf else timeframe
        return f'''   {handle_name}{suffix} = iRSI(_Symbol, {tf}, {period}, PRICE_CLOSE);
   if({handle_name}{suffix} == INVALID_HANDLE)
   {{
      Print("Failed to create RSI indicator handle");
      return(INIT_FAILED);
   }}'''

    @staticmethod
    def generate_macd_init(
        handle_name: str,
        fast: int = 12,
        slow: int = 26,
        signal: int = 9,
        timeframe: str = "PERIOD_CURRENT"
    ) -> str:
        """Generate MACD initialization code."""
        return f'''   {handle_name} = iMACD(_Symbol, {timeframe}, {fast}, {slow}, {signal}, PRICE_CLOSE);
   if({handle_name} == INVALID_HANDLE)
   {{
      Print("Failed to create MACD indicator handle");
      return(INIT_FAILED);
   }}'''

    @staticmethod
    def generate_atr_init(
        handle_name: str,
        period: int = 14,
        timeframe: str = "PERIOD_CURRENT"
    ) -> str:
        """Generate ATR initialization code."""
        return f'''   {handle_name} = iATR(_Symbol, {timeframe}, {period});
   if({handle_name} == INVALID_HANDLE)
   {{
      Print("Failed to create ATR indicator handle");
      return(INIT_FAILED);
   }}'''

    @staticmethod
    def generate_bb_init(
        handle_name: str,
        period: int = 20,
        deviation: float = 2.0,
        timeframe: str = "PERIOD_CURRENT"
    ) -> str:
        """Generate Bollinger Bands initialization code."""
        return f'''   {handle_name} = iBands(_Symbol, {timeframe}, {period}, 0, {deviation}, PRICE_CLOSE);
   if({handle_name} == INVALID_HANDLE)
   {{
      Print("Failed to create Bollinger Bands indicator handle");
      return(INIT_FAILED);
   }}'''

    @staticmethod
    def generate_stochastic_init(
        handle_name: str,
        k_period: int = 5,
        d_period: int = 3,
        slowing: int = 3,
        timeframe: str = "PERIOD_CURRENT"
    ) -> str:
        """Generate Stochastic initialization code."""
        return f'''   {handle_name} = iStochastic(_Symbol, {timeframe}, {k_period}, {d_period}, {slowing}, MODE_SMA, STO_LOWHIGH);
   if({handle_name} == INVALID_HANDLE)
   {{
      Print("Failed to create Stochastic indicator handle");
      return(INIT_FAILED);
   }}'''

    @staticmethod
    def generate_adx_init(
        handle_name: str,
        period: int = 14,
        timeframe: str = "PERIOD_CURRENT"
    ) -> str:
        """Generate ADX initialization code."""
        return f'''   {handle_name} = iADX(_Symbol, {timeframe}, {period});
   if({handle_name} == INVALID_HANDLE)
   {{
      Print("Failed to create ADX indicator handle");
      return(INIT_FAILED);
   }}'''

    @staticmethod
    def generate_buffer_read(
        handle_name: str,
        buffer_name: str,
        buffer_index: int = 0,
        count: int = 5
    ) -> str:
        """Generate code to read indicator buffer into array."""
        return f'''   double {buffer_name}[];
   ArraySetAsSeries({buffer_name}, true);
   if(CopyBuffer({handle_name}, {buffer_index}, 0, {count}, {buffer_name}) < {count})
   {{
      if(EnableLogging) Print("Failed to copy {buffer_name} buffer");
      return;
   }}'''

    @staticmethod
    def generate_ema_read(handle_name: str, buffer_name: str) -> str:
        """Generate EMA buffer read code."""
        return IndicatorTemplates.generate_buffer_read(handle_name, buffer_name, 0, 5)

    @staticmethod
    def generate_rsi_read(handle_name: str, buffer_name: str) -> str:
        """Generate RSI buffer read code."""
        return IndicatorTemplates.generate_buffer_read(handle_name, buffer_name, 0, 5)

    @staticmethod
    def generate_macd_read(handle_name: str) -> str:
        """Generate MACD buffer read code (main + signal)."""
        return f'''   double macd_main[], macd_signal[];
   ArraySetAsSeries(macd_main, true);
   ArraySetAsSeries(macd_signal, true);
   if(CopyBuffer({handle_name}, 0, 0, 5, macd_main) < 5) return;
   if(CopyBuffer({handle_name}, 1, 0, 5, macd_signal) < 5) return;'''

    @staticmethod
    def generate_bb_read(handle_name: str) -> str:
        """Generate Bollinger Bands buffer read code (upper, middle, lower)."""
        return f'''   double bb_upper[], bb_middle[], bb_lower[];
   ArraySetAsSeries(bb_upper, true);
   ArraySetAsSeries(bb_middle, true);
   ArraySetAsSeries(bb_lower, true);
   if(CopyBuffer({handle_name}, 1, 0, 5, bb_upper) < 5) return;
   if(CopyBuffer({handle_name}, 0, 0, 5, bb_middle) < 5) return;
   if(CopyBuffer({handle_name}, 2, 0, 5, bb_lower) < 5) return;'''

    @staticmethod
    def generate_stochastic_read(handle_name: str) -> str:
        """Generate Stochastic buffer read code (main + signal)."""
        return f'''   double stoch_main[], stoch_signal[];
   ArraySetAsSeries(stoch_main, true);
   ArraySetAsSeries(stoch_signal, true);
   if(CopyBuffer({handle_name}, 0, 0, 5, stoch_main) < 5) return;
   if(CopyBuffer({handle_name}, 1, 0, 5, stoch_signal) < 5) return;'''

    @staticmethod
    def generate_adx_read(handle_name: str) -> str:
        """Generate ADX buffer read code (ADX, +DI, -DI)."""
        return f'''   double adx_main[], adx_plus[], adx_minus[];
   ArraySetAsSeries(adx_main, true);
   ArraySetAsSeries(adx_plus, true);
   ArraySetAsSeries(adx_minus, true);
   if(CopyBuffer({handle_name}, 0, 0, 5, adx_main) < 5) return;
   if(CopyBuffer({handle_name}, 1, 0, 5, adx_plus) < 5) return;
   if(CopyBuffer({handle_name}, 2, 0, 5, adx_minus) < 5) return;'''

    @staticmethod
    def generate_price_arrays() -> str:
        """Generate price data arrays (close, open, high, low)."""
        return '''   double close[], open[], high[], low[];
   ArraySetAsSeries(close, true);
   ArraySetAsSeries(open, true);
   ArraySetAsSeries(high, true);
   ArraySetAsSeries(low, true);
   if(CopyClose(_Symbol, PERIOD_CURRENT, 0, 10, close) < 10) return;
   if(CopyOpen(_Symbol, PERIOD_CURRENT, 0, 10, open) < 10) return;
   if(CopyHigh(_Symbol, PERIOD_CURRENT, 0, 10, high) < 10) return;
   if(CopyLow(_Symbol, PERIOD_CURRENT, 0, 10, low) < 10) return;'''

    @staticmethod
    def generate_release(handle_name: str, htf: bool = False) -> str:
        """Generate indicator release code for OnDeinit."""
        suffix = "_htf" if htf else ""
        return f"   IndicatorRelease({handle_name}{suffix});"

    @classmethod
    def generate_for_indicator(
        cls,
        indicator_type: str,
        handle_name: str,
        params: dict,
        timeframe: str = "PERIOD_CURRENT"
    ) -> dict:
        """
        Generate all code blocks for an indicator.
        
        Returns dict with: declaration, init, read, release
        """
        result = {
            "declaration": cls.generate_handle_declaration(indicator_type, handle_name),
            "init": "",
            "read": "",
            "release": cls.generate_release(handle_name)
        }
        
        if indicator_type == "EMA":
            result["init"] = cls.generate_ema_init(
                handle_name, params.get("period", 14), timeframe
            )
            result["read"] = cls.generate_ema_read(handle_name, f"{handle_name}_val")
            
        elif indicator_type == "SMA":
            result["init"] = cls.generate_sma_init(
                handle_name, params.get("period", 14), timeframe
            )
            result["read"] = cls.generate_buffer_read(handle_name, f"{handle_name}_val")
            
        elif indicator_type == "RSI":
            result["init"] = cls.generate_rsi_init(
                handle_name, params.get("period", 14), timeframe
            )
            result["read"] = cls.generate_rsi_read(handle_name, f"{handle_name}_val")
            
        elif indicator_type == "MACD":
            result["init"] = cls.generate_macd_init(
                handle_name,
                params.get("fast", 12),
                params.get("slow", 26),
                params.get("signal", 9),
                timeframe
            )
            result["read"] = cls.generate_macd_read(handle_name)
            
        elif indicator_type == "ATR":
            result["init"] = cls.generate_atr_init(
                handle_name, params.get("period", 14), timeframe
            )
            result["read"] = cls.generate_buffer_read(handle_name, f"{handle_name}_val")
            
        elif indicator_type == "BB":
            result["init"] = cls.generate_bb_init(
                handle_name,
                params.get("period", 20),
                params.get("deviation", 2.0),
                timeframe
            )
            result["read"] = cls.generate_bb_read(handle_name)
            
        elif indicator_type == "Stochastic":
            result["init"] = cls.generate_stochastic_init(
                handle_name,
                params.get("kPeriod", 5),
                params.get("dPeriod", 3),
                params.get("slowing", 3),
                timeframe
            )
            result["read"] = cls.generate_stochastic_read(handle_name)
            
        elif indicator_type == "ADX":
            result["init"] = cls.generate_adx_init(
                handle_name, params.get("period", 14), timeframe
            )
            result["read"] = cls.generate_adx_read(handle_name)
        
        return result
