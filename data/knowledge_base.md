# Product Team Meeting Notes - Q1 2024

## Meeting: Product Roadmap Planning
**Date:** January 15, 2024
**Attendees:** Sarah Chen (PM), Mike Johnson (Eng Lead), Lisa Park (Design), Tom Wilson (Marketing)

### Key Decisions
1. **New Feature: Advanced Search**
   - Timeline: Launch by March 2024
   - Scope: Implement semantic search using vector embeddings
   - Technical approach: Use ChromaDB for vector storage
   - Owner: Mike Johnson
   - Budget: $50,000

2. **Mobile App Redesign**
   - Timeline: Q2 2024 (April-June)
   - Focus: Improve user onboarding flow
   - Key metric: Reduce drop-off rate from 45% to 25%
   - Owner: Lisa Park
   - User testing scheduled for February

3. **API Rate Limiting**
   - Implementation: February 2024
   - Limits: 100 requests/minute for free tier, 1000 requests/minute for premium
   - Reason: Prevent abuse and ensure service stability
   - Owner: Mike Johnson

### Action Items
- Sarah: Draft PRD for Advanced Search by Jan 22
- Mike: Evaluate vector database options (ChromaDB vs Pinecone)
- Lisa: Schedule user interviews for mobile redesign
- Tom: Prepare marketing campaign for Q1 features

---

## Meeting: Engineering Sprint Planning
**Date:** January 22, 2024
**Attendees:** Mike Johnson, Dev Team (6 engineers)

### Sprint Goals (Sprint 12)
1. Complete authentication refactor
2. Implement rate limiting middleware
3. Begin Advanced Search backend work

### Technical Decisions
- **Authentication**: Switch from JWT to session-based auth for better security
- **Database**: Migrate from PostgreSQL 13 to PostgreSQL 15 for performance improvements
- **Monitoring**: Add DataDog integration for real-time performance tracking

### Blockers Identified
- ChromaDB documentation unclear on scaling
- Need design mockups for Advanced Search UI
- API gateway upgrade required before rate limiting implementation

### Capacity
- Team velocity: 40 story points
- Sprint duration: 2 weeks (Jan 22 - Feb 5)
- On-call rotation: Tom handling this sprint

---

## Meeting: Customer Feedback Review
**Date:** January 29, 2024
**Attendees:** Sarah Chen, Tom Wilson, Customer Success Team

### Top Customer Requests
1. **Dark Mode** (requested by 234 users)
   - Priority: High
   - Effort: Medium (estimated 2 weeks)
   - Target: Q2 2024

2. **Bulk Export Feature** (requested by 89 enterprise customers)
   - Priority: Critical for enterprise retention
   - Format: CSV and JSON export
   - Target: March 2024
   - Revenue impact: Potentially $200K ARR at risk

3. **Better Search** (requested by 156 users)
   - Aligns with Advanced Search initiative
   - Specific asks: Filter by date, search in attachments, save searches
   - Already planned for Q1

### Customer Pain Points
- Current search is too slow (avg 3-5 seconds)
- Mobile app crashes on older devices (iOS 13, Android 9)
- No offline mode for mobile app

### Resolution Plan
- Prioritize Bulk Export feature (move to February)
- Advanced Search should address search performance
- Mobile stability fixes scheduled for Sprint 13

---

## Technical Architecture Documentation

### Current System Architecture
**Frontend:**
- React 18.2.0
- TypeScript 5.0
- State management: Redux Toolkit
- Styling: Tailwind CSS

**Backend:**
- Node.js 20.x with Express
- PostgreSQL 15 (primary database)
- Redis (caching and session storage)
- AWS S3 (file storage)

**Infrastructure:**
- Hosted on AWS (us-east-1)
- Load balancer: AWS ALB
- CDN: CloudFront
- CI/CD: GitHub Actions

### Advanced Search Technical Spec
**Components:**
1. Embedding Generation Service
   - Model: all-MiniLM-L6-v2
   - Batch processing for historical data
   - Real-time embedding for new content

2. Vector Database
   - ChromaDB with persistent storage
   - Collection per tenant for multi-tenancy
   - Automatic backup every 6 hours

3. Search API Endpoint
   - POST /api/v2/search
   - Query parameters: query (string), limit (number), filters (object)
   - Response: ranked results with similarity scores

**Performance Targets:**
- Search latency: < 200ms (p95)
- Index update latency: < 1 second
- Support 10,000 concurrent users

---

## Product Requirements: Bulk Export Feature

### Overview
Allow users to export their data in CSV or JSON format for backup, analysis, or migration purposes.

### User Stories
1. As an enterprise user, I want to export all my project data so I can analyze it in Excel
2. As a compliance officer, I need to export audit logs in JSON format for regulatory reporting
3. As a user, I want to schedule automatic weekly exports to my email

### Functional Requirements
- Support CSV and JSON formats
- Export scopes: All data, specific project, date range, filtered data
- Maximum export size: 100MB (split into multiple files if needed)
- Include metadata: export timestamp, user info, record count

### Non-Functional Requirements
- Export generation: < 30 seconds for 10K records
- Email delivery: within 5 minutes of request
- Exports stored for 7 days before deletion
- Rate limit: 5 exports per day per user

### Technical Implementation
- Background job processing with Bull queue
- S3 storage for generated files
- Pre-signed URLs for secure download
- Email notifications via SendGrid

### Security Considerations
- Only user's own data accessible
- Audit log all export requests
- Encryption at rest and in transit
- GDPR compliance: include right to erasure

---

## API Documentation Excerpt

### Rate Limiting
All API endpoints are subject to rate limiting to ensure fair usage and system stability.

**Rate Limits by Tier:**
- Free Tier: 100 requests/minute, 10,000 requests/day
- Pro Tier: 1,000 requests/minute, 100,000 requests/day
- Enterprise Tier: Custom limits negotiated

**Response Headers:**
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1706198400
```

**429 Response Example:**
```json
{
  "error": "rate_limit_exceeded",
  "message": "Rate limit exceeded. Please retry after 60 seconds.",
  "retry_after": 60
}
```

### Authentication
**Session-based Authentication** (recommended for web apps):
1. POST /auth/login with credentials
2. Receive session cookie (httpOnly, secure)
3. Include cookie in subsequent requests
4. Session expires after 7 days of inactivity

**API Key Authentication** (for integrations):
1. Generate API key in dashboard
2. Include in header: `Authorization: Bearer YOUR_API_KEY`
3. API keys don't expire but can be revoked

### Search Endpoint (v2)
**POST /api/v2/search**

Request:
```json
{
  "query": "product roadmap",
  "limit": 10,
  "filters": {
    "type": "document",
    "date_range": {
      "start": "2024-01-01",
      "end": "2024-01-31"
    }
  }
}
```

Response:
```json
{
  "results": [
    {
      "id": "doc_123",
      "title": "Q1 Product Roadmap",
      "snippet": "...semantic search using vector embeddings...",
      "similarity_score": 0.89,
      "metadata": {
        "created_at": "2024-01-15",
        "author": "Sarah Chen"
      }
    }
  ],
  "total": 1,
  "query_time_ms": 145
}
```
