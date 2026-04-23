# Releasing

## Local packaging

Build the plugin zip locally from the repository root:

```bash
python package_plugin.py
```

This writes a versioned archive into `dist/`.

## GitHub Actions packaging

The repository includes a GitHub Actions workflow at `.github/workflows/package-plugin.yml`.

### Manual run

- Open the repository on GitHub
- Go to `Actions`
- Open `Package Cura Plugin`
- Run the workflow
- Download the generated artifact from the workflow run

### Tagged release

Push a tag that starts with `v`, for example:

```text
v0.2.0
```

When that tag is pushed:

- the workflow validates the Python plugin files
- builds the plugin zip
- uploads it as a workflow artifact
- creates or updates a GitHub release with the zip attached

## Archive structure

The generated zip contains the plugin inside a top-level folder named after the repository, so it can be extracted directly into Cura's plugins directory.

## Before tagging a release

- Update `plugin.json` version
- Update `CHANGELOG.md`
- Verify the plugin in a live Cura instance
- Commit the release changes
- Push the commit and the release tag
