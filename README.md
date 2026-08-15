# Resume

Build a PDF resume from YAML. Edit your content in `resume.yaml`, add your `photo.png`, run `make pdf`, get `resume.pdf` in the project root.

## Dependencies

- Python 3
- [Google Chrome](https://www.google.com/chrome/) (used headless for PDF)

## Usage

```bash
make pdf
```

`make pdf` creates `.venv` and installs Python packages if needed. The first run also copies the examples if your files are missing:

- `resume.example.yaml` → `resume.yaml`
- `photo.example.png` → `photo.png`

Then:

1. Edit `resume.yaml` (name, contacts, jobs, skills).
2. Add your `photo.png`.
3. Run `make pdf` again.

Output is `resume.pdf` in the project root. `resume.yaml`, `photo.png`, and `resume.pdf` are gitignored, so your details stay local.

YAML supports inline markdown: `**bold**`, `*italic*`, `***both***`, `__underline__`, `~~strike~~`.
