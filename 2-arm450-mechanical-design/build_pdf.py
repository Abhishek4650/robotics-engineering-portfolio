#!/usr/bin/env python3
"""
Render REPORT.md (markdown subset) to output/ARM450_REPORT.pdf with fpdf2.

Supports: #/##/### headings, paragraphs, - bullets, | tables |, ![img](path),
``` code blocks. Animated GIFs are embedded as their middle frame.
Run after every step so the PDF stays in sync:  python3 build_pdf.py
"""
import os
import re
import sys
from fpdf import FPDF
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = "/usr/share/fonts/truetype/dejavu"
INK, MUT, ACC = (28, 35, 51), (90, 100, 120), (201, 86, 15)


def clean(s):
    s = s.replace("✅", "[done]").replace("🔶", "[gate]").replace("⛔", "X")
    s = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", s)
    s = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", s)
    s = s.replace("**", "").replace("`", "")
    s = re.sub(r"(?<!\w)\*([^*]+)\*(?!\w)", r"\1", s)
    return s.strip()


class Doc(FPDF):
    def __init__(self):
        super().__init__(format="A4")
        self.add_font("dv", "", f"{FONTS}/DejaVuSans.ttf")
        self.add_font("dv", "B", f"{FONTS}/DejaVuSans-Bold.ttf")
        self.add_font("dvm", "", f"{FONTS}/DejaVuSansMono.ttf")
        self.set_auto_page_break(True, margin=18)
        self.set_margins(17, 16, 17)

    # The footer used to be the literal string "ARM-450 · stress & stiffness
    # analysis" on EVERY document this script produced -- correct for the first
    # report it was written for, and wrong on the other seventeen. It now takes
    # the document's own H1.
    doc_title = "ARM-450"

    def footer(self):
        self.set_y(-12)
        self.set_font("dv", "", 8.5)
        self.set_text_color(*MUT)
        self.cell(0, 6, f"{self.doc_title} · page {self.page_no()}", align="C")

    def quote(self, text):
        """A markdown blockquote. Without this, every `> ...` line printed its
        own ">" character into the body text and the callouts -- which are the
        lines a reader is most likely to stop on -- came out looking like
        mangled source."""
        self.ln(2)
        x0, y0 = self.get_x(), self.get_y()
        self.set_font("dv", "", 10.2)
        self.set_text_color(*MUT)
        self.set_x(x0 + 6)
        self.multi_cell(0, 5.4, clean(text))
        y1 = self.get_y()
        self.set_draw_color(*ACC)
        self.set_line_width(1.1)
        self.line(x0 + 2, y0, x0 + 2, y1 - 1)
        self.set_x(x0)
        self.ln(2)

    def heading(self, level, text):
        sizes = {1: 20, 2: 15.5, 3: 12.5}
        self.ln(4 if level > 1 else 6)
        self.set_font("dv", "B", sizes[level])
        self.set_text_color(*(ACC if level == 2 else INK))
        self.multi_cell(0, 7, clean(text))
        if level == 1:
            self.set_draw_color(*INK)
            self.set_line_width(0.5)
            self.line(self.l_margin, self.get_y() + 1, 193, self.get_y() + 1)
            self.ln(3)
        self.ln(1)

    def para(self, text, bullet=False):
        self.set_font("dv", "", 11.0)
        self.set_text_color(*INK)
        if bullet:
            self.set_x(self.l_margin + 4)
            self.multi_cell(172, 5.9, "•  " + clean(text))
        else:
            self.multi_cell(0, 5.9, clean(text))
        self.ln(1.2)

    def code(self, lines):
        self.set_font("dvm", "", 9.0)
        self.set_text_color(*MUT)
        self.set_fill_color(240, 242, 246)
        self.multi_cell(0, 5.0, "\n".join(lines), fill=True)
        self.ln(1.5)

    def image_block(self, path):
        if not os.path.exists(path):
            return
        img = Image.open(path)
        if getattr(img, "n_frames", 1) > 1:
            img.seek(img.n_frames // 2)
        img = img.convert("RGB")
        w_mm = 176.0
        h_mm = w_mm * img.height / img.width
        if self.get_y() + h_mm > 275:
            self.add_page()
        x = (210 - w_mm) / 2
        self.image(img, x=x, w=w_mm)
        self.ln(2)

    def md_table(self, rows):
        cells = [[clean(c) for c in r.strip().strip("|").split("|")] for r in rows]
        cells = [r for r in cells if not all(set(c) <= set(":- ") for c in r)]
        self.set_font("dv", "", 9.6)
        self.set_text_color(*INK)
        self.set_draw_color(215, 220, 230)
        self.set_line_width(0.2)
        with self.table(first_row_as_headings=True, line_height=5.6,
                        text_align="LEFT", padding=1.2) as tb:
            for r in cells:
                row = tb.row()
                for c in r:
                    row.cell(c)
        self.ln(2)


def render(md_path, out_path):
    pdf = Doc()
    # footer text = the document's own H1, so it cannot describe the wrong doc
    for _l in open(md_path, encoding='utf-8'):
        if _l.startswith('# '):
            pdf.doc_title = clean(_l[2:].strip())
            break
    pdf.add_page()
    lines = open(md_path).read().splitlines()
    i, in_code, code_buf, tbl_buf = 0, False, [], []
    while i < len(lines):
        ln = lines[i]
        if ln.strip().startswith("```"):
            if in_code:
                pdf.code(code_buf); code_buf = []
            in_code = not in_code
            i += 1; continue
        if in_code:
            code_buf.append(ln); i += 1; continue
        if ln.strip().startswith("|"):
            tbl_buf.append(ln); i += 1; continue
        if tbl_buf:
            pdf.md_table(tbl_buf); tbl_buf = []
        m = re.match(r"^(#{1,3})\s+(.*)", ln)
        if m:
            pdf.heading(len(m.group(1)), m.group(2)); i += 1; continue
        m = re.match(r"^!\[[^\]]*\]\(([^)]+)\)", ln.strip())
        if m:
            pdf.image_block(os.path.join(HERE, m.group(1))); i += 1; continue
        if ln.strip().startswith(">"):
            q = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                q.append(lines[i].strip().lstrip(">").strip()); i += 1
            # a blank quoted line separates paragraphs inside the quote
            for part in " \n".join(q).split(" \n \n"):
                if part.strip():
                    pdf.quote(part.replace(" \n", " "))
            continue
        if ln.strip().startswith(("- ", "* ")):
            pdf.para(ln.strip()[2:], bullet=True); i += 1; continue
        m = re.match(r"^\s*(\d+)\.\s+(.*)", ln)
        if m:
            # numbered items were being swallowed into the paragraph below them,
            # so "1. ... 2. ..." ran together on one line.
            # They then lost the opposite way: only the FIRST line of a wrapped
            # item was taken, and every continuation line became a paragraph of
            # its own at the wrong indent. Gather the continuations here, the
            # same way a plain paragraph does.
            body = [m.group(2)]
            while (i + 1 < len(lines) and lines[i + 1].strip() not in ("", "---")
                   and not re.match(r"^(#|\||!\[|- |\* |>|\d+\.\s|```)",
                                    lines[i + 1].strip())):
                i += 1
                body.append(lines[i].strip())
            pdf.para(f"{m.group(1)}.  " + " ".join(body), bullet=False)
            i += 1; continue
        if ln.strip() in ("", "---"):
            i += 1; continue
        block = [ln]
        while (i + 1 < len(lines) and lines[i + 1].strip() not in ("", "---")
               and not re.match(r"^(#|\||!\[|- |\* |>|\d+\.\s|```)",
                                lines[i + 1].strip())):
            i += 1; block.append(lines[i])
        pdf.para(" ".join(block)); i += 1
    if tbl_buf:
        pdf.md_table(tbl_buf)
    pdf.output(out_path)
    print(f"wrote {out_path} ({pdf.page_no()} pages)")


if __name__ == "__main__":
    src = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "REPORT.md")
    dst = os.path.join(HERE, "output",
                       "ARM450_" + os.path.splitext(os.path.basename(src))[0].upper() + ".pdf")
    render(src, dst)
