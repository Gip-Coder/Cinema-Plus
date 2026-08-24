# Database Optimization & Benchmark Report

*Timestamp:* 2026-06-27T12:10:27.155513+00:00
*Database Engine:* sqlite

## Query Latency Profile
* **Average Select Query Latency:** 0.0895 ms
* **Best Query Duration:** 0.0768 ms
* **Worst Query Duration:** 0.2847 ms
* **Throughput Capacity (Read TPS):** 11130.5 queries/sec
* **Connection Pool Capacity:** 5 active slots

## Explain Query Plan Example
*Query:* `SELECT * FROM movies WHERE title = 'Tenet'`
```
(3, 0, 0, 'SEARCH movies USING INDEX ix_movies_title (title=?)')
```

## Schema & Index Assessment
* **Tables Audited:** audit_logs, booked_seats, bookings, media_assets, movies, pricing_rules, reservation_groups, reviews, screens, seat_pricings, seat_reservations, shows, theatres, users
* **Active Indexes:** 46 indexes found
* **Missing Index Recommendations:** 1 recommendations

### Recommended Indexes
* **Table:** `shows`, **Column:** `screen_id`
  *Reason:* Foreign key column 'screen_id' lacks an index, leading to table scans on joins.
  *SQL Command:* `CREATE INDEX idx_shows_screen_id ON shows(screen_id);`
