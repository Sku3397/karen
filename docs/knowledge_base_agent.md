# Knowledge Base Agent

## Overview
The Knowledge Base Agent provides an API for accessing technical repair knowledge, tool/material recommendations, cost estimation, safety guidelines, and relevant learning resources for handyman and repair tasks.

See the [API Design](api_design.md) for a full list of endpoints and security requirements.

## Endpoints
- `/knowledge-base/repair-knowledge` - Query technical repair articles
- `/knowledge-base/recommend-tools-materials` - Get tool/material recommendations by task type
- `/knowledge-base/estimate-cost` - Estimate cost for a specified task
- `/knowledge-base/safety-guidelines` - Safety guidelines for a repair task
- `/knowledge-base/learning-resources` - Learning resources for a topic

## Authentication & Security
- All endpoints require JWT authentication and RBAC (see [Authentication](authentication.md) and [Security](security.md)).
- Input validation is enforced via Pydantic schemas.
- See [Security and Validation](security_and_validation.md) for error handling and best practices.

## Extensibility
- Knowledge base data source can be swapped for a real database or external API.
- Schemas and endpoints can be extended to support more task types and languages.
