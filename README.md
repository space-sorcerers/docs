# The Robust Book

This is the Mintlify-based developer documentation for all Space Wizards projects, including Robust Toolbox, Space Station 14, the SS14 launcher, etc. These docs cover many topics and can be potentially very useful for mappers, spriters, active contributors & prospective contributors, people who want to use our engine for their own projects, fork developers, and so on.

The site is currently hosted at [https://docs.spacestation14.com](https://docs.spacestation14.com).

Benefits of the current docs site infrastructure include:
- First-class git support, open source and actually editable by everyone
- Decently familiar & comfortable for developers since Mintlify is widely used
- No sign-on infrastructure or hosting necessary (besides GH Pages), if forks would like to host their own
- Very low friction to adding new pages and editing/fixing old ones
- High level of customizability with styling and easy custom scripting
- Full localization support with bilingual `en/` and `ru/` content
- Integrated search, SEO, and analytics out of the box

The following features & tooling are available and in use:
- MDX components (JSX in markdown)
- Built-in search and sidebar navigation
- `mintlify validate` for CI checks
- `mintlify export` for static site generation
- Python-based test suite for validation
- GitHub Actions CI/CD for PRs and deployment

## Running locally
### Install
```bash
npm i -g mintlify
```
### Run
```bash
mintlify dev
```

Opens a live preview at `http://localhost:3000` with hot reload.

**More on editing: [Guide to Editing Docs](./en/meta/guide-to-editing-docs.mdx).**

## License

The Robust Book is released under the Mozilla Public License v2.0.
