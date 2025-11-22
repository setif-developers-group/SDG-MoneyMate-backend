# Expense Manager & Report Agent

The Expense Manager module handles multi-modal expense tracking (text, image, PDF) and generates comprehensive financial reports. It leverages **Gemini 2.5 Flash** to extract data from receipts and analyze spending habits.

## Overview

This app contains two specialized agents:
1.  **Expense Manager Agent**: Extracts expense details from user input (text or files), categorizes them, matches them to existing budgets, and detects overspending.
2.  **Report Agent**: Generates detailed Markdown financial reports by analyzing user expenses and budget goals.

## Features

-   **Multi-Modal Input**: Accepts text descriptions, receipt images, and PDF documents.
-   **AI Extraction**: Automatically identifies product name, price, category, and description from inputs.
-   **Privacy Focused**: Uploaded files are processed for data extraction and then immediately discarded; they are not stored on the server.
-   **Budget Integration**: Matches expenses to existing budget categories and updates "spent" amounts.
-   **Overspending Detection**: Real-time checks against budget limits, triggering alerts to the Main AI Coordinator.
-   **Financial Reporting**: Generates comprehensive reports comparing actual spending vs. goals.

## Architecture

### Components

1.  **services.py**: Contains the logic for `process_expense_management` and `process_report_generation`.
2.  **models.py**: Defines the `Expense` model with support for file uploads.
3.  **views.py**: API endpoints for expense creation and report generation.
4.  **serializers.py**: JSON serialization for expense data.
5.  **urls.py**: URL routing.

## API Endpoints

### POST /api/expenses/
Process a new expense.

**Request:**
-   `message` (text): Description of the expense (optional if file provided).
-   `file` (file): Receipt image or PDF (optional).

**Response:**
```json
{
  "message": "Processed 1 expenses.",
  "expenses": [
    {
      "id": 1,
      "product": "Milk",
      "amount": 150.0,
      "category": "Groceries"
    }
  ],
  "alerts": []
}
```

### GET /api/expenses/
List all user expenses.

**Response:**
```json
[
  {
    "id": 1,
    "product_name": "Milk",
    "amount": "150.00",
    "category_name": "Groceries",
    "date": "2023-10-27T10:00:00Z",
    ...
  }
]
```

### POST /api/expenses/report/
Generate a financial report.

**Request:**
```json
{
  "message": "Generate a monthly report"
}
```

**Response:**
```json
{
  "report": "# Financial Report\n\n## Summary\n..."
}
```

## Integration with Main AI

The Expense Manager is integrated with the Main AI Coordinator and Chatbot:
-   **Chatbot**: Users can upload receipts or mention expenses in chat.
-   **Main AI**: Receives alerts when overspending is detected.

## Model Configuration

-   **Model**: Gemini 2.5 Flash
-   **Capabilities**: Vision, Document Understanding, Text Analysis.
