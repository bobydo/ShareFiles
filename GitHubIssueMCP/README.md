````markdown
# Requirement and Solution Analyzer

AI tool that clarifies requirements, suggests technical solutions, and estimates feasibility (complexity, effort and risk) using a local LLM (privacy-safe).

## What it does

- Clarify requirements
- Classify replies (discussion vs solution)
- Estimate technical feasibility (complexity, effort, risk)

## Tech
- **Model:** `OLLAMA_MODEL = "qwen3:8b"` (for security purpose)
- **Language:** Python
- **Libraries:** Python standard libraries only

## Setup

### Initialize Virtual Environment
```bash
PS D:\ShareFiles\GitHubIssueMCP> uv venv
````

Output:

```bash
Using CPython 3.13.7 interpreter at: C:\Python313\python.exe
Creating virtual environment at: .venv
Activate with: .venv\Scripts\activate
```

## Test Issues

* https://github.com/bobydo/ShareFiles/issues

## Commands

```bash
uv run python analyze_issues.py --repo bobydo/ShareFiles --issue 1
uv run python analyze_issues.py --repo bobydo/ShareFiles --issue 1
```

## Example
- Real report https://github.com/bobydo/ShareFiles/tree/main/GitHubIssueMCP/reports
- **Input Issue:**  
- **Skip Discussion Reply:**  
- **Technical Feasibility (complexity / effort / risk): Estimate: Medium complexity, 2-3 weeks, medium complexity and risk**  
![1777044742177](image/README/1777044742177.png)

## Future Improvements

- **RAG-based Knowledge Base**
  - Analyze existing requirements, discussions, and solutions
  - Build a searchable knowledge base for better recommendations

- **Similar Solution Detection**
  - Identify related past issues and solutions
  - Support smarter suggestions during issue analysis

- **AI-assisted Code Review**
  - Detect common issues and improvement patterns
  - Suggest fixes based on historical solutions
