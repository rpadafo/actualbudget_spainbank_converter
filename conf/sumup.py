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
TABLE_SETTINGS = {
    'vertical_strategy': 'text',
    'horizontal_strategy': 'text',
    'min_words_vertical': 2,
    'min_words_horizontal': 1,
    'text_x_tolerance': 3,
    'text_y_tolerance': 3,
}
DATE_PATTERN = re.compile(r'^\d{1,2}/\d{1,2}/\d{4}$')


def _normalize_text(value):
    if value is None:
        return ''
    return ' '.join(str(value).split())


def _normalize_header(value):
    text = _normalize_text(value).casefold()
    return ''.join(
        character for character in unicodedata.normalize('NFKD', text)
        if not unicodedata.combining(character)
    )


def _extract_transactions(source_path):
    expected_headers = [_normalize_header(header) for header in HEADERS]
    transactions = []

    with pdfplumber.open(source_path) as pdf:
        for page in pdf.pages:
            for table in page.extract_tables(table_settings=TABLE_SETTINGS):
                header_index = next(
                    (
                        index for index, row in enumerate(table)
                        if len(row) == len(HEADERS)
                        and [_normalize_header(cell) for cell in row] == expected_headers
                    ),
                    None,
                )
                if header_index is None:
                    continue

                for row in table[header_index + 1:]:
                    cells = [_normalize_text(cell) for cell in row]
                    if not any(cells):
                        continue
                    if len(cells) != len(HEADERS):
                        raise ValueError(
                            "[SumUp] A transaction row does not contain exactly five columns."
                        )

                    if DATE_PATTERN.fullmatch(cells[0]):
                        transactions.append(cells)
                    elif transactions:
                        for index, cell in enumerate(cells):
                            if cell:
                                transactions[-1][index] = (
                                    f'{transactions[-1][index]} {cell}'.strip()
                                )

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
