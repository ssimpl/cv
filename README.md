# CV Builder

Build a PDF resume from YAML. Edit your content in `resume.yaml`, add your `photo.png`, run `make pdf`, get `resume.pdf` in the project root.

## Dependencies

- [Docker](https://docs.docker.com/get-docker/) (Compose included)

## Usage

```bash
make pdf
```

The first run builds a container with Python and Chromium. Later runs reuse it. If your files are missing, the first run also copies the examples:

- `resume.example.yaml` → `resume.yaml`
- `photo.example.png` → `photo.png`

Then:

1. Edit `resume.yaml` (name, contacts, jobs, skills).
2. Add your `photo.png`.
3. Run `make pdf` again.

Output is `resume.pdf` in the project root. `resume.yaml`, `photo.png`, and `resume.pdf` are gitignored, so your details stay local.

YAML supports inline markdown: `**bold**`, `*italic*`, `***both***`, `__underline__`, `~~strike~~`.

Summary can be several paragraphs (a YAML list, or a `|` block with blank lines). Optional `languages` go in the right column; `level` is one of Beginner, Intermediate, Advanced, Proficient, Native. On the `education:` block, set `position: left|right` and optional `page: 1, 2, 3, ...` (default 1); entries go under `items:`. Jobs use the same `page` field. `left` is under Experience, `right` is the bottom of the right column. If a block does not fit, it continues on the next page. Right-column blocks that do not fit on page 1 continue on page 2.
