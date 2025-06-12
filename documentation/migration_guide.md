# Documentation Migration Guide

This guide provides step-by-step instructions for migrating existing Exit Interview Bot documentation to the new structured system.

## Current Documentation State

The Exit Interview Bot project currently has documentation scattered across multiple locations:

1. Root directory (`*.md` files)
2. `exitbot/docs/` directory
3. Various summary files with inconsistent naming

## Migration Steps

### 1. Setup Directory Structure

Create the following folder structure:

```
documentation/
├── index.md                   # Already created
├── planning/
│   ├── architecture/
│   ├── implementation/
│   └── testing/
├── summaries/
│   ├── morning/
│   ├── afternoon/
│   └── sprints/
├── technical/
│   ├── api/
│   ├── database/
│   └── components/
├── guides/
│   ├── development/
│   ├── deployment/
│   └── user/
└── archived/
```

### 2. Categorize Existing Documents

#### Planning Documents
- `implementation_plan.md` → `documentation/planning/implementation/`
- `test_plan.md` → `documentation/planning/testing/`
- `architecture_recommendations.md` → `documentation/planning/architecture/`
- `dev_plan.md` → `documentation/planning/implementation/`

#### Session Summaries
- `morning_ses*.md` files → `documentation/summaries/morning/`
- `morning_summary*.md` files → `documentation/summaries/morning/`
- `afternoon_ses*.md` files → `documentation/summaries/afternoon/`
- `afternoon_summary*.md` files → `documentation/summaries/afternoon/`
- `evaluation01_summary.md` → `documentation/summaries/sprints/`
- `dev_summary1.md` → `documentation/summaries/sprints/`

#### Technical Documentation
- API documentation from `exitbot/docs/` → `documentation/technical/api/`
- Database schemas from `exitbot/docs/` → `documentation/technical/database/`
- Component descriptions from `exitbot/docs/` → `documentation/technical/components/`

#### Guides
- Setup guides from `exitbot/docs/` → `documentation/guides/development/`
- Deployment guides → `documentation/guides/deployment/`
- User guides → `documentation/guides/user/`

### 3. Migration Process

For each document:

1. **Copy the file** to the new location
2. **Update the filename** if it doesn't conform to naming conventions
3. **Edit the front matter** to add:
   ```markdown
   ---
   title: [Document Title]
   category: [Planning|Summary|Technical|Guide]
   created: [Original Creation Date]
   last_updated: [Current Date]
   version: 1.0
   ---
   ```
4. **Update internal links** to point to new document locations
5. **Add cross-references** to related documents

### 4. Document Conversion Examples

#### Example 1: Implementation Plan

**Original**: `/implementation_plan.md`  
**New Path**: `/documentation/planning/implementation/implementation_plan.md`

Add front matter:
```markdown
---
title: Exit Interview Bot - Detailed Implementation Plan
category: Planning
created: 2023-10-15
last_updated: 2023-10-20
version: 1.0
---
```

#### Example 2: Afternoon Summary

**Original**: `/afternoon_summary8.md`  
**New Path**: `/documentation/summaries/afternoon/afternoon_summary8.md`

Add front matter:
```markdown
---
title: Exit Interview Bot - Afternoon Session 8 Summary
category: Summary
created: 2023-10-15
last_updated: 2023-10-15
version: 1.0
---
```

### 5. Update Index Document

After migrating each document:

1. Update links in `documentation/index.md`
2. Ensure the "Recent Documents" section is current
3. Add any important documents that weren't previously listed

### 6. Special Considerations

#### Version History

For documents with multiple versions:
- Keep the latest version in the main directory
- Move older versions to `documentation/archived/`
- Name archived versions with version numbers: `implementation_plan_v0.9.md`

#### README.md Files

- Keep `README.md` files at the root of the repository
- Add links in the README to direct readers to the documentation index

#### Code Comments vs. Documentation

- Move detailed design explanations from code comments to proper documentation
- Keep code comments focused on "how" and "why" for specific implementations
- Documentation should focus on higher-level concepts and integrations

## After Migration

### Verification Checklist

- [ ] All documents are in their appropriate categories
- [ ] All documents follow naming conventions
- [ ] All documents have proper front matter
- [ ] All internal links are updated
- [ ] Index document is comprehensive and up-to-date
- [ ] No duplicate documents exist (except for archived versions)

### Documentation Maintenance

Set up a routine for maintaining documentation:

1. **Weekly Review**: Check for outdated information
2. **New Feature Documentation**: Require documentation for all new features
3. **Periodic Cleanup**: Archive obsolete documents quarterly

## Tools and Automation

Consider using these tools to help manage documentation:

1. **Markdown Linters**: Ensure consistent formatting
2. **Link Checkers**: Verify internal links are valid
3. **Documentation Generators**: For API documentation
4. **Git Hooks**: Enforce documentation standards

---

*Last Updated: 2025-05-01* 