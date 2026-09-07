# Sprint 01 Documentation & Progress Log

**Project:** AI Contract Intelligence & Negotiation Assistant  
**Sprint Window:** September 1 – September 14, 2026  
**Maintained by:** GitHub & Documentation Lead (`@hursh26`) & Scrum Master (`@komal1304`)  

---

## 1. Sprint Goals

1. **Repository Setup & Governance:** Establish branching strategy (`develop`, `main`), automated reviewer rules via `CODEOWNERS`, and CI GitHub Actions (`ci.yml`).
2. **Backend Foundation & Upload API:** Build core FastAPI structure, file validation (magic-byte sniffing, size limits, path sanitization), contract storage, and basic text extraction.
3. **NLP/ML Pipeline Contract Alignment:** Design database schema and endpoints (`PATCH /api/v1/contracts/{id}/extraction`) to allow NLP/ML services to submit clause analysis.
4. **Automated Testing:** 100% test passing rate across Linux, Windows, and macOS test runners.

---

## 2. Team Allocations & Ownership

| Subsystem | Team Members | PR / Status |
|---|---|---|
| **Scrum Master** | Komal Bhogale (`@komal1304`) | Managing sprint backlog & issue tracking |
| **NLP & ML Team** | Jay Ashar (`@JAY-ASHAR`), Srushti Kadam (`@shrushtik44-lab`), Omkar Nikam (`@Omyy786`), Vinayak Mahindrakar (`@abyaskar`) | Preparing clause classification & risk scoring models |
| **Backend AI Team** | Viraj Mhadgut (`@virajm7`), Kuldeep Pandey (`@hursh26`) | **Completed:** Contract Upload & Extraction API |
| **UI/UX & Frontend** | Siddhi Lakade (`@siddhilakade`), Ayush Yadav (`@Aayushyadv`) | Coordinating API contract for contract upload UI |
| **Testing Team** | Srushtee Talekar (`@srushteetalekar`), Ahmed Khan (`@parve1`), Aastha Sonawane (`@Aastha2005`) | Test suite verification across platforms |
| **GitHub & Docs** | Kuldeep Pandey (`@hursh26`) | Repository workflow guide, CODEOWNERS, & Sprint Logs |

---

## 3. Merged PRs & Deliverables

### PR #1: Backend Contract Upload, Validation, and Storage API
* **Author:** `@virajm7`
* **Reviewer:** `@hursh26`
* **Branch:** `feature/backend-upload-validate-store` -> `develop`
* **Key Features:**
  - `POST /api/v1/contracts/upload`: Accepts PDF, DOCX, and TXT files.
  - `POST /api/v1/contracts/{id}/extract`: Raw text extraction (PyMuPDF / `python-docx`).
  - `PATCH /api/v1/contracts/{id}/extraction`: Endpoint for NLP/ML pipeline payload.
  - Magic-byte signature validation (`%PDF-`, `PK\x03\x04`).
  - Path traversal sanitization for `/` and `\`.
  - 16 passing unit tests in `backend/tests/`.

---

## 4. Retrospective & Lessons Learned

* **Reviewer Routing:** Updated `.github/CODEOWNERS` to assign `@hursh26` as reviewer for `/backend/` PRs following team roster changes.
* **CI Verification:** Cross-platform CI tests passed across Windows, Linux, and macOS runners.
