````markdown
# Requirement and Solution Analyzer

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

## Result
- Real report https://github.com/bobydo/ShareFiles/tree/main/GitHubIssueMCP/reports
- **Issue:**  
- **Skip Discussion Reply:**  
- **Technical Feasibility (complexity / effort / risk):**  
![1777044742177](image/README/1777044742177.png)
