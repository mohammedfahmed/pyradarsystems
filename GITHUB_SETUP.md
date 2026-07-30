# GitHub Setup

## Create the repository from the command line

Extract the ZIP, enter the extracted project directory, and run:

```bash
git init
git branch -M main
git add .
git commit -m "Initial PyRadarSystems v0.1.0 release"
git remote add origin https://github.com/<account>/pyradarsystems.git
git push -u origin main
```

Alternatively, create an empty repository on GitHub and upload the extracted files through the web interface.

## Recommended repository settings

- Keep GitHub Actions enabled so the included test workflow runs automatically.
- Enable branch protection for `main` after the first push.
- Add a repository description and topics such as `radar`, `phased-array`, `radar-simulation`, `signal-processing`, `fmcw`, `mimo`, and `tracking`.
- Replace or extend the contact instructions in `SECURITY.md`.
- Add the final repository URL to `CITATION.cff`.

## First release

Create a GitHub release tagged `v0.1.0` after the tests pass. The source ZIP generated automatically by GitHub is sufficient; build artifacts can be attached separately later.
