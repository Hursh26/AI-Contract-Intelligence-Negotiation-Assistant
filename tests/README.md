# Contract Testing Documents

## Overview

This folder contains sample legal and business contract documents used for testing the **AI Contract Intelligence & Negotiation Assistant**.

The main project is designed to help users:

* Understand complex contract language in simple terms
* Compare contract clauses and contract versions
* Ask questions about specific contract terms
* Identify important contractual information and potential issues
* Support contract negotiation by providing alternative wording and negotiation-related suggestions

The documents in this folder provide different types of contracts so that the system can be tested across multiple business and legal scenarios.

---

## Purpose of the Test Documents

The documents are used as sample inputs for testing the contract intelligence system.

Testing can cover whether the system can correctly:

1. Read and understand contract documents
2. Identify the parties involved
3. Extract important dates and durations
4. Identify financial information such as rent, fees, premiums, deposits, and payments
5. Understand contractual obligations
6. Identify termination and renewal conditions
7. Understand confidentiality requirements
8. Extract governing-law and jurisdiction information
9. Answer questions based on the content of a contract
10. Compare information between different contract types
11. Avoid generating information that is not present in the source document
12. Handle different contract structures and terminology

---

## Test Documents

The current test dataset contains the following documents:

| # | Document                                      | Contract Type                  | Main Testing Area                                                   |
| - | --------------------------------------------- | ------------------------------ | ------------------------------------------------------------------- |
| 1 | `Business_Partnership_NDA_Agreement.docx`     | Business Partnership NDA       | Confidentiality, obligations, exclusions, duration                  |
| 2 | `Commercial_Office_Rental_Agreement(1).docx`  | Commercial Rental Agreement    | Rent, lease term, deposit, maintenance, termination                 |
| 3 | `Employee_NDA_Agreement.docx`                 | Employee NDA                   | Confidential information, employee obligations, return of materials |
| 4 | `Graphic_Designer_Agreement.docx`             | Service Agreement              | Scope of work, fees, revisions, intellectual property               |
| 5 | `Health_Insurance_Agreement.docx`             | Insurance Agreement            | Coverage, premium, exclusions, claims, validity                     |
| 6 | `Product_Vendor_Agreement.docx`               | Vendor/Supply Agreement        | Products, pricing, delivery, warranty, inspection                   |
| 7 | `Residential_Apartment_Rental_Agreement.docx` | Residential Rental Agreement   | Rent, deposit, tenancy, utilities, termination                      |
| 8 | `Website_Development_Agreement.docx`          | Software/Development Agreement | Scope, milestones, payment, IP, change requests                     |

---

## 1. Business Partnership NDA

**File:** `Business_Partnership_NDA_Agreement.docx`

This document represents a confidentiality agreement between two businesses.

Important clauses include:

* Purpose of the agreement
* Definition of confidential information
* Confidentiality obligations
* Exclusions from confidential information
* No partnership or joint-venture obligation
* Return or destruction of information
* Duration of confidentiality obligations
* Remedies
* Governing law and jurisdiction

The agreement specifies a three-year confidentiality period and Mumbai, Maharashtra as the jurisdiction.

### Example test questions

* Who are the parties in the agreement?
* What information is considered confidential?
* How long do the confidentiality obligations remain effective?
* What happens to confidential information after the discussions end?
* What is the governing jurisdiction?

---

## 2. Commercial Office Rental Agreement

**File:** `Commercial_Office_Rental_Agreement(1).docx`

This document represents a commercial property lease.

Important information includes:

* Premises and office area
* Three-year lease term
* Monthly rent
* 5% annual rent escalation
* Six-month security deposit
* Utilities and maintenance
* Alterations and fit-outs
* Insurance
* Assignment and subletting
* Termination
* Renewal

The agreement specifies a monthly rent of ₹3,75,000 and a refundable security deposit of ₹22,50,000.

### Example test questions

* What is the monthly rent?
* What is the security deposit?
* How long is the lease?
* How much does the rent increase each year?
* Who is responsible for utilities?
* What notice period is required for termination?

---

## 3. Employee NDA

**File:** `Employee_NDA_Agreement.docx`

This document represents a confidentiality agreement between an employer and an employee.

Important areas include:

* Confidential information
* Employee confidentiality obligations
* Exclusions
* Return or destruction of company materials
* Duration of confidentiality
* No license to company information
* Remedies
* Governing law

