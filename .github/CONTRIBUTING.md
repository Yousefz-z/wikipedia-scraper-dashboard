# Contributing to Wikipedia Data Scraper Dashboard

Thanks for your interest in contributing! This is a small personal project, but
outside contributions, bug reports, and suggestions are welcome.

## Before you start

For anything beyond a trivial fix (typos, small doc tweaks), please open an
issue first describing what you'd like to change and why. This avoids
duplicated effort and lets us agree on the approach before you spend time
writing code.

Found a bug or have an idea? [Open a new issue](https://github.com/Yousefz-z/wikipedia-scraper-dashboard/issues/new/choose) — you'll be prompted to pick a Bug Report or Feature Request form.

## Development setup

```bash
git clone https://github.com/<your-fork-username>/wikipedia-scraper-dashboard.git
cd wikipedia-scraper-dashboard
python -m venv venv
source venv/bin/activate  # on Windows: venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install --group dev
streamlit run dashboard.py
```

The app opens at `http://localhost:8501`.

`pip install --group dev` installs the linting and type checking tools at the
same versions CI uses, pinned in `pyproject.toml`. It needs pip 25.1 or newer,
which is why the setup upgrades pip first.

## Branching

Create a branch off `main` named for the kind of change you're making:

- `fix/short-description` — bug fixes
- `feature/short-description` — new functionality
- `refactor/short-description` — code cleanup with no behavior change
- `docs/short-description` — documentation only

## Making a change

1. Fork the repo and create your branch from `main`.
2. Make your change, keeping it focused on one thing at a time.
3. Follow the existing code style:
   - Prefer small, named functions over long top-level script logic.
   - Add type hints to new functions and keep existing ones consistent.
   - Pin any new dependency you add to `requirements.txt` with an exact or
     minimum-safe version.
   - Handle expected failure cases explicitly rather than catching broad
     exceptions and surfacing raw error text to the user.
4. Test your change manually by running the dashboard.
5. Run the same checks CI runs, and make sure all three pass:

   ```bash
   ruff check .
   ruff format --check .
   mypy dashboard.py scraper.py database.py
   ```

   `ruff format .` will fix formatting for you, and `ruff check --fix .` will
   fix the lint errors it knows how to fix.
6. Commit with a clear message describing what changed and why.
7. Open a pull request against `main` using the pull request template — fill
   it out completely, including how you tested the change.

## Pull request review

- Keep PRs small and scoped to a single change where possible — easier to
  review, easier to revert if something goes wrong.
- Be responsive to review feedback; if a requested change doesn't make sense
  to you, say so and we can discuss it.
- A maintainer will merge once the PR looks good.

## Code of Conduct

This project follows a [Code of Conduct](CODE_OF_CONDUCT.md). By
participating, you're expected to uphold it.

## Questions

If anything here is unclear, open an issue and ask — documentation gaps are
worth fixing too.
