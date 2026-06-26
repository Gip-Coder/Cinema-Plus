# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 1.0.x-beta | ✅ |
| < 1.0.0 | ❌ |

## Reporting a Vulnerability

If you discover a security vulnerability, please report it responsibly:

1. **Do NOT** open a public GitHub issue
2. Email the maintainers with details of the vulnerability
3. Include steps to reproduce the issue
4. Allow reasonable time for a fix before public disclosure

## Security Considerations

### Authentication
- JWT tokens with configurable expiration
- Bcrypt password hashing with salt
- Role-based access control (RBAC)

### Data Protection
- SQL injection prevention via SQLAlchemy ORM (parameterized queries)
- Input validation via Pydantic schemas
- CORS middleware configuration
- Request validation error sanitization

### File Uploads
- File type validation
- Secure file storage paths
- No directory traversal in upload paths

### Environment Variables
- Sensitive configuration via `.env` (never committed)
- `.env.example` provided with placeholder values only