The agreement states that confidentiality obligations continue for three years after employment ends, or while the information remains confidential, whichever is longer.

### Example test questions

* What information is considered confidential?
* What must the employee do when employment ends?
* How long do confidentiality obligations continue?
* Does the employee receive ownership rights over confidential information?
* What happens if the employee breaches the agreement?

---

## 4. Graphic Designer Agreement

**File:** `Graphic_Designer_Agreement.docx`

This document represents a professional services agreement between a client and a graphic designer.

Important areas include:

* Scope of work
* Deliverables
* Contract duration
* Fees and payments
* Advance payment
* Revisions
* Review and acceptance
* Software and expenses
* Intellectual property
* Assignment and subcontracting
* Termination
* Renewal

The agreement includes brand identity and logo work, social media creative work, and additional revision charges.

### Example test questions

* What services will the designer provide?
* How many revision rounds are included?
* What is the advance payment?
* Who owns the final deliverables after payment?
* What is the termination notice period?
* What are the fees for additional revisions?

---

## 5. Health Insurance Agreement

**File:** `Health_Insurance_Agreement.docx`

This document represents a health insurance policy.

Important areas include:

* Policy summary
* Premium
* Coverage
* Exclusions
* Waiting periods
* Policy validity
* Claims procedure
* Free-look period
* Cancellation
* Governing law

The policy provides a ₹10,00,000 sum insured on a floater basis and specifies a 36-month waiting period for pre-existing diseases.

### Example test questions

* What is the sum insured?
* What is the annual premium?
* What treatments are covered?
* What are the major exclusions?
* What is the waiting period for pre-existing diseases?
* How long is the policy valid?
* What is the free-look period?

---

## 6. Product Vendor Agreement

**File:** `Product_Vendor_Agreement.docx`

This document represents a buyer-vendor supply agreement.

Important areas include:

* Products
* Pricing
* Payment terms
* Security deposit
* Delivery
* Quality inspection
* Packaging and shipping
* Customization
* Warranty
* Insurance
* Termination
* Renewal

The agreement covers networking hardware such as switches, routers, and Ethernet cables.

### Example test questions

* What products are being supplied?
* What are the payment terms?
* What is the security deposit?
* Who is responsible for shipping?
* How long is the product warranty?
* How many days does the buyer have to reject non-conforming products?

---

## 7. Residential Apartment Rental Agreement

**File:** `Residential_Apartment_Rental_Agreement.docx`

This document represents a residential tenancy agreement.

Important areas include:

* Residential premises
* Tenancy period
* Monthly rent
* Security deposit
* Permitted use
* Maintenance
* Utilities
* Alterations
* Inspection
* Termination
* Renewal

The agreement specifies an 11-month tenancy, monthly rent of ₹35,000, and a refundable security deposit of ₹1,05,000.

### Example test questions

* What is the monthly rent?
* What is the rental period?
* What is the security deposit?
* Who pays utility charges?
* Can the tenant make structural changes?
* What notice period is required for termination?

---

## 8. Website Development Agreement

**File:** `Website_Development_Agreement.docx`

This document represents a software and website development agreement.

Important areas include:

* Project scope
* UI/UX design
* Front-end and back-end development
* Payment gateway integration
* CMS
* SEO
* Project milestones
* Payment structure
* Intellectual property
* Change requests
* Warranty and support
* Confidentiality
* Termination
* Limitation of liability

The project contains milestones for design, development, testing, bug fixing, and final deployment.

### Example test questions

* What is the total project fee?
* What are the payment milestones?
* What is included in the project scope?
* Who owns the custom code after final payment?
* What is the process for requesting changes?
* How long is the bug-fixing warranty?
* What is the termination notice period?

---

# Testing Categories

The documents can be used to test several capabilities of the AI Contract Intelligence & Negotiation Assistant.

## 1. Contract Understanding

Test whether the AI can explain complicated legal clauses in simple language.

**Example:**

> "Explain the termination clause in simple words."

Expected behavior:

* The response should be based on the contract.
* The response should clearly explain the relevant clause.
* The system should not add terms that are not present in the document.

---

## 2. Information Extraction

Test whether important information can be extracted from the contract.

Examples:

* Parties
* Dates
* Contract duration
* Payment amounts
* Security deposits
* Notice periods
* Renewal conditions
* Governing law

---

## 3. Question Answering

Users should be able to ask natural-language questions about a contract.

