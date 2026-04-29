from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

import fitz
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[2]
INPUT_MD = ROOT / "Ejercicio_1_CheapShark.md"
OUTPUT_PDF = ROOT / "output" / "pdf" / "Ejercicio_1_CheapShark.pdf"
PREVIEW_DIR = ROOT / "tmp" / "pdfs" / "preview"

A4_WIDTH = 1240
A4_HEIGHT = 1754
MARGIN_X = 96
MARGIN_TOP = 110
MARGIN_BOTTOM = 120
CONTENT_WIDTH = A4_WIDTH - (MARGIN_X * 2)

FONT_REGULAR = ImageFont.truetype(r"C:\Windows\Fonts\arial.ttf", 26)
FONT_BOLD = ImageFont.truetype(r"C:\Windows\Fonts\arialbd.ttf", 26)
FONT_H1 = ImageFont.truetype(r"C:\Windows\Fonts\arialbd.ttf", 42)
FONT_H2 = ImageFont.truetype(r"C:\Windows\Fonts\arialbd.ttf", 32)
FONT_H3 = ImageFont.truetype(r"C:\Windows\Fonts\arialbd.ttf", 28)
FONT_CODE = ImageFont.truetype(r"C:\Windows\Fonts\consola.ttf", 22)
FONT_FOOTER = ImageFont.truetype(r"C:\Windows\Fonts\arial.ttf", 18)

TEXT_COLOR = "#1b1f23"
MUTED_COLOR = "#4e5865"
ACCENT_COLOR = "#204d74"
RULE_COLOR = "#c9d7e4"
CODE_BG = "#f3f6f9"
PAGE_BG = "white"


@dataclass
class Block:
    kind: str
    text: str = ""
    level: int = 0


def parse_markdown(text: str) -> list[Block]:
    blocks: list[Block] = []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].rstrip()
        stripped = line.strip()

        if not stripped:
            i += 1
            continue

        if stripped.startswith("```"):
            code_lines: list[str] = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code_lines.append(lines[i].rstrip())
                i += 1
            blocks.append(Block(kind="code", text="\n".join(code_lines)))
            i += 1
            continue

        heading = re.match(r"^(#{1,3})\s+(.*)$", stripped)
        if heading:
            blocks.append(
                Block(kind="heading", level=len(heading.group(1)), text=heading.group(2).strip())
            )
            i += 1
            continue

        if stripped.startswith("- "):
            bullet_lines = [stripped[2:].strip()]
            i += 1
            while i < len(lines):
                next_line = lines[i].rstrip()
                next_stripped = next_line.strip()
                if not next_stripped:
                    i += 1
                    break
                if next_stripped.startswith("- ") or next_stripped.startswith("#") or next_stripped.startswith("```"):
                    break
                bullet_lines.append(next_stripped)
                i += 1
            blocks.append(Block(kind="bullet", text=" ".join(bullet_lines)))
            continue

        paragraph_lines = [stripped]
        i += 1
        while i < len(lines):
            next_line = lines[i].rstrip()
            next_stripped = next_line.strip()
            if not next_stripped:
                i += 1
                break
            if next_stripped.startswith("- ") or next_stripped.startswith("#") or next_stripped.startswith("```"):
                break
            paragraph_lines.append(next_stripped)
            i += 1
        blocks.append(Block(kind="paragraph", text=" ".join(paragraph_lines)))

    return blocks


def clean_inline_markdown(text: str) -> str:
    text = text.replace("**", "")
    text = text.replace("`", "")
    return text


def measure_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont) -> int:
    if not text:
        return 0
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0]


def line_height(font: ImageFont.FreeTypeFont, extra: int = 0) -> int:
    bbox = font.getbbox("Ag")
    return (bbox[3] - bbox[1]) + extra


def wrap_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.FreeTypeFont,
    max_width: int,
) -> list[str]:
    if not text:
        return [""]

    def split_long_token(token: str) -> list[str]:
        if measure_text(draw, token, font) <= max_width:
            return [token]
        parts: list[str] = []
        remaining = token
        while remaining:
            cut = len(remaining)
            while cut > 1 and measure_text(draw, remaining[:cut], font) > max_width:
                cut -= 1
            parts.append(remaining[:cut])
            remaining = remaining[cut:]
        return parts

    words: list[str] = []
    for raw_word in text.split():
        words.extend(split_long_token(raw_word))

    lines: list[str] = []
    current = words[0]
    for word in words[1:]:
        candidate = f"{current} {word}"
        if measure_text(draw, candidate, font) <= max_width:
            current = candidate
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def wrap_code_lines(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.FreeTypeFont,
    max_width: int,
) -> list[str]:
    wrapped: list[str] = []
    for raw_line in text.splitlines() or [""]:
        line = raw_line
        if not line:
            wrapped.append("")
            continue
        while measure_text(draw, line, font) > max_width:
            cut = len(line)
            while cut > 1 and measure_text(draw, line[:cut], font) > max_width:
                cut -= 1
            wrapped.append(line[:cut])
            line = line[cut:]
        wrapped.append(line)
    return wrapped


def start_page(page_number: int) -> tuple[Image.Image, ImageDraw.ImageDraw, int]:
    image = Image.new("RGB", (A4_WIDTH, A4_HEIGHT), PAGE_BG)
    draw = ImageDraw.Draw(image)
    draw.line((MARGIN_X, 72, A4_WIDTH - MARGIN_X, 72), fill=RULE_COLOR, width=3)
    draw.text((MARGIN_X, 34), "CheapShark - Catalogo Externo", font=FONT_FOOTER, fill=MUTED_COLOR)
    return image, draw, MARGIN_TOP


