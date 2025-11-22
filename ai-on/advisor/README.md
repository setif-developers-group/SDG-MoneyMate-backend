# Advisor Agent

The **Advisor Agent** is a specialized AI agent in the AION system that provides smart product recommendations and purchase guidance integrated with the user's budget data.

## Overview

The Advisor Agent helps users make informed purchasing decisions by:
- Analyzing their current budget and spending patterns
- Providing budget-aware product recommendations
- Evaluating if specific purchases fit their financial situation
- Comparing products to find the best option within budget constraints

## Architecture

### Components

- **`models.py`**: Defines the `AdvisorSession` model for tracking user interactions
- **`serializers.py`**: Handles request/response serialization
- **`services.py`**: Core business logic and AI integration
- **`tools.py`**: Chatbot integration tools
- **`views.py`**: API endpoints
- **`urls.py`**: URL routing

### AI Model

The Advisor Agent uses **Gemini 2.5 Flash** for intelligent product analysis and recommendations.

### System Instruction

The agent is instructed to:
- Consider user budget constraints in all recommendations
- Analyze spending patterns from expense history
- Provide honest advice about financial implications
- Suggest budget-friendly alternatives when necessary
- Prioritize the user's financial health over making purchases
- Format responses in clear, actionable Markdown

## API Endpoints

### 1. Product Recommendations

**Endpoint**: `POST /api/advisor/recommend/`

Get AI-powered product recommendations based on your budget and preferences.

**Request**:
```json
{
  "message": "Recommend a laptop for programming under 50000 DZD"
}
```

**Response**:
```json
{
  "advice": "# Laptop Recommendations for Programming\n\n## Budget Analysis\n...",
  "session_id": 123
}
```

### 2. Purchase Analysis

**Endpoint**: `POST /api/advisor/analyze-purchase/`

Analyze if a specific purchase is financially wise.

**Request**:
```json
{
  "message": "Should I buy a phone for 80000 DZD?"
}
```

**Response**:
```json
{
  "advice": "# Purchase Analysis: Phone for 80000 DZD\n\n## Financial Impact\n...",
  "session_id": 124
}
```

### 3. Product Comparison

**Endpoint**: `POST /api/advisor/compare/`

Compare multiple products and get a recommendation.

**Request**:
```json
{
  "message": "Compare iPhone 15 vs Samsung S24"
}
```

**Response**:
```json
{
  "advice": "# Product Comparison: iPhone 15 vs Samsung S24\n\n## Comparison\n...",
  "session_id": 125
}
```

### 4. Advisor History

**Endpoint**: `GET /api/advisor/history/`

Retrieve past advisor sessions and recommendations.

**Response**:
```json
[
  {
    "id": 123,
    "query_type": "recommend",
    "user_query": "Recommend a laptop...",
    "ai_response": "# Laptop Recommendations...",
    "created_at": "2025-11-22T02:00:00Z"
  }
]
```

## Integration with Other Agents

### Chatbot Integration

The Advisor Agent is fully integrated with the Chatbot Agent. Users can ask for product advice through natural conversation:

**Example Conversation**:
```
User: "I want to buy a new laptop, any recommendations?"
Chatbot: [Calls call_advisor tool]
Chatbot: "Based on your budget, here are some great options..."
```

The chatbot automatically routes product-related queries to the advisor using the `call_advisor` tool.

### Budget Integration

The advisor considers:
- User's budget categories and allocated amounts
- Current spending in each category
- Remaining budget available
- Overall financial health (income, savings, debts)

### Expense Integration

The advisor analyzes:
- Recent expense patterns
- Spending trends
- Category-wise expenditure
- Historical purchase behavior

## How It Works

1. **User Query**: User asks for product advice (via API or chatbot)
2. **Context Building**: Agent gathers user's financial profile, budgets, and recent expenses
3. **AI Analysis**: Gemini 2.5 Flash analyzes the query with financial context
4. **Response Generation**: AI generates budget-aware advice in Markdown format
5. **Session Tracking**: Interaction is saved to `AdvisorSession` for analytics

## Example Use Cases

### 1. Budget-Aware Recommendations
```
User: "Recommend a phone under 30000 DZD"
Advisor: Provides options within budget, considering user's electronics budget category
```

### 2. Purchase Validation
```
User: "Can I afford a laptop for 60000 DZD?"
Advisor: Analyzes budget impact, suggests if affordable or recommends waiting/alternatives
```

### 3. Product Comparison
```
User: "Compare MacBook Air vs Dell XPS"
Advisor: Compares features, prices, and recommends based on budget constraints
```

### 4. Alternative Suggestions
```
User: "I want the latest iPhone"
Advisor: If too expensive, suggests previous generation or alternative brands within budget
```

## Financial Context

The advisor has access to:

- **User Profile**: Income, savings, investments, debts
- **Budget Data**: All budget categories, allocated amounts, spent amounts
- **Expense History**: Recent purchases and spending patterns
- **Financial Health**: Overall budget utilization and remaining funds

This comprehensive context ensures all recommendations are financially responsible and personalized.

## Response Format

All responses are in **Markdown format** with:
- Clear headers and sections
- Bullet points for easy scanning
- Emphasis on key information
- Specific price points and budget impact
- Actionable recommendations

## Session Tracking

Every interaction is saved as an `AdvisorSession` with:
- Query type (recommend, analyze, compare)
- User's original query
- AI's response
- Timestamp

This allows for:
- Analytics on user preferences
- Improving recommendations over time
- Tracking advisor usage patterns
- Providing personalized follow-ups

## Best Practices

### For Frontend Developers

1. **Display Markdown**: Render the `advice` field as Markdown for best UX
2. **Show Context**: Display relevant budget info alongside recommendations
3. **Track Sessions**: Use `session_id` to link related queries
4. **Handle Errors**: Gracefully handle API errors with user-friendly messages

### For Users

1. **Be Specific**: Provide clear budget constraints in queries
2. **Update Budget**: Keep budget categories current for accurate advice
3. **Track Expenses**: Regular expense tracking improves recommendations
4. **Ask Follow-ups**: Use chatbot for conversational product advice

## Future Enhancements

Potential improvements:
- Price tracking and alerts
- Product review integration
- Seasonal buying recommendations
- Multi-currency support
- Deal and discount suggestions
- Long-term purchase planning
