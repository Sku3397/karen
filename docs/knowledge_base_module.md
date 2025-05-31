# Knowledge Base Management Module

## Overview
This module provides an agent for managing handyman procedures, pricing, client history, and FAQs, backed by Google Firestore. It supports real-time updates, role-based access, and learning from interactions (e.g., auto-generating FAQs from repeated user questions).

## Features
- CRUD operations for procedures, pricing, client history, FAQs
- Role-based access control (admin, agent, viewer)
- Learning from new interactions (auto-generating FAQs)
- Firestore-backed persistence
- Easy extension for more document types

## Usage
- Integrate `KnowledgeBaseAgent` in backend service
- Use methods for managing procedures, pricing, FAQs, and client history
- Call `learn_from_interaction(client_id, interaction)` after user sessions to update history and grow the knowledge base

## Security
- Enforced role-based access control on all operations
- Firestore security rules recommended for deeper enforcement

## Testing
- See `tests/test_knowledge_base_agent.py` for CRUD and learning flow tests