def footer(draw: ImageDraw.ImageDraw, page_number: int) -> None:
    label = f"Pagina {page_number}"
    width = measure_text(draw, label, FONT_FOOTER)
    draw.line(
        (MARGIN_X, A4_HEIGHT - 68, A4_WIDTH - MARGIN_X, A4_HEIGHT - 68),
        fill=RULE_COLOR,
        width=2,
    )
    draw.text(
        ((A4_WIDTH - width) / 2, A4_HEIGHT - 52),
        label,
        font=FONT_FOOTER,
        fill=MUTED_COLOR,
    )


def render_pages(blocks: list[Block]) -> list[Image.Image]:
    pages: list[Image.Image] = []
    page_number = 1
    image, draw, y = start_page(page_number)

    def ensure_space(height: int) -> tuple[Image.Image, ImageDraw.ImageDraw, int, int]:
        nonlocal image, draw, y, page_number, pages
        if y + height <= A4_HEIGHT - MARGIN_BOTTOM:
            return image, draw, y, page_number
        footer(draw, page_number)
        pages.append(image)
        page_number += 1
        image, draw, y = start_page(page_number)
        return image, draw, y, page_number

    for block in blocks:
        if block.kind == "heading":
            text = clean_inline_markdown(block.text)
            if block.level == 1:
                font = FONT_H1
                color = ACCENT_COLOR
                spacing_before = 24
                spacing_after = 20
            elif block.level == 2:
                font = FONT_H2
                color = TEXT_COLOR
                spacing_before = 18
                spacing_after = 14
            else:
                font = FONT_H3
                color = TEXT_COLOR
                spacing_before = 12
                spacing_after = 10

            lines = wrap_text(draw, text, font, CONTENT_WIDTH)
            block_height = (line_height(font, 8) * len(lines)) + spacing_before + spacing_after
            ensure_space(block_height)
            y += spacing_before
            for idx, line in enumerate(lines):
                draw.text((MARGIN_X, y), line, font=font, fill=color)
                y += line_height(font, 8)
                if block.level == 1 and idx == len(lines) - 1:
                    draw.line(
                        (MARGIN_X, y + 4, MARGIN_X + 220, y + 4),
                        fill=ACCENT_COLOR,
                        width=4,
                    )
            y += spacing_after
            continue

        if block.kind == "paragraph":
            text = clean_inline_markdown(block.text)
            lines = wrap_text(draw, text, FONT_REGULAR, CONTENT_WIDTH)
            block_height = (line_height(FONT_REGULAR, 10) * len(lines)) + 8
            ensure_space(block_height)
            for line in lines:
                draw.text((MARGIN_X, y), line, font=FONT_REGULAR, fill=TEXT_COLOR)
                y += line_height(FONT_REGULAR, 10)
            y += 8
            continue

        if block.kind == "bullet":
            text = clean_inline_markdown(block.text)
            bullet_prefix = "- "
            bullet_width = measure_text(draw, bullet_prefix, FONT_REGULAR)
            lines = wrap_text(draw, text, FONT_REGULAR, CONTENT_WIDTH - bullet_width)
            block_height = (line_height(FONT_REGULAR, 10) * len(lines)) + 4
            ensure_space(block_height)
            for index, line in enumerate(lines):
                prefix = bullet_prefix if index == 0 else "  "
                x = MARGIN_X
                draw.text((x, y), prefix, font=FONT_REGULAR, fill=TEXT_COLOR)
                draw.text((x + bullet_width, y), line, font=FONT_REGULAR, fill=TEXT_COLOR)
                y += line_height(FONT_REGULAR, 10)
            y += 4
            continue

        if block.kind == "code":
            code_lines = wrap_code_lines(draw, block.text, FONT_CODE, CONTENT_WIDTH - 36)
            code_line_height = line_height(FONT_CODE, 8)
            block_height = (code_line_height * len(code_lines)) + 34
            ensure_space(block_height)
            draw.rounded_rectangle(
                (MARGIN_X, y, A4_WIDTH - MARGIN_X, y + block_height),
                radius=16,
                fill=CODE_BG,
                outline=RULE_COLOR,
                width=2,
            )
            inner_y = y + 16
            for code_line in code_lines:
                draw.text((MARGIN_X + 18, inner_y), code_line, font=FONT_CODE, fill=TEXT_COLOR)
                inner_y += code_line_height
            y += block_height + 10
            continue

    footer(draw, page_number)
    pages.append(image)
    return pages


def save_pdf(pages: list[Image.Image], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    rgb_pages = [page.convert("RGB") for page in pages]
    rgb_pages[0].save(
        output_path,
        save_all=True,
        append_images=rgb_pages[1:],
        resolution=150.0,
    )


def render_preview(pdf_path: Path, preview_dir: Path) -> None:
    preview_dir.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(pdf_path)
    try:
        for index, page in enumerate(doc, start=1):
            pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5), alpha=False)
            pix.save(preview_dir / f"page-{index}.png")
    finally:
        doc.close()


def main() -> None:
    markdown = INPUT_MD.read_text(encoding="utf-8")
    blocks = parse_markdown(markdown)
    pages = render_pages(blocks)
    save_pdf(pages, OUTPUT_PDF)
    render_preview(OUTPUT_PDF, PREVIEW_DIR)
    print(f"PDF generado: {OUTPUT_PDF}")
    print(f"Paginas: {len(pages)}")
    print(f"Preview: {PREVIEW_DIR}")


if __name__ == "__main__":
    main()
