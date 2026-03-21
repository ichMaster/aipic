---
description: Generate markdown documentation for each record in a selected .inv file. Saves to documentation/ folder.
argument-hint: [path/to/file.inv]
allowed-tools: [Read, Write, Bash, Glob, Grep, TodoWrite, mcp__analytics-mcp-server-sapbo__tl_asmt_query_db, mcp__analytics-mcp-server-sapbo__tl_asmt_query_etl, mcp__analytics-mcp-server-sapbo__tl_asmt_query_bi, mcp__analytics-mcp-server-sapbo__tl_inv_extract_object_code, mcp__analytics-mcp-server-sapbo__tl_ln_explore_neighbors, mcp__analytics-mcp-server-sapbo__tl_anly_query_cplx]
---

# Generate Inventory Documentation

Reads a selected `.inv` file (JSON array of records), detects inventory type, enriches each record with data from migVisor MCP tools, and generates a markdown documentation file per record in the `documentation/` folder.

## Arguments

The user provided: $ARGUMENTS

If $ARGUMENTS contains a file path, use it. Otherwise proceed to Step 1.

## Execution

### Step 1 — Select the .inv file

If no file was provided as argument, list `.inv` files:

```bash
find . -name "*.inv" -maxdepth 2
```

Ask the user to pick one.

### Step 2 — Load and detect type

Read the selected `.inv` file (it's a JSON array). Detect the inventory type from the filename prefix:

- `db_` → DB inventory (name field: `object_name`, type field: `object_type`)
- `etl_` → ETL inventory (name field: `pipeline_item_name`, type field: `platform_item_type`)
- `bi_` → BI inventory (name field: `object_name`, type field: `object_type`)

If prefix doesn't match, ask the user which type it is.

Count the records and confirm with the user before proceeding:
```
Found <N> records of type <type> in <filename>. Generate documentation for all? (yes/no)
```

### Step 3 — Create output folder

```bash
mkdir -p documentation
```

### Step 4 — Process each record

Use TodoWrite to track progress. Create one task per record using the object name.

For each record in the file:

1. Mark the record's task as `in_progress`.

2. **Extract the object name** for the filename:
   - DB/BI: use `object_name` field
   - ETL: use `pipeline_item_name` field
   - Sanitize the name for filesystem use (replace spaces, slashes, special chars with underscores)

3. **Enrich with MCP data** — fetch additional details using the record's `object_id`:

   For **DB inventory** objects:
   - Call `tl_asmt_query_db` with `object_id` and `include_details=true` to get full assessment
   - Call `tl_inv_extract_object_code` with `object_id` to get code/DDL (for procedures, views, functions, triggers)
   - Call `tl_ln_explore_neighbors` with `object_id` to get upstream/downstream dependencies
   - Call `tl_anly_query_cplx` with `object_id` to get complexity breakdown

   For **ETL inventory** objects:
   - Call `tl_asmt_query_etl` with `object_id` and `include_details=true`
   - Call `tl_ln_explore_neighbors` with `object_id` to get data flow connections
   - Call `tl_anly_query_cplx` with `object_id` to get complexity breakdown

   For **BI inventory** objects:
   - Call `tl_asmt_query_bi` with `object_id` and `include_details=true`
   - Call `tl_ln_explore_neighbors` with `object_id` to get data sources
   - Call `tl_anly_query_cplx` with `object_id` to get complexity breakdown

   Make MCP calls in parallel where possible. If any MCP call fails, continue with available data.

4. **Generate the markdown file** — write to `documentation/<sanitized_object_name>.md` using this template:

```markdown
# <object_name>

## Overview

| Property | Value |
|----------|-------|
| **Type** | <object_type or platform_item_type> |
| **Technology** | <technology_name> |
| **Complexity** | <complexity> |
| **Schema/Folder** | <schema_name or folder> |
| <any other key fields from the record> | <values> |

## Description

<Generate a 2-3 sentence description of what this object does based on its name, type, and any available code or metadata. If code_text is available, analyze it to describe the object's purpose.>

## Complexity Analysis

<If complexity data was retrieved, list the complexity attributes and their values. Explain what drives the complexity rating.>

## Dependencies

### Upstream (Sources)
<List objects that this object reads from, based on lineage neighbors with "incoming" direction. Format as a bullet list with object name and type.>

### Downstream (Consumers)
<List objects that read from this object, based on lineage neighbors with "outgoing" direction. Format as a bullet list with object name and type.>

## Code

<If code_text/DDL was retrieved, include it in a fenced code block with appropriate language tag (sql, etc.). If no code is available, omit this section entirely.>

## Additional Details

<Include any remaining fields from the original record that weren't covered above, formatted as a key-value table. Omit fields with null/empty values. Omit this section if no additional fields remain.>
```

5. Mark the record's task as `completed`.

### Step 5 — Summary

After processing all records, print a summary:
```
Documentation generated for <N> records.
Output folder: documentation/
Files created:
  - <filename1>.md
  - <filename2>.md
  ...
```

## Rules

- Always sanitize filenames: replace `/`, `\`, `:`, `*`, `?`, `"`, `<`, `>`, `|`, spaces with `_`. Lowercase the filename.
- If a documentation file already exists, overwrite it.
- If an object has no `object_id`, skip MCP enrichment and generate documentation from the record data only.
- Keep MCP calls efficient: use `include_details=true` to get all data in one call where possible.
- If MCP server is unavailable, generate documentation from the .inv record data only and note that enrichment was skipped.
- Do not stop on individual record failures — log the error and continue with the next record.
