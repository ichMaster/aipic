# procedure_procedure_couv_stock_semaine

## Overview

| Property | Value |
|----------|-------|
| **Type** | procedure |
| **Technology** | db2 |
| **Complexity** | 4XL |
| **Schema** | fra_bi |
| **Database** | testdb |
| **System Group** | db2_system |

## Description

A DB2 stored procedure that calculates weekly stock coverage (couverture de stock en semaines). It iterates through stock records from `MSNP_FW_COUV`, and for each stock position, calculates how many weeks of demand the initial stock can cover. The algorithm subtracts weekly demand (`DEMTOT_QTB`) from the initial stock quantity (`STKINI_QTB`) until stock is depleted, computing a fractional week count for partial coverage. Results are written back to the `MSNP_FW_COUV` table's `COUSTK_NBW` column. Error handling logs exceptions to `MSNP_FW_COUV_ERROR`.

## Complexity Analysis

Rated **4XL** (Extra Large) complexity. The procedure features nested cursor loops (stock positions x demand weeks), dynamic SQL preparation, complex decimal arithmetic for fractional week calculation, and comprehensive error handling with EXIT HANDLER. It has 3 read dependencies and 2 modify dependencies.

## Dependencies

### Upstream (Sources)
- **MSNP_FW_COUV** (table) — stock and demand data by plant/family/product/week
- **psnp_fd0** (table) — provides the current SNP version number for filtering

### Downstream (Consumers)
- **MSNP_FW_COUV** (table) — updated with calculated stock coverage weeks (COUSTK_NBW)
- **MSNP_FW_COUV_ERROR** (table) — receives error logs when exceptions occur

## Code

```sql
create or replace procedure BIDEF.Couv_stock_semaine ( INOUT a_codret varchar(4000) )
LANGUAGE SQL
BEGIN
DECLARE err_msg varchar(300);
    DECLARE err_num DECIMAL(31,0);--
    DECLARE Nb_Semaine DECIMAL(10,2);--
    DECLARE Diff DECIMAL(17,3);--
    DECLARE Premier_enr_C1 DECIMAL(31,0);--
    DECLARE Premier_enr_C2 DECIMAL(31,0);--
    DECLARE Rupture DECIMAL(31,0);--
    DECLARE C1_FOUND INTEGER DEFAULT NULL;--
DECLARE C2_STMTSTR varchar(32672) DEFAULT 'SELECT SAP_PLT_COD, INDFAM_COD, PDTTOP_COD, WEK_COD, SNPVER_NUM, TPS_COD, STKINI_QTB, DEMTOT_QTB FROM BIDEF.MSNP_FW_COUV WHERE SAP_PLT_COD = CAST(? AS varchar(4000)) AND INDFAM_COD = CAST(? AS varchar(4000)) AND PDTTOP_COD = CAST(? AS varchar(4000)) AND WEK_COD > CAST(? AS FLOAT) AND snpver_num = (SELECT snpver_num FROM BIDEF.psnp_fd0) ORDER BY 1, 2, 3, 4';--
    DECLARE C2_FOUND INTEGER DEFAULT NULL;--
    DECLARE SQLCODE INTEGER DEFAULT 0;--
    DECLARE SQLCODE1 INTEGER;--
    -- ... (variable declarations for rec_Stocks and rec_Demande) ...
    DECLARE C1 CURSOR FOR SELECT SAP_PLT_COD, INDFAM_COD, PDTTOP_COD, WEK_COD,
                                 SNPVER_NUM, TPS_COD, STKINI_QTB, DEMTOT_QTB
                          FROM BIDEF.MSNP_FW_COUV
                          WHERE snpver_num = (SELECT snpver_num FROM BIDEF.psnp_fd0)
                          ORDER BY 1, 2, 3, 4;--
    DECLARE C2 CURSOR FOR C2_STMT;--
    DECLARE EXIT HANDLER FOR SQLEXCEPTION, SQLWARNING, NOT FOUND
        BEGIN
            SET SQLCODE1 = SQLCODE;--
            SET err_num = SQLCODE1;--
            SET err_msg = to_char(SQLCODE1);--
            INSERT INTO BIDEF.MSNP_FW_COUV_ERROR (NUM_ERROR, MESSAGE) VALUES (err_num, err_msg);--
            COMMIT;--
            CLOSE C1;--
            CLOSE C2;--
        END;--
    -- Main processing loop: iterate stock records, calculate coverage weeks
    -- For each stock position, subtract demand until stock depleted
    -- Update COUSTK_NBW with calculated weeks of coverage
END;
```

## Additional Details

| Property | Value |
|----------|-------|
| **Object ID** | c69db05e-8054-43ef-a0f8-648aea904848 |
| **Total Relationships** | 5 |
| **Read Objects** | 3 |
| **Modify Objects** | 2 |
| **Load Date** | 2026-02-20T09:24:08.187650 |
