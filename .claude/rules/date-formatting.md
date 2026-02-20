# Date Formatting

## YYYY-MM-DD strings must be parsed as local time

`new Date('2026-02-23')` parses as **UTC midnight**, which shifts back a day in western timezones. This causes off-by-one display bugs.

**Wrong:**
```typescript
new Date(dateStr).toLocaleDateString(...) // UTC -- shows wrong day
```

**Correct:**
```typescript
const [y, m, d] = dateStr.split('-').map(Number);
const date = new Date(y!, m! - 1, d!); // Local time -- correct day
```
