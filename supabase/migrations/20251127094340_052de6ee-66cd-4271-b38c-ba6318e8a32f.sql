-- Create trades table for trade journal
CREATE TABLE public.trades (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  instrument TEXT NOT NULL,
  direction TEXT NOT NULL CHECK (direction IN ('long', 'short')),
  entry_price DECIMAL(18, 5) NOT NULL,
  exit_price DECIMAL(18, 5),
  position_size DECIMAL(18, 5) NOT NULL,
  entry_date TIMESTAMPTZ NOT NULL DEFAULT now(),
  exit_date TIMESTAMPTZ,
  profit_loss DECIMAL(18, 5),
  profit_loss_percent DECIMAL(10, 4),
  notes TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Enable RLS
ALTER TABLE public.trades ENABLE ROW LEVEL SECURITY;

-- RLS Policies: Users can only see and manage their own trades
CREATE POLICY "Users can view their own trades"
  ON public.trades
  FOR SELECT
  TO authenticated
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own trades"
  ON public.trades
  FOR INSERT
  TO authenticated
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own trades"
  ON public.trades
  FOR UPDATE
  TO authenticated
  USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own trades"
  ON public.trades
  FOR DELETE
  TO authenticated
  USING (auth.uid() = user_id);

-- Function to automatically update profit_loss when exit_price is set
CREATE OR REPLACE FUNCTION public.calculate_trade_profit()
RETURNS TRIGGER AS $$
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
$$ LANGUAGE plpgsql;

CREATE TRIGGER calculate_trade_profit_trigger
  BEFORE INSERT OR UPDATE ON public.trades
  FOR EACH ROW
  EXECUTE FUNCTION public.calculate_trade_profit();

-- Function to update timestamps
CREATE OR REPLACE FUNCTION public.update_trades_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_trades_updated_at
  BEFORE UPDATE ON public.trades
  FOR EACH ROW
  EXECUTE FUNCTION public.update_trades_updated_at();