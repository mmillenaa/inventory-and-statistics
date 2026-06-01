# Inventory and Statistics of GPDVE Collections

A local Streamlit application for consolidating, exploring, and analysing structured archival metadata, enabling transversal statistical generation across collections. Designed for cataloguing and archival description, it supports the management of photographic archives and primary written sources in compliance with national and international archival standards, including CONARQ, NOBRADE, and ISAD(G).
<img src="https://github.com/user-attachments/assets/73c92635-287d-4530-afeb-9015b83f2d13" width="622" height="298" />
<img src="https://github.com/user-attachments/assets/deda2963-0170-4e98-bd36-b51bdb71b0be" width="624" height="150" />
<img src="https://github.com/user-attachments/assets/69e3fed4-204c-449a-9f24-38757b2140d0" width="487" height="249" />

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
