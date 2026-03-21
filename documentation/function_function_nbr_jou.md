# function_function_nbr_jou

## Overview

| Property | Value |
|----------|-------|
| **Type** | function |
| **Technology** | db2 |
| **Complexity** | 1S |
| **Schema** | fra_3000h |
| **Database** | testdb |
| **System Group** | db2_system |

## Description

`function_function_nbr_jou` is a DB2 user-defined function in the `fra_3000h` schema of `testdb`. The name indicates it computes a daily count or number ("nbr" for number, "jou" likely abbreviating the French "jour" for day), operating on hourly granularity data within the FRA domain. It reads from one upstream source, suggesting it derives a daily numeric value from an underlying data table or reference object.

## Complexity Analysis

Complexity rating: 1S. Simple function with minimal logic — a straightforward numeric calculation or lookup returning a daily count value with no complex branching or transformation. Total relationships: 1. Read dependencies: 1. Called by: 0.

## Dependencies

### Upstream (Sources)

This object reads from 1 source(s). MCP enrichment was not available to retrieve specific dependency names.

### Downstream (Consumers)

No downstream consumers detected.

## Additional Details

| Property | Value |
|----------|-------|
| **Object ID** | 2843cbff-c0da-4883-a3e4-e488957b4e9e |
| **Cluster ID** | N/A |
| **Duplicate Count** | N/A |
| **Similar Objects** | N/A |
| **Load Date** | 2026-02-20T09:24:08.187650 |

> **Note:** MCP enrichment was not available during generation. Code/DDL, detailed complexity breakdown, and specific dependency names could not be retrieved.
