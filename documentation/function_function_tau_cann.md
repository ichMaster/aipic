# function_function_tau_cann

## Overview

| Property | Value |
|----------|-------|
| **Type** | function |
| **Technology** | db2 |
| **Complexity** | 2M |
| **Schema** | fra_3000h |
| **Database** | testdb |
| **System Group** | db2_system |

## Description

`function_function_tau_cann` is a DB2 user-defined function in the `fra_3000h` schema. The name suggests it calculates a cancellation rate ("tau cann" likely abbreviating "taux d'annulation"), a metric commonly used to measure the proportion of cancelled transactions or contracts within a given period. It reads from two source objects to derive this rate, indicating it compares or joins data from multiple tables.

## Complexity Analysis

Complexity rating: 2M. Medium complexity driven by the rate calculation logic that likely involves combining or comparing values from two distinct source objects, potentially using division or ratio operations. Total relationships: 2. Read dependencies: 2. Called by: 0.

## Dependencies

### Upstream (Sources)

This object reads from 2 source(s). MCP enrichment was not available to retrieve specific dependency names.

### Downstream (Consumers)

No downstream consumers detected.

## Additional Details

| Property | Value |
|----------|-------|
| **Object ID** | 66de3837-430d-4985-a1ea-ee66ff03f820 |
| **Cluster ID** | N/A |
| **Duplicate Count** | N/A |
| **Similar Objects** | N/A |
| **Load Date** | 2026-02-20T09:24:08.187650 |

> **Note:** MCP enrichment was not available during generation. Code/DDL, detailed complexity breakdown, and specific dependency names could not be retrieved.
