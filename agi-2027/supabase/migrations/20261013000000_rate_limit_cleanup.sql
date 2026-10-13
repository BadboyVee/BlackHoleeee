-- Milestone 2: rate limit rows no longer outlive their use.
--
-- take_rate_limit cleared only the earlier windows of the bucket it was
-- counting, so a visitor who sent one form and never came back left a row
-- (a salted hash of their IP) behind for good. Each call now also clears
-- every window that started over two days ago, whoever it counted, so a
-- hashed IP is kept two days at most; the privacy page says so. Windows are
-- capped at one day, so the cleanup never touches a window still counting.

create index rate_limits_window_start_idx on public.rate_limits (window_start);

create or replace function private.take_rate_limit(p_bucket text, p_limit integer, p_window interval)
returns boolean
language plpgsql
volatile
security definer
set search_path = ''
as $$
declare
  v_window_start timestamptz;
  v_hits integer;
begin
  if p_bucket is null or p_limit is null or p_window is null
     or p_window <= interval '0' or p_window > interval '1 day' then
    raise exception 'take_rate_limit needs a bucket, a limit and a window of at most a day'
      using errcode = '22023';
  end if;

  -- Fixed windows lined up with the epoch: for one hour, each clock hour in UTC.
  v_window_start := pg_catalog.date_bin(p_window, now(), timestamptz '1970-01-01 00:00:00+00');

  insert into public.rate_limits as r (bucket, window_start, hits)
  values (p_bucket, v_window_start, 1)
  on conflict (bucket, window_start) do update set hits = r.hits + 1
  returning r.hits into v_hits;

  -- Earlier windows for this bucket no longer matter.
  delete from public.rate_limits r
  where r.bucket = p_bucket and r.window_start < v_window_start;

  -- Nor does any window that started over two days ago, whoever it counted.
  delete from public.rate_limits r
  where r.window_start < now() - interval '2 days';

  return v_hits <= p_limit;
end;
$$;

comment on function private.take_rate_limit(text, integer, interval) is
  'Counts one hit for a bucket and says whether it is still within p_limit hits for the '
  'current window (true = allowed). Windows are fixed, line up with the clock and last at '
  'most a day. Also clears windows that started over two days ago, so hashed IPs are kept '
  'two days at most. Safe under concurrent calls.';
