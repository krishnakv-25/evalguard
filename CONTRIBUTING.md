# Contributing to EvalGuard 🛡️

We welcome contributions from Quality Engineers, SDETs, Security Researchers, and AI Platform Engineers!

---

## 🛠️ Development Setup

EvalGuard is intentionally designed with **zero external dependencies**. All you need is Python 3.8+.

```bash
# 1. Clone the repository
git clone https://github.com/your-username/evalguard.git
cd evalguard

# 2. Run the test suite
python3 -m unittest discover -s tests -v
```

---

## 🧩 Adding a New Guard

Adding a new quality or security guard is straightforward:

1. **Create the Guard:**
   Add a new file in `evalguard/guards/your_guard.py` subclassing `BaseGuard`:
   ```python
   from evalguard.guards.base import BaseGuard
   from evalguard.models import TestCase, TargetResponse, GuardResult

   class CustomGuard(BaseGuard):
       def __init__(self, config=None):
           super().__init__("CustomGuard", config)

       def evaluate(self, test_case: TestCase, response: TargetResponse) -> GuardResult:
           # Your evaluation logic here
           passed = ...
           score = 1.0 if passed else 0.0
           return GuardResult(
               guard_name=self.name,
               passed=passed,
               score=score,
               reason="Explanation of pass or failure",
               details={}
           )
   ```

2. **Register the Guard:**
   Import and add it to `GUARD_REGISTRY` in `evalguard/guards/__init__.py`.

3. **Add Unit Tests:**
   Add test coverage in `tests/test_guards.py`.

4. **Verify & Run:**
   Run `python3 -m unittest discover -s tests -v`.

---

## 📋 Pull Request Guidelines

1. Ensure all tests pass: `python3 -m unittest discover -s tests -v`.
2. Keep core dependencies at zero (pure Python standard library).
3. Update `README.md` and `examples/` if introducing new guards or CLI flags.
4. Write descriptive commit messages.

Thank you for contributing to the future of GenAI Quality Engineering!
