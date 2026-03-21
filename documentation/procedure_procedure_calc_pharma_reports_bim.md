# procedure_procedure_calc_pharma_reports_bim

## Overview

| Property | Value |
|----------|-------|
| **Type** | procedure |
| **Technology** | db2 |
| **Complexity** | 4XL |
| **Schema** | fra_3000m |
| **Database** | testdb |
| **System Group** | db2_system |
| **Duplicate Cluster** | 84127316-5c18-482d-823c-0e766d83a330 |
| **Similar Objects** | procedure_procedure_calc_pharma_reports, procedure_procedure_calc_pharma_reports_bim |

## Description

A DB2 stored procedure that calculates pharmaceutical sales reports for the BIM (Business Intelligence Management) variant. It is nearly identical to `CALC_PHARMA_REPORTS` but operates on a test/BIM-specific dataset. It iterates over days of the year, loops through product families and sectors, compares current year vs previous year revenue from `D_F_PHA_VTE_EST_JOU_TEST`, retrieves objectives from `D_REF_PHA_OBJ_JOU_BIM_V`, and writes results to `D_F_PHA_BON_BIM`. After processing, it zeroes out future dates and removes zero-value rows.

## Complexity Analysis

Rated **4XL** (Extra Large) complexity. Like its sibling procedure, it uses extensive dynamic SQL with PREPARE/EXECUTE, multiple nested cursor loops, and complex date arithmetic. It has 2 read dependencies and uses BIM-specific target tables.

## Dependencies

### Upstream (Sources)
- **D_REF_JOU** (table) — provides the list of days for the year
- **D_PAR_DWH** (table) — provides the DELTA_MOIS_PHA parameter
- **D_F_PHA_VTE_EST_JOU_TEST** (table) — BIM-specific pharmaceutical sales estimates
- **D_REF_PHA_OBJ_JOU_BIM_V** (view) — BIM-specific daily objective revenue data

### Downstream (Consumers)
- **D_F_PHA_BON_BIM** (table) — BIM-specific target table for calculated pharma report data

## Code

