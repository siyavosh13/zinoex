# Zinoex

Zinoex is an AI-powered contract intelligence platform designed to help users generate professional legal contracts, review existing agreements, and assess potential contractual risks using artificial intelligence.

The project combines contract drafting, contract review, risk analysis, and user management features in a web-based application.

---

## Overview

Zinoex provides tools for working with legal documents in a smarter and more structured way. It is designed to assist users in creating customized contracts, reviewing contract content, identifying potential risks, and improving the quality and clarity of legal agreements.

The platform uses AI-based services to analyze contract-related information and provide intelligent assistance during contract creation and review.

---

## Key Features

### AI Contract Generation

Zinoex allows users to generate professional contracts based on structured questions and user-provided information.

The contract generation system can help create customized agreements by collecting relevant details and drafting contract text accordingly.

### Contract Review

Users can submit or review contract content to identify important clauses, missing information, unclear language, or potentially problematic sections.

The review feature helps users better understand the structure and quality of a contract before using or signing it.

### Risk Assessment

Zinoex includes AI-assisted risk analysis for contracts. It can help evaluate the level of risk associated with contract terms, clauses, or missing protections.

This feature is intended to support better decision-making by highlighting areas that may require attention.

### AI-Powered Contract Chat

The platform includes contract-focused chat intelligence that helps users interact with contract-related data, ask questions, and receive AI-assisted explanations or drafting support.

### User Authentication

Zinoex includes authentication features such as signup, login, and email verification.

### User Dashboard

Users can access a dashboard to manage their activities, contracts, subscription status, and profile information.

### Admin Dashboard

The project includes administrative tools for managing users, activities, and platform-level data.

### Subscription Management

Zinoex includes subscription-related functionality to support different access levels or service plans.

### Blockchain-Related Utilities

The project contains blockchain-related modules that may be used for contract verification, registry, or blockchain-based contract utilities.

---

## Project Structure
```text
zinoex/
│
├── app/
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── models/
│   ├── routers/
│   ├── schemas/
│   ├── services/
│   └── utils/
│
├── frontend/
│   ├── zinoex-index.html
│   ├── login.html
│   ├── signup.html
│   ├── dashboard-with-subscription.html
│   ├── contract-generation-page.html
│   ├── contract-review.html
│   ├── admin-dashboard.html
│   └── api.js
│
├── .gitignore
└── README.md

---

## Backend

The backend is built with Python and provides API routes for authentication, contract handling, dashboard features, profile management, subscription management, blockchain utilities, and AI-powered contract services.

Main backend modules include:

- Authentication
- Contract generation
- Contract review
- Contract chat
- User profile management
- Subscription handling
- Admin management
- Blockchain-related services
- AI service integration

---

## Frontend

The frontend consists of HTML and JavaScript files that provide the user interface for:

- Landing page
- Signup and login
- Email verification
- User dashboard
- Profile management
- Contract generation
- Contract review
- Admin dashboard
- Blockchain page
- Legal pages such as privacy policy, terms, disclaimer, and cookie policy

---

## Environment Variables

This project uses environment variables for sensitive configuration values.

Create a `.env` file in the project root or backend environment and define the required variables.

Example:

env
OPENAI_API_KEY=your_openai_api_key
SECRET_KEY=your_secret_key
DATABASE_URL=your_database_url

> Important: Never commit your `.env` file or real API keys to GitHub.

A safe `.env.example` file can be added to show required variables without exposing secrets.

---

## Security Notice

Sensitive information such as API keys, access tokens, database passwords, and secret keys must not be stored directly in the source code.

Use environment variables instead.

Recommended ignored files:

gitignore
.env
.env.*
*.db
*.sqlite3
__pycache__/
venv/
.venv/

---

## Installation

Clone the repository:

bash
git clone https://github.com/siyavosh13/zinoex.git
cd zinoex

Create and activate a virtual environment:

bash
python -m venv venv

On Windows:

bash
venv\Scripts\activate

On macOS/Linux:

bash
source venv/bin/activate

Install backend dependencies:

bash
pip install -r app/requirements.txt

---

## Running the Application

Run the backend server:

bash
uvicorn app.main:app --reload

The API should be available at:

text
http://127.0.0.1:8000

API documentation may be available at:

text
http://127.0.0.1:8000/docs

The frontend files can be opened directly in the browser or served through a static file server, depending on the final deployment setup.

---

## Main Use Cases

Zinoex can be used for:

- Drafting professional contracts using AI
- Reviewing existing legal agreements
- Detecting unclear or risky contract clauses
- Estimating contract risk level
- Managing user contract-related activities
- Providing AI-based legal document assistance

---

## Disclaimer

Zinoex is an AI-assisted contract intelligence tool. It is designed to help with contract drafting, review, and risk identification.

It does not replace professional legal advice. Users should consult a qualified legal professional before relying on any generated or reviewed contract for legal, business, or financial decisions.

---

## Roadmap

Planned or possible future improvements:

- Advanced contract templates
- Multi-language contract generation
- PDF/DOCX export
- More detailed risk scoring
- Clause comparison
- Contract version history
- Team collaboration features
- Payment gateway integration
- Improved admin analytics
- Deployment-ready frontend/backend configuration

---

## License

This project is currently under development.

License information can be added later.

