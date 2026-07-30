# GitHub setup

The intended repository is:

https://github.com/mohammedfahmed/pyradarsystems

To initialize a fresh extracted archive:

```bash
git init
git branch -M main
git add .
git commit -m "PyRadarSystems v0.2.0 research experiment layer"
git remote add origin https://github.com/mohammedfahmed/pyradarsystems.git
git push -u origin main
```

Keep GitHub Actions enabled and create a release tagged `v0.2.0` after the test matrix passes.
