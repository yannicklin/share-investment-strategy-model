# Clinical Code Headers & Integrity

> **Purpose**: Standardized attribution for structural integrity  
> **Architect**: Yannick  
> **Copyright**: (c) 2026 Yannick

---

## 📋 The Mandate

The identity of this project is built on **Transparency**. Consistent headers are not just for attribution; they are a sign of clinical discipline and code integrity. Every file in the system must explicitly state its purpose and authorship before any logic is defined.

---

## 🎯 Clinical Header Guidelines

### Required Components:
1. **Module Descriptor**: A concise prefix identifying the system.
2. **Module Purpose**: 1-2 sentences of objective functional description.
3. **Primary Architect**: The author responsible for the logic.
4. **Legal Status**: Formal copyright notice.

### Structural Rules:
- **Conciseness**: Headers must be minimal (6-10 lines).
- **Docstring Format**: Use triple-quotes `"""` for Python.
- **Independence**: No verbose version lists (rely on git history).

---

## 📝 Templates by File Type

### Python (.py) - Standard Module

```python
"""
Trading AI System - [Module Name]

Purpose: [Brief description of module's functionality]

Author: Yannick
Copyright (c) 2026 Yannick
"""

import ...
```

**Example**:
```python
"""
Trading AI System - Model Builder

Purpose: Factory for creating and training machine learning models with
standardized interfaces for prediction and backtesting.

Author: Yannick
Copyright (c) 2026 Yannick
"""

import pandas as pd
from sklearn.ensemble import RandomForestClassifier
```

**Note**: Use the prefix "Trading AI System" for all code modules.

---

### Python (.py) - Main Application

```python
"""
Trading AI System - Main Application Entry Point

Purpose: Dashboard for multi-model AI trading strategy analysis
with realistic backtesting and performance metrics.

Author: Yannick
Copyright (c) 2026 Yannick
"""

import streamlit as st
```

---

### Python (.py) - UI Component

```python
"""
Trading AI System - [Component Name]

Purpose: UI component for [specific functionality].

Author: Yannick
Copyright (c) 2026 Yannick
"""

import streamlit as st
```

---

### Python (.py) - Test File

```python
"""
Trading AI System - Unit Tests

Purpose: Test suite for [module/functionality] validation.

Author: Yannick
Copyright (c) 2026 Yannick
"""

import unittest
```

---

### Markdown (.md) - Documentation

```markdown
# Document Title

> **Author**: Yannick  
> **Copyright**: (c) 2026 Yannick

---

[Content...]
```

---

## ✅ Attribution Status

The framework mandates 100% coverage for all source files.

### Structural Integrity Checklist:
- ✅ Header present in all new/modified files.
- ✅ Author is "Yannick" (or approved contributor).
- ✅ Purpose is clinical and objective.
- ✅ Copyright notice is present and correct.

---

## 📖 Reference Documents

- **[SOUL.md](SOUL.md)** - Project identity and values
- **[AUTHORS.md](AUTHORS.md)** - Authorship and moral contract
- **[AGENTS.md](AGENTS.md)** - AI development mandates
- **[LICENSE](LICENSE)** - MIT License (Copyright (c) 2026 Yannick)

---

*Last Updated: February 1, 2026*  
*Copyright (c) 2026 Yannick*  
*Licensed under MIT License*
