# procedure_procedure_grade_student_encrypted (db2inst1)

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

A DB2 stored procedure that grades a student based on their ID and grade value. The procedure accepts a `student_id` (INT) and `student_grade` (INT) as input parameters. The procedure body is encrypted/wrapped using DB2's WRAPPED encoding, so the actual implementation logic is not readable. This is a copy of the same procedure in the `sasha_test` schema, deployed to the `db2inst1` schema (likely a production or main instance schema).

## Complexity Analysis

Rated **4XL** (Extra Large) complexity. Detailed complexity attribute breakdown was not available during documentation generation.

## Dependencies

### Upstream (Sources)
1 read dependency identified (specific object not available from lineage data).

### Downstream (Consumers)
No downstream consumers identified (read_by_object_list_count: 0).

## Code

```sql
-- Procedure body is encrypted (WRAPPED)
CREATE OR REPLACE PROCEDURE grade_student_encrypted(student_id INT, student_grade INT)
  WRAPPED SQL11057 ablGWmdiWmJiTmteTmdeTmtmUmZiUndyUmtC0mJmWidaWmdaWmdaXmtzeoYaGicaG...
```

## Additional Details

| Property | Value |
|----------|-------|
| **Object ID** | 19de15c5-2b14-4293-99c8-fe4905287555 |
| **Total Relationships** | 1 |
| **Read Objects** | 1 |
| **Load Date** | 2026-02-20T09:24:08.187650 |
