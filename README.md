# FoodShield AI: Agentic Refund Fraud Verification System

FoodShield AI is an agentic AI system designed to verify food delivery refund complaints by combining conversational complaint intake, visual evidence analysis, AI-image manipulation risk detection, customer refund history, and evidence-based decision routing.

The system simulates how a food delivery platform could handle refund claims more intelligently instead of approving or rejecting complaints based on a single signal.

---

## Project Overview

Customers may submit refund complaints such as:

* “I found hair in my food.”
* “I received the wrong item.”
* “One item is missing.”
* “The food was spoiled.”
* “The uploaded image looks suspicious.”

FoodShield AI processes these complaints through multiple specialized agents. Each agent handles one responsibility, and the final decision is made only after combining all available evidence.

---

## Key Features

* Conversational complaint intake using an LLM
* Message memory during the intake conversation
* Order and refund history lookup using SQLite
* Gemini Vision analysis for food and issue verification
* Hugging Face AI-image detector for manipulation risk scoring
* LangGraph-based agent workflow
* Human-in-the-loop escalation support
* Streamlit user interface
* Evidence-based final decision: APPROVE, REJECT, ESCALATE, or ASK_MORE_EVIDENCE

---

## Tech Stack

* Python
* Streamlit
* LangGraph
* LangChain
* Groq LLM
* Gemini Vision
* Hugging Face Transformers
* PyTorch
* SQLite
* Pydantic

---

## System Architecture


User Complaint + Order ID
        ↓
Intake Agent
- Understands complaint
- Asks follow-up questions
- Collects issue, food item, and photo
        ↓
Database Tool
- Fetches order details
- Fetches refund history
        ↓
Vision Agent
- Uses Gemini Vision to analyze uploaded food image
- Checks whether the claimed issue is visible
- Checks whether the food matches the complaint
        ↓
Hugging Face AI Image Detector
- Estimates whether the image may be AI-generated or manipulated
        ↓
Decision Agent
- Combines claim, image evidence, manipulation risk, and refund history
- Produces final decision
        ↓
APPROVE / REJECT / ESCALATE / ASK_MORE_EVIDENCE


---

## Agents

### 1. Intake Agent

The intake agent acts like a real food delivery support chatbot. It talks to the customer until all required complaint details are collected.

It extracts:

* Claimed issue
* Issue type
* Foreign object, if applicable
* Food item being complained about
* Image upload confirmation

Example:

User: I found hair in my food.
Bot: Which food item had the hair?
User: Chicken Biryani.
Bot: Please upload a clear photo showing the issue.

The intake agent uses message memory only during complaint collection. Later agents do not depend on raw conversation history.

---

### 2. Vision Agent

The vision agent uses Gemini Vision to analyze the uploaded complaint image.

It checks:

* What food is visible
* Whether the claimed issue is visible
* Whether the food matches the claimed item
* Whether there are visible signs of manipulation
* Vision confidence score

---

### 3. Hugging Face AI Image Detector

A pretrained Hugging Face image classification model is used to estimate AI-generated or manipulated image risk.

Model used:


dima806/ai_vs_real_image_detection


The detector output is treated only as a risk signal, not final proof of fraud.

Example:

FAKE score: 0.89
Manipulation risk: high


---

### 4. Decision Agent

The decision agent combines all signals and produces the final verdict.

Signals considered:

* Refund history
* Claim-image match
* Food match
* Issue visibility
* Manipulation risk
* Vision confidence

Possible decisions:

APPROVE
REJECT
ESCALATE
ASK_MORE_EVIDENCE


The system avoids rejecting a claim based on only one signal.

---

## Example Use Case


Customer complaint:
"I found hair in my food."

Bot:
"Which food item had the hair?"

Customer:
"Chicken Biryani."

Bot:
"Please upload a clear photo showing the issue."

System:
- Gemini checks whether biryani and hair are visible.
- Hugging Face estimates AI-image risk.
- Database checks refund history.
- Decision agent gives final decision.


---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/muthuprakash23/foodShield-ai-refund-fraud-detector.git
cd foodShield-ai-refund-fraud-detector
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

### 3. Activate the virtual environment

For Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

## Environment Variables

Create a `.env` file in the project root.

```env
GROQ_API_KEY=your_groq_api_key
GEMINI_API_KEY=your_gemini_api_key
```

The `.env` file is ignored using `.gitignore` and should not be committed.

## Database Setup

A sample SQLite database is included for demo/testing. To regenerate the database, run:

```bash
python database/seed.py
```

## Run the Application

```bash
streamlit run main.py
```


---

## System Architecture

```text
User Complaint + Order ID
        ↓
Intake Agent
        ├── Understands complaint
        ├── Asks follow-up questions
        └── Collects issue, food item, and photo
        ↓
Database Tool
        ├── Fetches order details
        └── Fetches refund history
        ↓
Vision Agent
        ├── Uses Gemini Vision to analyze uploaded food image
        ├── Checks whether the claimed issue is visible
        └── Checks whether the food matches the complaint
        ↓
Hugging Face AI Image Detector
        └── Estimates whether the image may be AI-generated or manipulated
        ↓
Decision Agent
        ├── Combines claim, image evidence, manipulation risk, and refund history
        └── Produces final decision
        ↓
APPROVE / REJECT / ESCALATE / ASK_MORE_EVIDENCE
```


---

## Why This Project Is Agentic

FoodShield AI is not a simple chatbot or single model classifier. It uses multiple specialized agents with clear responsibilities.

* Intake agent collects missing information.
* Vision agent verifies image evidence.
* AI-image detector estimates manipulation risk.
* Decision agent combines all evidence.
* LangGraph controls routing between agents.

This makes the system explainable, modular, and closer to real-world AI workflow design.

---

## Important Limitations

* The AI-image detector is not treated as final proof.
* Gemini Vision may fail if the image is unclear.
* The SQLite database is used for demo purposes.
* The current version is a prototype and not a production fraud detection system.
* Human review is recommended for uncertain or high-risk cases.

---

## Author

Muthu Prakash L.
