# Release process

BirthDex follows [Semantic Versioning](https://semver.org/):
`MAJOR.MINOR.PATCH`.

- **MAJOR** — breaking API or behaviour changes.
- **MINOR** — new features, backwards compatible.
- **PATCH** — fixes and documentation.

## 1. Prepare

1. Make sure `main` is green in CI.
2. Update `CHANGELOG.md`: move the entries out of *Unreleased*, add the date and
   links to the new tag.
3. Bump the version in `pyproject.toml` (`[project] version`).
4. Run locally:

   ```bash
   python -m pytest
   python -m compileall -q birthdex app.py
   python -m build
   ```

5. Commit:

   ```bash
   git add CHANGELOG.md pyproject.toml
   git commit -m "release: v1.0.0"
   ```

## 2. Tag and push

```bash
git tag -a v1.0.0 -m "BirthDex v1.0.0"
git push origin main --tags
```

Pushing the tag triggers `.github/workflows/release.yml`, which:

- builds the sdist and wheel,
- installs the wheel in a clean environment and runs `birthdex --version`,
- publishes a GitHub release with generated notes and the artifacts attached.

## 3. Optional: PyPI with trusted publishing

No API token is stored in the repository.

1. Create the project on PyPI (one-time) or reserve the name.
2. In PyPI, add a **trusted publisher**:
   - owner: `johirxofficial`
   - repository: `birthdex`
   - workflow: `release.yml`
   - environment: leave empty
3. In GitHub, set a repository variable
   `PUBLISH_TO_PYPI=true` (Settings → Variables → Actions).
4. Re-run the `Release` workflow. The `pypi` job publishes the artifacts.

After the first publish, installs work with:

```bash
pipx install birthdex
pip install birthdex
```

## 4. Optional: Docker Hub

```bash
docker build -t <dockerhub-user>/birthdex:1.0.0 .
docker tag <dockerhub-user>/birthdex:1.0.0 <dockerhub-user>/birthdex:latest
docker push <dockerhub-user>/birthdex:1.0.0
docker push <dockerhub-user>/birthdex:latest
```

## 5. Verify the release

- [ ] GitHub release exists with `birthdex-1.0.0.tar.gz` and the wheel.
- [ ] `pip install birthdex==1.0.0` in a clean venv works.
- [ ] `birthdex --version` prints the new version.
- [ ] The UI loads and `/health` responds.
- [ ] One real lookup succeeds and one wrong captcha returns `422` + a new
      captcha.

## Hotfixes

Branch from the tag, apply the fix, add a `PATCH` entry to `CHANGELOG.md`, bump
the version, tag `vX.Y.Z+1` and repeat the steps above. Keep the fix on `main`
as well.
