# function_function_nbr_sem

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

`function_function_nbr_sem` is a DB2 user-defined function in the `fra_3000h` schema of `testdb`. The name indicates it computes a weekly count or number ("nbr" for number, "sem" likely abbreviating the French "semaine" for week), operating on hourly granularity data within the FRA domain. Like its sibling `function_function_nbr_jou`, it reads from one upstream source and likely derives a weekly numeric value from an underlying data table or reference object.

## Complexity Analysis

Complexity rating: 1S. Simple function with minimal logic — a straightforward numeric calculation or lookup returning a weekly count value with no complex branching or transformation. Total relationships: 1. Read dependencies: 1. Called by: 0.

## Dependencies

### Upstream (Sources)

This object reads from 1 source(s). MCP enrichment was not available to retrieve specific dependency names.

### Downstream (Consumers)

No downstream consumers detected.

## Additional Details

| Property | Value |
|----------|-------|
| **Object ID** | 0ad463dd-56ce-45a9-8dd2-a04e99e44dc8 |
| **Cluster ID** | N/A |
| **Duplicate Count** | N/A |
| **Similar Objects** | N/A |
| **Load Date** | 2026-02-20T09:24:08.187650 |

> **Note:** MCP enrichment was not available during generation. Code/DDL, detailed complexity breakdown, and specific dependency names could not be retrieved.
