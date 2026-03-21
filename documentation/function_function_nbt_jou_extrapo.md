# function_function_nbt_jou_extrapo

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

`function_function_nbt_jou_extrapo` is a DB2 user-defined function residing in the `fra_3000h` schema, likely responsible for extrapolating journal entry counts (NBT JOU suggesting "nombre de journaux" or a journal numbering context). Based on the name, it performs a numerical extrapolation calculation derived from journal-related data. It operates in a read-only capacity, consuming data from two source objects to produce its result.

## Complexity Analysis

Complexity rating: 2M. Medium complexity driven by the extrapolation logic that likely involves arithmetic or statistical operations across multiple input sources. Total relationships: 2. Read dependencies: 2. Called by: 0.

## Dependencies

### Upstream (Sources)

This object reads from 2 source(s). MCP enrichment was not available to retrieve specific dependency names.

### Downstream (Consumers)

No downstream consumers detected.

## Additional Details

| Property | Value |
|----------|-------|
| **Object ID** | 192bd8c9-a8bb-44ea-972c-6f2bc8f5626a |
| **Cluster ID** | N/A |
| **Duplicate Count** | N/A |
| **Similar Objects** | N/A |
| **Load Date** | 2026-02-20T09:24:08.187650 |

> **Note:** MCP enrichment was not available during generation. Code/DDL, detailed complexity breakdown, and specific dependency names could not be retrieved.
