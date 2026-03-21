# procedure_procedure_truncate

## Overview

| Property | Value |
|----------|-------|
| **Type** | procedure |
| **Technology** | db2 |
| **Complexity** | 4XL |
| **Schema** | db2inst1 |
| **Database** | testdb |
| **System Group** | db2_system |

## Description

A DB2 stored procedure that simulates SQL TRUNCATE functionality by using the `IMPORT FROM NUL OF DEL REPLACE INTO` technique via `SYSPROC.ADMIN_CMD`. It accepts a schema name and table name as input parameters, verifies the table exists by querying `SYSCAT.TABLES`, and if found, executes an import from a null device to effectively empty the table. This approach was commonly used in DB2 versions where native TRUNCATE was not available or had limitations. The schema parameter is optional — if NULL, only the table name is used.

## Complexity Analysis

Rated **4XL** (Extra Large) complexity. The procedure has 6 read dependencies (primarily system catalog queries). It uses dynamic SQL with PREPARE/EXECUTE and calls the DB2 administrative command interface (`SYSPROC.ADMIN_CMD`).

## Dependencies

### Upstream (Sources)
- **SYSCAT.TABLES** (system catalog) — used to verify table existence before truncation
- **SYSPROC.ADMIN_CMD** (system procedure) — executes the IMPORT command to truncate the table

### Downstream (Consumers)
No downstream consumers identified (read_by_object_list_count: 0).

## Code

```sql
CREATE PROCEDURE truncate(IN sch_name VARCHAR(130), IN tab_name VARCHAR(130))
  LANGUAGE SQL
  ---------------------------------
  -- Procedure stockee pour simuler un TRUNCATE SQL
  ---------------------------------
  BEGIN
    DECLARE stmt VARCHAR(1000);--
    DECLARE param VARCHAR(1000);--
    DECLARE full_name VARCHAR(1000);--
    DECLARE a VARCHAR(130);--

    IF sch_name IS NULL
      THEN
        SET full_name = tab_name;--
        -- Verification de l'existence de la table
        SELECT tabname INTO a
          FROM SYSCAT.TABLES
          WHERE tabname = UCASE(tab_name);--
    ELSE
      SET full_name = sch_name||'.'||tab_name;--
      -- Verification de l'existence de la table
      SELECT tabname INTO a
        FROM SYSCAT.TABLES
        WHERE tabname = UCASE(tab_name) AND tabschema = UCASE(sch_name);--
    END IF;--

    IF UCASE(a) = UCASE(tab_name)
      THEN
        SET param = 'IMPORT FROM NUL OF DEL REPLACE INTO '||full_name;--
        SET stmt = 'CALL SYSPROC.ADMIN_CMD (?)';--
        PREPARE s1 FROM stmt;--
        EXECUTE s1 USING param;--
    ELSE
      -- La table n'existe pas
    END IF;--
  END;
```

## Additional Details

| Property | Value |
|----------|-------|
| **Object ID** | ac8b919d-e5be-43a2-bd36-98b6b4242ac9 |
| **Total Relationships** | 6 |
| **Read Objects** | 6 |
| **Load Date** | 2026-02-20T09:24:08.187650 |
