import argparse
import csv
import os
import re
import unicodedata
from collections import defaultdict

from dotenv import load_dotenv
from supabase import create_client


EXPECTED_HEADERS = [
    "NOMBRE",
    "NIT",
    "DIRECCIÓN",
    "CIUDAD",
    "CORREO 1",
    "CONTACTO",
    "CARGO",
    "SEDE",
    "TELÉFONO",
    "RESPONSABLE DE LA VISITA",
    "CARGO",
    "ASESOR",
    "CORREO DE ASESOR",
    "ZONA",
    "CAJA DE COMPENSACIÓN",
    "PROFESIONAL ASIGNADO",
    "CORREO ",
    "ESTADO",
    "OBSERVACIONES ",
]


def strip_invisible_chars(text):
    if text is None:
        return None
    return "".join(
        ch for ch in text if unicodedata.category(ch) not in ("Cf", "Cc") or ch in ("\n", "\t", "\r")
    )


def clean_text(value):
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    text = strip_invisible_chars(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text if text else None


def normalize_name(value):
    text = clean_text(value)
    return text.lower() if text else ""


def normalize_nit(value):
    text = clean_text(value)
    if not text:
        return ""
    text = text.replace(" ", "")
    if re.fullmatch(r"\d+\.0+", text):
        text = text.split(".", 1)[0]
    return text.lower()


def read_csv_rows(path):
    for enc in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            with open(path, "r", encoding=enc, newline="") as fh:
                reader = csv.reader(fh)
                headers = next(reader)
                rows = [row for row in reader]
            return headers, rows, enc
        except UnicodeDecodeError:
            continue
    raise RuntimeError("No se pudo leer el CSV con codificaciones utf-8-sig/utf-8/latin-1")


def map_row(row):
    # Index 10 has the second "CARGO", which has priority in this template.
    cargo = clean_text(row[10]) if len(row) > 10 else None
    if not cargo:
        cargo = clean_text(row[6]) if len(row) > 6 else None

    return {
        "nombre_empresa": clean_text(row[0]) if len(row) > 0 else None,
        "nit_empresa": clean_text(row[1]) if len(row) > 1 else None,
        "direccion_empresa": clean_text(row[2]) if len(row) > 2 else None,
        "ciudad_empresa": clean_text(row[3]) if len(row) > 3 else None,
        "correo_1": clean_text(row[4]) if len(row) > 4 else None,
        "contacto_empresa": clean_text(row[5]) if len(row) > 5 else None,
        "cargo": cargo,
        "sede_empresa": clean_text(row[7]) if len(row) > 7 else None,
        "telefono_empresa": clean_text(row[8]) if len(row) > 8 else None,
        "responsable_visita": clean_text(row[9]) if len(row) > 9 else None,
        "asesor": clean_text(row[11]) if len(row) > 11 else None,
        "correo_asesor": clean_text(row[12]) if len(row) > 12 else None,
        "zona_empresa": clean_text(row[13]) if len(row) > 13 else None,
        "caja_compensacion": clean_text(row[14]) if len(row) > 14 else None,
        "profesional_asignado": clean_text(row[15]) if len(row) > 15 else None,
        "correo_profesional": clean_text(row[16]) if len(row) > 16 else None,
        "estado": clean_text(row[17]) if len(row) > 17 else None,
        "observaciones": clean_text(row[18]) if len(row) > 18 else None,
    }


def fetch_existing_pairs(client):
    pairs = set()
    offset = 0
    batch = 1000
    while True:
        data = (
            client.table("empresas")
            .select("nit_empresa,nombre_empresa")
            .range(offset, offset + batch - 1)
            .execute()
            .data
            or []
        )
        for rec in data:
            pairs.add((normalize_nit(rec.get("nit_empresa")), normalize_name(rec.get("nombre_empresa"))))
        if len(data) < batch:
            break
        offset += batch
    return pairs


def main():
    parser = argparse.ArgumentParser(description="Importa nuevas empresas desde CSV a Supabase.")
    parser.add_argument("--csv", required=True, help="Ruta del archivo CSV")
    parser.add_argument("--apply", action="store_true", help="Aplica inserciones en BD")
    args = parser.parse_args()

    load_dotenv(".env")
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    if not url or not key:
        raise RuntimeError("Faltan SUPABASE_URL o SUPABASE_KEY en .env")
    client = create_client(url, key)

    headers, raw_rows, encoding = read_csv_rows(args.csv)
    if len(headers) != len(EXPECTED_HEADERS):
        print(f"warning: columnas esperadas={len(EXPECTED_HEADERS)} encontradas={len(headers)}")
    if headers[:5] != EXPECTED_HEADERS[:5]:
        print("warning: encabezados no coinciden exactamente con la plantilla esperada")

    mapped = []
    for row in raw_rows:
        rec = map_row(row)
        if any(v for v in rec.values()):
            mapped.append(rec)

    existing_pairs = fetch_existing_pairs(client)

    csv_pair_seen = set()
    csv_pair_dupes = 0
    to_insert = []
    already_exists = 0
    skipped_no_key = 0

    for rec in mapped:
        key_pair = (normalize_nit(rec.get("nit_empresa")), normalize_name(rec.get("nombre_empresa")))
        if not key_pair[0] and not key_pair[1]:
            skipped_no_key += 1
            continue
        if key_pair in csv_pair_seen:
            csv_pair_dupes += 1
            continue
        csv_pair_seen.add(key_pair)
        if key_pair in existing_pairs:
            already_exists += 1
            continue
        to_insert.append(rec)

    # Report how many NITs have more than one distinct name in the new batch.
    nit_names = defaultdict(set)
    for rec in to_insert:
        nit_key = normalize_nit(rec.get("nit_empresa"))
        name_key = normalize_name(rec.get("nombre_empresa"))
        if nit_key and name_key:
            nit_names[nit_key].add(name_key)
    repeated_nit_diff_name = sum(1 for names in nit_names.values() if len(names) > 1)

    print(f"encoding={encoding}")
    print(f"rows_csv={len(raw_rows)}")
    print(f"rows_mapped={len(mapped)}")
    print(f"already_exists_nit_name={already_exists}")
    print(f"duplicates_in_csv_nit_name={csv_pair_dupes}")
    print(f"skipped_no_key={skipped_no_key}")
    print(f"to_insert={len(to_insert)}")
    print(f"nits_with_multiple_names_in_new_rows={repeated_nit_diff_name}")

    if not args.apply:
        print("mode=dry_run")
        return

    if not to_insert:
        print("applied_inserts=0")
        return

    inserted = 0
    chunk_size = 200
    for idx in range(0, len(to_insert), chunk_size):
        chunk = to_insert[idx : idx + chunk_size]
        client.table("empresas").insert(chunk).execute()
        inserted += len(chunk)

    print(f"applied_inserts={inserted}")


if __name__ == "__main__":
    main()

