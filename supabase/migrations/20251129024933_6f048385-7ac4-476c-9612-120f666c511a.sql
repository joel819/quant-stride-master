-- Fix security warnings by setting search_path on existing functions

-- Update calculate_trade_profit function with proper search_path
CREATE OR REPLACE FUNCTION public.calculate_trade_profit()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $function$
BEGIN
  IF NEW.exit_price IS NOT NULL THEN
    IF NEW.direction = 'long' THEN
      NEW.profit_loss := (NEW.exit_price - NEW.entry_price) * NEW.position_size;
      NEW.profit_loss_percent := ((NEW.exit_price - NEW.entry_price) / NEW.entry_price) * 100;
    ELSE -- short
      NEW.profit_loss := (NEW.entry_price - NEW.exit_price) * NEW.position_size;
      NEW.profit_loss_percent := ((NEW.entry_price - NEW.exit_price) / NEW.entry_price) * 100;
    END IF;
  END IF;
  RETURN NEW;
END;
$function$;

-- Update update_trades_updated_at function with proper search_path
CREATE OR REPLACE FUNCTION public.update_trades_updated_at()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $function$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$function$;