Example:

> "How much is the security deposit?"

The system should locate the relevant clause and provide the answer based on the document.

---

## 4. Clause Comparison

Different documents can be used to test comparison functionality.

For example:

**Commercial Rental Agreement vs. Residential Rental Agreement**

Possible comparison fields:

| Field              | Commercial Rental | Residential Rental |
| ------------------ | ----------------- | ------------------ |
| Contract type      | Office lease      | Apartment tenancy  |
| Rent               | ₹3,75,000/month   | ₹35,000/month      |
| Term               | 3 years           | 11 months          |
| Security deposit   | ₹22,50,000        | ₹1,05,000          |
| Termination notice | 3 months          | 1 month            |

The comparison should clearly identify which information comes from which document.

---

## 5. Contract Risk / Clause Analysis

The system can be tested on whether it identifies important contractual conditions such as:

* Termination conditions
* Payment obligations
* Confidentiality obligations
* Waiting periods
* Renewal conditions
* Intellectual-property ownership
* Liability limitations
* Warranty periods

The system should distinguish between information explicitly stated in the contract and any interpretation or suggestion.

---

## 6. Negotiation Testing

The project aims to support contract negotiation.

Possible prompts include:

> "What part of this contract could be discussed during negotiation?"

or:

> "Suggest alternative wording for this clause."

When testing negotiation functionality, responses should clearly distinguish **the original contract wording** from **AI-generated suggestions**.

---

## 7. Hallucination Testing

One important testing area is checking whether the AI invents information.

### Example

Ask:

> "What is the penalty for late delivery?"

If the contract does not specify a late-delivery penalty, the system should not invent an amount.

A suitable response would indicate that the supplied contract does not specify a particular late-delivery penalty.

---

# Test Data Coverage

The current documents provide a variety of contract scenarios:

* Business confidentiality
* Employment confidentiality
* Commercial property rental
* Residential property rental
* Graphic design services
* Health insurance
* Product supply
* Website development

This variety allows the system to be tested against different terminology, clauses, financial structures, obligations, and contract formats.

---

# Suggested Testing Workflow

A basic testing workflow can be:

```text
Upload Contract
      ↓
Document Processing
      ↓
Contract Understanding
      ↓
Information / Clause Extraction
      ↓
User Question
      ↓
Retrieve Relevant Contract Information
      ↓
Generate Answer
      ↓
Verify Answer Against Source
```

For comparison:

```text
Upload Contract A
       +
Upload Contract B
       ↓
Extract Relevant Clauses
       ↓
Compare Clauses
       ↓
Generate Comparison
       ↓
Verify Against Both Documents
```

For negotiation testing:

```text
Contract
   ↓
Identify Clause
   ↓
User Negotiation Request
   ↓
Generate Suggested Alternative
   ↓
Clearly Separate Original vs Suggested Text
   ↓
Review Result
```

---

# Expected Testing Goals

The testing documents should help the team evaluate whether the system:

* Correctly understands different contract types
* Extracts information accurately
* Answers questions using the provided contract
* Compares contract information correctly
* Handles financial values and dates correctly
* Identifies relevant clauses
* Does not hallucinate missing information
* Clearly separates source information from AI-generated suggestions
* Handles different contract structures consistently

---

# Folder Structure

The documents can be maintained in the project's `tests/` directory:

```text
tests/
├── README.md
├── Business_Partnership_NDA_Agreement.docx
├── Commercial_Office_Rental_Agreement(1).docx
├── Employee_NDA_Agreement.docx
├── Graphic_Designer_Agreement.docx
├── Health_Insurance_Agreement.docx
├── Product_Vendor_Agreement.docx
├── Residential_Apartment_Rental_Agreement.docx
└── Website_Development_Agreement.docx
```

---

# Relation to the Main Project

These documents serve as test inputs for the **AI Contract Intelligence & Negotiation Assistant**.

The main project repository separates the application into areas such as:

```text
frontend/   → User interface
backend/    → Server/API
ml/         → NLP/ML and contract analysis
tests/      → Testing and test documents
docs/       → Project documentation
```

The repository's workflow specifically identifies `/tests/` as the primary working area for the Testing Team and recommends recording hallucination and prompt-testing results in `/docs/`.

---

# Disclaimer

These documents are provided as **test/sample contracts for software testing purposes**. They should not be treated as legal advice or as a substitute for review by a qualified legal professional.
