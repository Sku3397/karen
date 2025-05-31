# Authentication Service Documentation

This document outlines the OAuth 2.0 and JWT token-based authentication system implemented for the AI Handyman Secretary Assistant project.

## OAuth 2.0 Service

The `OAuthService` class in `src/auth/oauth_service.py` is responsible for obtaining tokens via the Client Credentials flow.

## JWT Service

The `JWTService` class in `src/auth/jwt_service.py` handles the encoding and decoding of JWT tokens, which are used for authenticating users after they have obtained an OAuth token.

## Authentication Helpers

`src/auth/auth_helpers.py` contains utility functions for validating tokens and retrieving current user information based on the token.