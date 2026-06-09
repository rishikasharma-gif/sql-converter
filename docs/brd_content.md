# Business Requirement Document (BRD): SQL CONVERTER

## Tool Overview
The purpose of the SQL Converter Tool is to automate the conversion of SAP HANA Calculation Views and Composite Providers (XML-based models) into optimized BigQuery SQL scripts for migration into Dataform.
The tool will reduce manual effort, minimize data loss risks, improve migration accuracy and accelerate SAP to BigQuery transformation activities.

## Goal / Business Objectives
The primary objective of this tool is to solve the following business problems:
- **Manual Conversion Effort**: Eliminates repetitive manual rewriting of SAP Calculation Views and Composite Providers into BigQuery SQL.
- **Faster Migration**: Accelerates SAP-to-BigQuery migration activities by automating XML-to-SQL conversion.
- **Data Loss Prevention**: Ensures SAP business logic is preserved accurately during migration with minimal data loss.
- **SQL Optimization**: Generates optimized BigQuery SQL to improve query performance and scalability.
- **Dataform Integration**: Provides direct export functionality into Dataform Silver Layer with one-click file generation.

## Scope & Feature Priorities

| Feature | Description | Priority | Phase |
| :--- | :--- | :--- | :--- |
| **XML Parsing Engine** | Extract joins, filters, calculations, and metadata | High | MVP |
| **SQL Conversion Engine** | Convert SAP logic into BigQuery SQL | High | MVP |
| **SQL Optimization** | Optimize generated SQL for BigQuery | Medium | 2nd Phase |
| **Validation Engine** | Detect unsupported logic and reduce data loss | High | MVP |
| **Dataform Export** | Export generated SQL into Dataform Silver Layer | Low | Future Phase |
| **Bulk File Processing** | Support multiple XML files simultaneously | Medium | Future Phase |

## Pre-requisites
From Data Engineering (DE) to AI Team:
To generate accurate SQL conversion outputs, the converter requires the following inputs:
- **SAP Calculation View XML Files**: XML-based SAP Calculation Views containing transformation logic.
- **Composite Provider XML Files**: SAP Composite Provider structures and metadata.

## Challenges / Blockers
- **Complex SAP Logic**: Some SAP transformations may be highly nested or customized.
- **Unsupported Functions**: Certain SAP-specific functions may not directly map to BigQuery.
- **XML Inconsistencies**: Different XML structures may impact parsing accuracy.
- **Data Validation Complexity**: Complex transformations require extensive validation.
- **Manual Dependencies**: Some custom logic may still require manual intervention.
- **Performance Optimization**: Large transformations may require advanced optimization.

## Success Metrics
- **Conversion Accuracy**: 95%+ SAP logic correctly converted into BigQuery SQL.
- **Data Preservation**: Minimal data loss during conversion ideally less than 1%.
- **Migration Efficiency**: Reduction in manual conversion effort.
- **SQL Performance**: Optimized queries executing efficiently in BigQuery.
- **Dataform Integration**: Successful one-click export into Silver Layer (Future Phase).

## Revised Timelines / Delivery Plan

| Phase | Focus | Output | Estimated Timeline |
| :--- | :--- | :--- | :--- |
| **Phase 1: Requirement Gathering** | Understand SAP XML structures and migration standards | Requirement Documentation | TBD |
| **Phase 2: Parser Development** | Build XML parsing engine | XML Metadata Extraction Engine | TBD |
| **Phase 3: SQL Conversion** | Build SAP-to-BigQuery conversion logic | Functional MVP Converter | TBD |
| **Phase 4: Optimization & Validation** | SQL optimization and validation framework | Optimized SQL Outputs | TBD |
| **Phase 5: Dataform Integration** | One-click export into Silver Layer | Integrated Deployment Flow | TBD |
| **Phase 6: Production Deployment** | End-to-end deployment and testing | Production Ready Tool | TBD |
