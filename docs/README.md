# Documentation Folder

## Purpose

This folder is reserved for **permanent reference documentation** and supplementary guides that complement the core architecture documents.

## Core Documentation (Permanent)

All essential system documentation is maintained in the project root:

- **[ARCHITECTURE.md](../ARCHITECTURE.md)** - Complete system architecture, database schemas, multi-market design
- **[README.md](../README.md)** - Project overview, installation, usage
- **[AGENTS.md](../AGENTS.md)** - AI agent development guidelines, core mandates
- **[DEPLOYMENT_GUIDE.md](../DEPLOYMENT_GUIDE.md)** - Production deployment guide (Koyeb/Supabase)
- **[SOUL.md](../SOUL.md)** - Project philosophy, values, architectural principles
- **[AUTHORS.md](../AUTHORS.md)** - Contributors and acknowledgments

## Implementation Notes

Detailed implementation documentation (feature enhancements, test results, migration guides) are tracked in git history and can be retrieved when needed:

```bash
# View documentation history
git log --all --full-history -- "docs/*.md"

# Restore specific documentation from history
git show <commit-hash>:docs/filename.md
```

## Guidelines

- **Core architecture changes** → Update root-level documents (ARCHITECTURE.md, README.md, etc.)
- **Implementation progress** → Use git commits with descriptive messages, avoid long-lived progress docs
- **Permanent reference material** → Place here (e.g., API specifications, integration guides that won't change)

---

*Last Updated: February 6, 2026*
