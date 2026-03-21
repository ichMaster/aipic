# procedure_procedure_create_axe_tps

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

## Description

A DB2 stored procedure that creates the complete time dimension axis (axe temps) for a data warehouse. Given a year and an action flag ('A' for add, 'D' for delete), it populates or removes time reference data across multiple granularity levels: years (`D_REF_ANN`), semesters (`D_REF_STR`), quadrimesters (`D_REF_QUAD`), quarters (`D_REF_TRI`), months (`D_REF_MOI`), weeks (`D_REF_SEM`), business days (`D_REF_JOU_OUV`), and calendar days (`D_REF_JOU`). It handles French holidays via `IS_FERIE()`, ISO week numbering across year boundaries, and business day assignment logic with forward/backward lookups for weekends and holidays. Finally, it runs a large UPDATE to cross-reference all time dimension tables.

## Complexity Analysis

Rated **4XL** (Extra Large) complexity. This is a highly complex procedure with deeply nested loops (months x days), extensive date arithmetic, multiple INSERT operations across 8 reference tables, dynamic SQL for the final cross-reference UPDATE, and calls to 3 UDFs (`IS_FERIE`, `JOU_DAT`, `JOU_INT`). It has 13 read dependencies, 8 modify dependencies, and 3 call dependencies — totaling 24 relationships.

## Dependencies

### Upstream (Sources)
- **D_REF_JOU** — calendar days reference table (read and modified)
- **D_REF_JOU_OUV** — business days reference table
- **D_REF_MOI** — months reference table
- **D_REF_TRI** — quarters reference table
- **D_REF_STR** — semesters reference table
- **D_REF_QUAD** — quadrimesters reference table
- **D_REF_SEM** — weeks reference table
- **D_REF_ANN** — years reference table
- **D_REF_MOI_ANN** — month-of-year reference
- **D_REF_STR_ANN**, **D_REF_TRI_ANN**, **D_REF_QUAD_ANN**, **D_REF_SEM_ANN**, **D_REF_JOU_SEM** — additional time dimension references
- **IS_FERIE()** (function) — determines if a date is a French holiday
- **JOU_DAT()** (function) — converts integer date code to DATE
- **JOU_INT()** (function) — converts DATE to integer date code

### Downstream (Consumers)
No downstream consumers identified (called_by_object_list_count: 0).

## Code

```sql
CREATE PROCEDURE BIF3000M.CREATE_AXE_TPS (
    IN DEL	CHARACTER(1),
    IN ANNEE	SMALLINT,
    OUT RES	VARCHAR(200) )
  LANGUAGE SQL
  NOT DETERMINISTIC
  EXTERNAL ACTION
  MODIFIES SQL DATA
  CALLED ON NULL INPUT
  INHERIT SPECIAL REGISTERS
SPECIFIC SQL110922142807900
BEGIN

DECLARE CPT INTEGER DEFAULT 1;--
DECLARE INSVAL INTEGER;--
DECLARE INSVALTMP INTEGER;--
DECLARE INSLIB VARCHAR(15);--
DECLARE INSFKEY INTEGER;--
DECLARE TEMP VARCHAR(20);--
DECLARE TMP_CPT CHAR(2);--
DECLARE TMP_CPTJ CHAR(2);--
DECLARE TMP_ANN CHAR(4);--
DECLARE CPTJ INTEGER default 1;--
DECLARE IS_DATE CHAR(1);--
DECLARE INSDATE DATE;--
DECLARE INSFKEY2 INTEGER;--
DECLARE INSFKEY3 INTEGER;--
DECLARE INSFKEY4 INTEGER;--
DECLARE INSFKEY5 INTEGER;--
DECLARE PLUSJOU SMALLINT;--
DECLARE CPTMOI SMALLINT;--
DECLARE REQ_REFRESH VARCHAR(2000);--
DECLARE date_false CONDITION FOR SQLSTATE '22007';--

DECLARE CONTINUE HANDLER FOR date_false
    BEGIN
        SET IS_DATE = 'N';--
    END;--

IF (ANNEE < 1998) OR (ANNEE > 2029) THEN
    SET RES = 'ANNEE INVALIDE, VEUILLEZ RENTRER UN CHIFFRE DE 1999 A 2029';--
    RETURN -200;--
END IF ;--

IF (DEL NOT IN ('A','D')) THEN
    SET RES = 'Veuillez choisir une option correcte : A pour ajouter, D pour supprimer une annee';--
    RETURN -200;--
END IF ;--

DELETE FROM BIF3000M.D_REF_JOU WHERE TRUNC(COD_JOU,-2)/10000 = ANNEE;--
DELETE FROM BIF3000M.D_REF_JOU_OUV WHERE TRUNC(COD_JOU_OUV,-2)/10000 = ANNEE;--
DELETE FROM BIF3000M.D_REF_MOI WHERE TRUNC(COD_MOI,-2)/100 = ANNEE;--
DELETE FROM BIF3000M.D_REF_TRI WHERE TRUNC(COD_TRI,-1)/10 = ANNEE;--
DELETE FROM BIF3000M.D_REF_STR WHERE TRUNC(COD_STR,-1)/10 = ANNEE;--
DELETE FROM BIF3000M.D_REF_QUAD WHERE TRUNC(COD_QUAD,-1)/10 = ANNEE;--
DELETE FROM BIF3000M.D_REF_SEM WHERE TRUNC(COD_SEM,-2)/100 = ANNEE;--
DELETE FROM BIF3000M.D_REF_ANN WHERE COD_ANN=ANNEE;--

SET RES = 'SUPPRESSION DE L ANNEE REUSSIE';--

IF DEL = 'A' THEN
-- Populates years, semesters, quadrimesters, quarters, months, weeks,
-- business days (with holiday checking), calendar days (with ISO week
-- handling and business day assignment), and runs cross-reference UPDATE
-- ... (full procedure body ~200 lines)
END IF;--
END;
```

## Additional Details

| Property | Value |
|----------|-------|
| **Object ID** | 102b3c05-a854-4bf3-b279-fdbb8d0f5968 |
| **Total Relationships** | 24 |
| **Read Objects** | 13 |
| **Modify Objects** | 8 |
| **Call Objects** | 3 |
| **Duplicate Count** | 2 |
| **Load Date** | 2026-02-20T09:24:08.187650 |
