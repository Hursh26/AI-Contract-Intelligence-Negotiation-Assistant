# Changelog

All notable changes to this project are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versioning follows [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added
- **Backend AI REST API**: Contract upload endpoint (`POST /api/v1/contracts/upload`) with file validation (`@virajm7`).
- **File Validation & Security**: Magic-byte signature checking (`%PDF-`, `PK\x03\x04`) and dual-separator (`/` and `\`) path-traversal sanitization (`@virajm7`).
- **Text Extraction API**: Raw text extraction endpoint (`POST /api/v1/contracts/{id}/extract`) for PDF (PyMuPDF), DOCX (python-docx), and TXT (`@virajm7`).
- **NLP/ML Contract Integration**: Clause & extraction persistence endpoint (`PATCH /api/v1/contracts/{id}/extraction`) (`@virajm7`).
- **CI/CD Pipeline**: Multi-platform automated backend tests on Ubuntu, Windows, and macOS GitHub Actions runners (`@virajm7`, `@hursh26`).
- **Repository Governance**: Automated reviewer assignment via `CODEOWNERS` and team workflow guide `team-github-workflow-guide.md` (`@hursh26`, `@komal1304`).

### Changed
- Updated `CODEOWNERS` backend reviewer mapping to `@hursh26` following team roster update (`@hursh26`).

---

## [0.1.0] - 2026-09-07
### Added
- Initial project scaffold (repo structure, CI, docs, templates)
