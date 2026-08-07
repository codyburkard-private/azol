# Releasing azol

Package version lives in [`pyproject.toml`](pyproject.toml) (`project.version`).
Publishing is driven by annotated git tags `vMAJOR.MINOR.PATCH` via
[`.github/workflows/release.yml`](.github/workflows/release.yml).

## Checklist

1. Land features on `main` (green CI).
2. Open a release PR that:
   - Bumps `project.version` in `pyproject.toml`
   - Updates [`CHANGELOG.md`](CHANGELOG.md)
3. Merge the PR to `main`.
4. Tag and push from `main` (tag **must** match `pyproject.toml`, including the leading `v` only on the tag):

   ```bash
   git checkout main
   git pull
   git tag -a v0.6.0 -m "azol 0.6.0"
   git push origin v0.6.0
   ```

5. Confirm the **Release** workflow:
   - Runs unit tests (`AZOL_LIVE_GRAPH=0`)
   - Builds wheels/sdists and runs `twine check`
   - Uploads to PyPI
   - Creates a GitHub Release with the dist artifacts

## TestPyPI (manual)

Use **Actions → Release → Run workflow**, target `testpypi`.
This uses `secrets.PyPiTestSecret` and does not create a GitHub Release.

Manual Prod publish from the same workflow (`target=pypi`) is available but
prefer tagging `v*` so version checks and GitHub Releases stay consistent.

## Notes

- Do **not** derive the version from the branch name.
- Live Graph tests are not part of the release gate.
- PyPI credentials: `PyPiProdSecret` / `PyPiTestSecret` (twine token auth).
