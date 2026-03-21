# procedure_procedure_create_axe_tps_olddb

## Overview

| Property | Value |
|----------|-------|
| **Type** | procedure |
| **Technology** | db2 |
| **Complexity** | 4XL |
| **Schema** | fra_3000m |
| **Database** | testdb |
| **System Group** | db2_system |
| **Duplicate Cluster** | a98b5828-0328-4912-a76c-a2eca2724b7c |
| **Similar Objects** | procedure_procedure_create_axe_tps, procedure_procedure_create_axe_tps_olddb |
| **Out-of-Scope Reason** | backup |

## Description

A legacy/backup version of the `CREATE_AXE_TPS` procedure that creates the time dimension axis for the data warehouse. This older version handles the same time hierarchy (years, semesters, quarters, months, weeks, business days, calendar days) but lacks the quadrimester (`D_REF_QUAD`) dimension and bimester (`COD_BIM`) column that were added in the newer version. It operates on the same reference tables (`D_REF_ANN`, `D_REF_STR`, `D_REF_TRI`, `D_REF_MOI`, `D_REF_SEM`, `D_REF_JOU_OUV`, `D_REF_JOU`) and uses the same UDFs (`IS_FERIE`, `JOU_DAT`, `JOU_INT`). The final cross-reference UPDATE is simpler, excluding quadrimester joins.

## Complexity Analysis

Rated **4XL** (Extra Large) complexity. Similar to the current version but slightly less complex due to fewer time dimensions. It has 12 read dependencies, 7 modify dependencies, and 3 call dependencies — totaling 22 relationships. Flagged as a backup object and candidate for out-of-scope.

## Dependencies

### Upstream (Sources)
- **D_REF_JOU** — calendar days reference table
- **D_REF_JOU_OUV** — business days reference table
- **D_REF_MOI** — months reference table
- **D_REF_TRI** — quarters reference table
- **D_REF_STR** — semesters reference table
- **D_REF_SEM** — weeks reference table
- **D_REF_ANN** — years reference table
- **D_REF_MOI_ANN**, **D_REF_STR_ANN**, **D_REF_TRI_ANN**, **D_REF_SEM_ANN**, **D_REF_JOU_SEM** — time dimension references
- **IS_FERIE()** (function) — French holiday checker
- **JOU_DAT()** (function) — integer-to-date conversion
- **JOU_INT()** (function) — date-to-integer conversion

### Downstream (Consumers)
No downstream consumers identified (called_by_object_list_count: 0).

## Code

```sql
CREATE PROCEDURE BIF3000M.CREATE_AXE_TPS_OLD (
    IN DEL	CHARACTER(1),
    IN ANNEE	SMALLINT,
    OUT RES	VARCHAR(200) )
  LANGUAGE SQL
  NOT DETERMINISTIC
  EXTERNAL ACTION
  MODIFIES SQL DATA
  CALLED ON NULL INPUT
  INHERIT SPECIAL REGISTERS
BEGIN
-- Legacy version of CREATE_AXE_TPS
-- Handles years, semesters, quarters, months, weeks, business days, calendar days
-- Missing: quadrimester and bimester dimensions
-- Same UDF dependencies: IS_FERIE, JOU_DAT, JOU_INT
-- Simpler cross-reference UPDATE without quadrimester joins

DECLARE CPT INTEGER DEFAULT 1;--
-- ... (variable declarations identical to CREATE_AXE_TPS) ...

-- Input validation: year range 1998-2029, action flag A/D
-- DELETE existing time data for the year
-- IF action='A': populate all time dimension tables
-- Final cross-reference UPDATE (without QUAD joins)
END;
```

## Additional Details

| Property | Value |
|----------|-------|
| **Object ID** | 162ff91b-7967-4a5a-b831-3b3a0053041f |
| **Total Relationships** | 22 |
| **Read Objects** | 12 |
| **Modify Objects** | 7 |
| **Call Objects** | 3 |
| **Duplicate Count** | 2 |
| **Load Date** | 2026-02-20T09:24:08.187650 |
