import csv
import logging
import os
import re
import unicodedata

import pdfplumber


logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger()

HEADERS = ['Fecha', 'Referencia', 'Tipo', 'Importe', 'Descripción']
DATE_PATTERN = re.compile(r'^\d{1,2}/\d{1,2}/\d{4}$')
MAX_ROW_LINE_GAP = 60
HEADER_Y_TOLERANCE = 12


def _normalize_header(value):
    text = ' '.join(str(value).split()).casefold()
    return ''.join(
        character for character in unicodedata.normalize('NFKD', text)
        if not unicodedata.combining(character)
    )


def _extract_page_transactions_from_words(page):
    words = page.extract_words(x_tolerance=2, y_tolerance=3)
    normalized_headers = [_normalize_header(header) for header in HEADERS]
    header_positions = None
    header_bottom = None

    for anchor in words:
        anchor_header = _normalize_header(anchor['text'])
        if anchor_header not in normalized_headers:
            continue

        nearby_words = [
            word for word in words
            if abs(word['top'] - anchor['top']) <= HEADER_Y_TOLERANCE
        ]
        positions = {}
        for word in nearby_words:
            header = _normalize_header(word['text'])
            if header in normalized_headers:
                positions.setdefault(header, word['x0'])

        if len(positions) == len(HEADERS):
            header_positions = positions
            header_bottom = max(
                word['bottom'] for word in nearby_words
                if _normalize_header(word['text']) in normalized_headers
            )
            break

    if header_positions is None:
        return []

    column_positions = sorted(
        (header_positions[header], index)
        for index, header in enumerate(normalized_headers)
    )
    boundaries = [
        (column_positions[index][0] + column_positions[index + 1][0]) / 2
        for index in range(len(column_positions) - 1)
    ]
    transactions = []
    previous_line_top = header_bottom

    for line in _group_words_after_header(words, header_bottom):
        if line['top'] - previous_line_top > MAX_ROW_LINE_GAP:
            break

        cells = [''] * len(HEADERS)
        for word in line['words']:
            if any(_normalize_header(word['text']) == header for header in normalized_headers):
                continue
            column = sum(word['x0'] >= boundary for boundary in boundaries)
            cells[column] = f"{cells[column]} {word['text']}".strip()

        if DATE_PATTERN.fullmatch(cells[0]):
            transactions.append(cells)
        elif transactions and any(cells):
            for index, cell in enumerate(cells):
                if cell:
                    transactions[-1][index] = (
                        f"{transactions[-1][index]} {cell}".strip()
                    )

        previous_line_top = line['top']

    return transactions


def _group_words_after_header(words, header_bottom):
    lines = []
    for word in sorted(
        (word for word in words if word['top'] > header_bottom),
        key=lambda item: (item['top'], item['x0']),
    ):
        if not lines or word['top'] - lines[-1]['top'] > 3:
            lines.append({'top': word['top'], 'words': [word]})
        else:
            lines[-1]['words'].append(word)
    return lines


def _extract_transactions(source_path):
    transactions = []

    with pdfplumber.open(source_path) as pdf:
        for page in pdf.pages:
            transactions.extend(_extract_page_transactions_from_words(page))

    return transactions


def process(source_path, output_path, file_name):
    """Extract the SumUp statement transaction table into a semicolon-delimited CSV."""
    transactions = _extract_transactions(source_path)
    if not transactions:
        raise ValueError(
            "[SumUp] No transaction table with the expected five columns was found in the PDF."
        )

    base_name = os.path.splitext(file_name)[0]
    prefix = os.environ.get("PREFIX_SUMUP", "SUMUP")
    csv_path = os.path.join(output_path, f"{prefix}_{base_name}.csv")

    with open(csv_path, 'w', encoding='utf-8', newline='') as csv_file:
        writer = csv.writer(csv_file, delimiter=';')
        writer.writerow(HEADERS)
        writer.writerows(transactions)

    logger.info(f"[SumUp] CSV successfully saved to: {csv_path}")
