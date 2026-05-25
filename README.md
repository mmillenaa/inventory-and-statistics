# Inventory and Statistics of GPDVE Collections

A local Streamlit application for consolidating, exploring, and analysing archival metadata from structured spreadsheet collections.

## Project Status

**Functional early-stage release — under active development**

This repository contains a working version of the application with core features already implemented. It is being published now for evaluation purposes, but development is ongoing and further improvements are planned.

## What This Project Does

The application was designed to support archival inventory workflows and transversal metadata analysis from spreadsheet-based sources. It allows users to load multiple Excel files, search and filter records, generate statistical views, and export a structured inventory document.

## Main Features

- Consolidates multiple Excel spreadsheets into a single working dataset
- Performs full-text search across indexed metadata
- Applies categorical filters to document records
- Displays key metrics and collection-level indicators
- Generates timeline and thematic visualisations
- Exports filtered records to a `.docx` inventory
- Includes a multilingual interface (Portuguese / English / Spanish)
- Queries institutional data published on Dataverse

## Run Locally

### Requirements

- Python 3.10+
- Streamlit
- Pandas
- Plotly
- python-docx
- Requests
- Openpyxl

### Install

```bash
git clone https://github.com/your-username/your-repository.git
cd your-repository
python -m venv venv
