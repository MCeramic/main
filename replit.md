# Replit Configuration for Facebook Messenger Bot

## Overview

This is a Facebook Messenger bot application built with Python Flask, designed to provide product information and customer support for ARDEX construction products. The bot is currently configured for deployment on Render platform and integrates with Facebook's Messenger API to handle customer inquiries about construction materials, adhesives, and related products.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

The application follows a simple monolithic architecture pattern:

- **Backend Framework**: Flask (Python web framework)
- **Deployment Platform**: Render (cloud platform)
- **Integration**: Facebook Messenger API
- **Data Storage**: JSON file-based product catalog
- **Logging**: File and console-based logging system

## Key Components

### 1. Flask Web Server
- **Purpose**: Handles HTTP requests and webhook endpoints for Facebook Messenger
- **Main Routes**:
  - `/` - Health check endpoint
  - `/images/<path>` - Static image serving (incomplete implementation)
  - Webhook endpoints for Facebook Messenger (implied but not visible in current code)

### 2. Product Catalog System
- **File**: `products.json`
- **Purpose**: Contains ARDEX construction product information
- **Structure**: JSON array with product objects containing:
  - `name`: Product identifier
  - `description`: Product details
  - `application`: Use cases and applications
  - `category`: Product classification

### 3. User Tracking System
- **Components**: 
  - `seen_users` dictionary for user session management
  - `processed_events` dictionary for event deduplication
- **Purpose**: Prevent duplicate message processing and maintain user context

### 4. Logging System
- **Dual Output**: Both file (`bot.log`) and console logging
- **Level**: DEBUG level for comprehensive monitoring
- **Purpose**: Track bot interactions and troubleshoot issues

## Data Flow

1. **Incoming Messages**: Facebook sends webhook requests to Flask endpoints
2. **Event Processing**: Bot checks for duplicate events using `processed_events`
3. **User Management**: Bot tracks users in `seen_users` dictionary
4. **Product Queries**: Bot searches `products.json` for relevant information
5. **Response Generation**: Bot formulates responses and sends via Facebook API
6. **Image Serving**: Static images served through `/images/` endpoint

## External Dependencies

### Facebook Messenger Platform
- **Integration**: Webhook-based communication
- **Authentication**: 
  - `PAGE_ACCESS_TOKEN` for API calls
  - `VERIFY_TOKEN` for webhook verification
- **Purpose**: Primary communication channel with users

### Render Platform
- **URL**: `https://main-owe4.onrender.com`
- **Purpose**: Cloud hosting and deployment
- **Configuration**: Static server URL (no dynamic discovery)

### Python Libraries
- **Flask**: Web framework
- **requests**: HTTP client for Facebook API calls
- **difflib**: Text similarity matching (likely for product search)
- **datetime**: Time-based operations
- **logging**: Application monitoring

## Deployment Strategy

### Environment Configuration
- **Platform**: Render cloud platform
- **URL**: Static configuration (`https://main-owe4.onrender.com`)
- **Environment Variables**:
  - `PAGE_ACCESS_TOKEN` (with fallback)
  - `VERIFY_TOKEN` (with fallback)
  - `SERVER_URL` (with fallback)

### Token Management
- Tokens are configured with environment variables
- Fallback values provided for development (should be removed in production)
- Facebook API tokens required for messenger integration

### Current Issues
- Hardcoded tokens visible in code (security concern)
- Incomplete image serving implementation
- Missing main webhook endpoint implementations
- No database persistence (relies on in-memory dictionaries)

### Architecture Decisions

**Problem**: Product information storage
**Solution**: JSON file-based catalog
**Rationale**: Simple, lightweight solution for small product catalog
**Alternatives**: Database storage (PostgreSQL, MongoDB)
**Pros**: Easy to update, version control friendly, no database overhead
**Cons**: Limited scalability, no concurrent update protection

**Problem**: User session management
**Solution**: In-memory dictionaries
**Rationale**: Simple implementation for prototype/development
**Alternatives**: Redis, database sessions, stateless design
**Pros**: Fast access, simple implementation
**Cons**: Data loss on restart, memory usage concerns, no horizontal scaling

**Problem**: Deployment platform
**Solution**: Render with static URL configuration
**Rationale**: Simple deployment, built-in HTTPS
**Alternatives**: Heroku, AWS, Docker containers
**Pros**: Easy setup, managed infrastructure
**Cons**: Platform lock-in, limited configuration options