```sql
CREATE PROCEDURE BIF3000M.CALC_PHARMA_REPORTS_BIM
()
LANGUAGE SQL
SPECIFIC CALC_PHARMA_REPORTS_BIM
 BEGIN
 DECLARE REQ VARCHAR(1000);--
 DECLARE JOUR_A INTEGER;--
 DECLARE JOUR_A1 INTEGER;--
 DECLARE NB_ENR INTEGER;--
 DECLARE OK INTEGER;--
 DECLARE V_SEC_ID , V_GAM_ID INTEGER;--
 DECLARE CA_A , CA_A1 , OBJ_A DECIMAL(20,7);--
 DECLARE AT_END SMALLINT DEFAULT 0;--
 DECLARE not_found CONDITION FOR SQLSTATE '02000';--
 DECLARE rec_still_exist CONDITION FOR SQLSTATE '23505';--
 DECLARE CJOUR CURSOR FOR SELECT cod_jou FROM BIF3000M.D_REF_JOU WHERE COD_JOU between
      year(current date - (select int(val_par)-12 from BIF3000M.D_PAR_DWH where cod_par = 'DELTA_MOIS_PHA') month) *10000 + month(current date - (select int(val_par)-12 from BIF3000M.D_PAR_DWH where cod_par = 'DELTA_MOIS_PHA') month)*100 +1 AND int(trim(char(year(current date))) || '1231');--
 DECLARE C1 CURSOR FOR SQL1;--
 DECLARE C2 CURSOR FOR SQL2;--
 DECLARE C3 CURSOR FOR SQL3;--
 DECLARE C4 CURSOR FOR SQL4;--
 DECLARE C5 CURSOR FOR SQL5;--
 DECLARE CONTINUE HANDLER FOR not_found SET AT_END = 1;--
 SET AT_END = 0;--
 OPEN CJOUR;--
 WHILE (AT_END=0) DO
     FETCH CJOUR INTO JOUR_A;--
     IF (AT_END<>1) THEN
        SET REQ = 'select int(trim(char(int(substr(trim(char(cod_jou)),1,4))-1)) || substr(trim(char(cod_jou)),5,4)) from BIF3000M.D_REF_JOU where cod_jou = '||char(JOUR_A);--
        PREPARE SQL1 FROM REQ;--
        OPEN C1;--
        FETCH C1 INTO JOUR_A1;--
        CLOSE C1;--

        SET REQ = 'select distinct coalesce(sec_pha_id,0) , gam_id from BIF3000M.D_F_PHA_VTE_EST_JOU_TEST';--
        PREPARE SQL2 FROM REQ;--
        OPEN C2;--
        WHILE (AT_END=0) DO
           FETCH C2 INTO V_SEC_ID , V_GAM_ID;--
           IF (AT_END<>1) THEN
               SET OK = 0;--
               SET REQ = 'Select count(*) from BIF3000M.D_F_PHA_VTE_EST_JOU_TEST where cod_jou = '||char(JOUR_A)||' and coalesce(sec_pha_id,0) = '||char(V_SEC_ID)||' and gam_id = '||char(V_GAM_ID);--
               PREPARE SQL3 FROM REQ;--
               OPEN C3;--
               FETCH C3 INTO NB_ENR;--
               CLOSE C3;--
               SET CA_A = 0;--
               IF (NB_ENR<>0) THEN
                  SET OK = 1;--
                  SET REQ = 'Select sum(pht_net_tot) from BIF3000M.D_F_PHA_VTE_EST_JOU_TEST where cod_jou = '||char(JOUR_A)||' and coalesce(sec_pha_id,0) = '||char(V_SEC_ID)||' and gam_id = '||char(V_GAM_ID);--
                  PREPARE SQL3 FROM REQ;--
                  OPEN C3;--
                  FETCH C3 INTO CA_A;--
                  CLOSE C3;--
               END IF;--
               SET REQ = 'Select count(*) from BIF3000M.D_F_PHA_VTE_EST_JOU_TEST where cod_jou = '||char(JOUR_A1)||' and coalesce(sec_pha_id,0) = '||char(V_SEC_ID)||' and gam_id = '||char(V_GAM_ID);--
               PREPARE SQL4 FROM REQ;--
               OPEN C4;--
               FETCH C4 INTO NB_ENR;--
               CLOSE C4;--
               SET CA_A1 = 0;--
               IF (NB_ENR<>0) THEN
                  SET OK = 1;--
                  SET REQ = 'Select sum(pht_net_tot) from BIF3000M.D_F_PHA_VTE_EST_JOU_TEST where cod_jou = '||char(JOUR_A1)||' and coalesce(sec_pha_id,0) = '||char(V_SEC_ID)||' and gam_id = '||char(V_GAM_ID);--
                  PREPARE SQL4 FROM REQ;--
                  OPEN C4;--
                  FETCH C4 INTO CA_A1;--
                  CLOSE C4;--
                END IF;--
               SET REQ = 'select count(*) from BIF3000M.D_REF_PHA_OBJ_JOU_BIM_V where cod_jou = '||char(JOUR_A)||' and coalesce(sec_pha_id,0) = '||char(V_SEC_ID)||' and gam_id = '||char(V_GAM_ID);--
               PREPARE SQL5 FROM REQ;--
               OPEN C5;--
               FETCH C5 INTO NB_ENR;--
               CLOSE C5;--
               SET OBJ_A = 0;--
               IF (NB_ENR<>0) THEN
                  SET OK = 1;--
                  SET REQ = 'select sum(CA_OBJ_JOU) from BIF3000M.D_REF_PHA_OBJ_JOU_BIM_V where cod_jou = '||char(JOUR_A)||' and coalesce(sec_pha_id,0) = '||char(V_SEC_ID)||' and gam_id = '||char(V_GAM_ID);--
                  PREPARE SQL5 FROM REQ;--
                  OPEN C5;--
                  FETCH C5 INTO OBJ_A;--
                  CLOSE C5;--
                END IF;--

               IF (OK <> 0) THEN
                   SET REQ = 'INSERT INTO BIF3000M.D_F_PHA_BON_BIM (COD_JOU , GAM_ID , SEC_PHA_ID , CA_REA_A , CA_REA_A1 , CA_OBJ_AD) VALUES ('||char(JOUR_A)||','||char(V_GAM_ID)||','||char(V_SEC_ID)||','||char(CA_A)||','||char(CA_A1)||','||char(OBJ_A)||')';--
                   PREPARE r2 from REQ;--
                   EXECUTE r2;--
               END IF;--

           END IF;--
        END WHILE;--
        CLOSE C2;--
        SET AT_END=0;--

     END IF;--

 END WHILE;--
 CLOSE CJOUR;--
 COMMIT;--

 SET REQ = 'update BIF3000M.D_F_PHA_BON_BIM set CA_REA_A = 0 , CA_REA_A1 = 0 where cod_jou > int(year(current date -1 day) *10000 + month(current date -1 day) *100 + day(current date -1 day))';--
 PREPARE r2 from REQ;--
 EXECUTE r2;--

 SET REQ = 'delete from BIF3000M.D_F_PHA_BON_BIM where ca_rea_a = 0 and ca_rea_a1 = 0 and ca_obj_ad = 0';--
 PREPARE r2 from REQ;--
 EXECUTE r2;--
END;
```

## Additional Details

| Property | Value |
|----------|-------|
| **Object ID** | 76dce827-6818-48fb-9eef-68421c26a6a5 |
| **Total Relationships** | 2 |
| **Read Objects** | 2 |
| **Duplicate Count** | 2 |
| **Load Date** | 2026-02-20T09:24:08.187650 |
