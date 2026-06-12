-- Freqtrade PostgreSQL query templates for the current schema.
-- Verified against the live database on 2026-04-05.
--
-- Key schema changes versus older query snippets:
-- - trades.open_date_utc   -> trades.open_date
-- - trades.close_date_utc  -> trades.close_date
-- - orders.pair            -> orders.ft_pair
-- - orders.safe_amount     -> orders.ft_amount
-- - trades.open_order_id   -> no direct replacement column on trades

-- Open trades
select
    id,
    pair,
    is_open,
    open_date,
    close_date,
    enter_tag,
    exit_reason
from trades
where is_open = true
order by open_date desc
limit 20;

-- Recent trades
select
    id,
    pair,
    is_open,
    open_date,
    close_date,
    open_rate,
    close_rate,
    close_profit,
    close_profit_abs,
    enter_tag,
    exit_reason,
    leverage,
    is_short
from trades
order by coalesce(close_date, open_date) desc
limit 20;

-- Orders for selected trades
-- Replace the IDs in the IN (...) clause as needed.
select
    id,
    ft_trade_id,
    ft_pair,
    ft_order_side,
    order_id,
    status,
    order_date,
    order_filled_date,
    order_update_date,
    filled,
    ft_amount,
    average,
    ft_is_open
from orders
where ft_trade_id in (116, 149)
order by ft_trade_id, id;
