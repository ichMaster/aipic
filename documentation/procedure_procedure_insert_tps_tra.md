# procedure_procedure_insert_tps_tra

## Overview

| Property | Value |
|----------|-------|
| **Type** | procedure |
| **Technology** | db2 |
| **Complexity** | 4XL |
| **Schema** | fra_3000m |
| **Database** | testdb |
| **System Group** | db2_system |

## Description

A DB2 stored procedure that builds transcodification (cross-reference) tables for cumulative calculations in MicroStrategy (MSTR). For each day in the calendar reference table (`D_REF_JOU`), it populates 19 different transcodification tables that map time periods to their constituent days. These include Year-to-Date (YTD), Month-to-Date (MTD), Quarter-to-Date (TTD), Semester-to-Date (STD), Bimester-to-Date (BTD), rolling 15-day (XV_GLS), rolling 30-day (XXX_GLS), and other temporal aggregation mappings. It also handles month-level YTD, TTD, YFD, and rolling 12-month mappings, as well as business day equivalents.

## Complexity Analysis

Rated **4XL** (Extra Large) complexity. This is the most relationship-heavy procedure in the inventory with 40 total relationships: 20 read dependencies (all time dimension reference tables), 19 modify dependencies (all transcodification target tables), and 1 call dependency (`WEEK_TRUNC` function). The procedure uses extensive dynamic SQL with PREPARE/EXECUTE inside a FOR loop over all days, generating massive volumes of cross-reference data.

## Dependencies

### Upstream (Sources)
- **D_REF_JOU** (table) — calendar days reference, iterated for each day
- **D_REF_JOU_OUV** (table) — business days reference
- **D_REF_MOI** (table) — months reference
- **D_REF_SEM** (table) — weeks reference
- **D_REF_ANN** (table) — years reference
- **WEEK_TRUNC()** (function) — calculates the start of a week for a given day code

### Downstream (Consumers)
- **D_TRA_MOI_YTD**, **D_TRA_MOI_TTD**, **D_TRA_MOI_YFD** — month-level cumulative transco tables
- **D_TRA_MOI_ANN_YTD**, **D_TRA_MOI_XII_GLS** — month-year and rolling 12-month transco
- **D_TRA_SEM_YTD**, **D_TRA_SEM_YFD** — week-level cumulative transco tables
- **D_TRA_JOU_YTD**, **D_TRA_JOU_MTD**, **D_TRA_JOU_TTD** — day-level YTD/MTD/TTD transco
- **D_TRA_JOU_STD**, **D_TRA_JOU_BTD** — day-level semester/bimester transco
- **D_TRA_JOU_OUV_YTD**, **D_TRA_JOU_OUV_MTD**, **D_TRA_JOU_OUV_TTD**, **D_TRA_JOU_OUV_STD** — business day transco
- **D_TRA_JOU_XV_GLS**, **D_TRA_JOU_XXX_GLS** — rolling 15/30-day transco
- **D_TRA_MOI_FEV_LY** — February last-year transco

## Code

```sql
CREATE PROCEDURE BIF3000M.INSERT_TPS_TRA()
  SPECIFIC BIF3000M.INSERT_TPS_TRA
  LANGUAGE SQL
  NOT DETERMINISTIC
  CALLED ON NULL INPUT
  EXTERNAL ACTION
  OLD SAVEPOINT LEVEL
  MODIFIES SQL DATA
  INHERIT SPECIAL REGISTERS
------------------------------------------------------------------------
-- Construction des tables de transco pour les cumuls dans MSTR
------------------------------------------------------------------------
BEGIN
    DECLARE jour_start_week INTEGER;
    DECLARE REQ VARCHAR(1000);

    -- Delete data from all 19 transcodification tables
    DELETE FROM BIF3000M.D_TRA_MOI_YTD;
    DELETE FROM BIF3000M.D_TRA_MOI_TTD;
    DELETE FROM BIF3000M.D_TRA_MOI_YFD;
    DELETE FROM BIF3000M.D_TRA_MOI_ANN_YTD;
    DELETE FROM BIF3000M.D_TRA_MOI_XII_GLS;
    DELETE FROM BIF3000M.D_TRA_SEM_YTD;
    DELETE FROM BIF3000M.D_TRA_SEM_YFD;
    DELETE FROM BIF3000M.D_TRA_JOU_YTD;
    DELETE FROM BIF3000M.D_TRA_JOU_MTD;
    DELETE FROM BIF3000M.D_TRA_JOU_TTD;
    DELETE FROM BIF3000M.D_TRA_JOU_STD;
    DELETE FROM BIF3000M.D_TRA_JOU_BTD;
    DELETE FROM BIF3000M.D_TRA_JOU_OUV_YTD;
    DELETE FROM BIF3000M.D_TRA_JOU_OUV_MTD;
    DELETE FROM BIF3000M.D_TRA_JOU_OUV_TTD;
    DELETE FROM BIF3000M.D_TRA_JOU_OUV_STD;
    DELETE FROM BIF3000M.D_TRA_JOU_XV_GLS;
    DELETE FROM BIF3000M.D_TRA_JOU_XXX_GLS;
    DELETE FROM BIF3000M.D_TRA_MOI_FEV_LY;

    -- For each day, build YTD, MTD, TTD, STD, BTD, rolling 15/30-day mappings
    FOR v1 AS SELECT COD_JOU AS jourins FROM BIF3000M.D_REF_JOU DO
        -- INSERT INTO D_TRA_JOU_YTD: all days from Jan 1 to current day
        -- INSERT INTO D_TRA_JOU_MTD: all days from month start to current day
        -- INSERT INTO D_TRA_JOU_TTD: all days from quarter start to current day
        -- INSERT INTO D_TRA_JOU_XV_GLS: rolling 15-day window
        -- INSERT INTO D_TRA_JOU_XXX_GLS: rolling 30-day window
        -- INSERT INTO D_TRA_JOU_BTD: bimester-to-date
        -- INSERT INTO D_TRA_JOU_STD: week-to-date (using WEEK_TRUNC)
    END FOR;
END;
```

## Additional Details

| Property | Value |
|----------|-------|
| **Object ID** | 3e693311-44fc-4448-9965-9da50321a249 |
| **Total Relationships** | 40 |
| **Read Objects** | 20 |
| **Modify Objects** | 19 |
| **Call Objects** | 1 |
| **Load Date** | 2026-02-20T09:24:08.187650 |
