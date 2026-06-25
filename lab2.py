import argparse
import csv
import json
import os
import sys
import time
import urllib.error
import urllib.request


DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"
DEFAULT_MODEL = "deepseek-chat"


def parse_args():
    parser = argparse.ArgumentParser(
        description="Read CSV rows, summarize texts with DeepSeek API, save JSON results."
    )
    parser.add_argument("--input", required=True, help="Path to input CSV file.")
    parser.add_argument("--output", required=True, help="Path to output JSON file.")
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Maximum number of CSV rows to process. Default: 20.",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"DeepSeek model name. Default: {DEFAULT_MODEL}.",
    )
    parser.add_argument(
        "--sleep",
        type=float,
        default=0.4,
        help="Pause between API requests in seconds. Default: 0.4.",
    )
    return parser.parse_args()


def read_rows(path, limit):
    rows = []
    with open(path, "r", encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        required_columns = {"id", "date", "text"}
        missing_columns = required_columns - set(reader.fieldnames or [])
        if missing_columns:
            missing = ", ".join(sorted(missing_columns))
            raise ValueError(f"Input CSV is missing required columns: {missing}")

        for row in reader:
            text = (row.get("text") or "").strip()
            if not text:
                continue

            rows.append(
                {
                    "id": row.get("id", ""),
                    "date": row.get("date", ""),
                    "text": text,
                    "favorites": row.get("favorites", ""),
                    "retweets": row.get("retweets", ""),
                    "replies": row.get("replies", ""),
                }
            )
            if len(rows) >= limit:
                break

    return rows


def build_prompt(row):
    return (
        "Summarize this social media post. Return only valid JSON with keys "
        '"summary" and "key_points". '
        '"summary" must be one short sentence. '
        '"key_points" must be an array of 1-3 short strings. '
        "Do not add any extra keys.\n\n"
        f"Post date: {row['date']}\n"
        f"Favorites: {row['favorites']}\n"
        f"Retweets: {row['retweets']}\n"
        f"Replies: {row['replies']}\n"
        f"Text: {row['text']}"
    )


def call_deepseek(api_key, model, prompt):
    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a data analysis assistant. "
                    "Always return strict JSON and no Markdown."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
    }
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        DEEPSEEK_API_URL,
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            response_body = response.read().decode("utf-8")
    except urllib.error.HTTPError as error:
        details = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"DeepSeek API error {error.code}: {details}") from error
    except urllib.error.URLError as error:
        raise RuntimeError(f"Network error while calling DeepSeek API: {error}") from error

    data = json.loads(response_body)
    content = data["choices"][0]["message"]["content"]
    return parse_model_json(content)


def parse_model_json(content):
    cleaned = content.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:].strip()
    return json.loads(cleaned)


def normalize_item(row, model_result):
    return {
        "id": row["id"],
        "date": row["date"],
        "source_length": len(row["text"]),
        "summary": model_result.get("summary", ""),
        "key_points": model_result.get("key_points", []),
    }


def save_results(path, results):
    output_dir = os.path.dirname(os.path.abspath(path))
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    with open(path, "w", encoding="utf-8") as json_file:
        json.dump(results, json_file, ensure_ascii=False, indent=2)
        json_file.write("\n")


def main():
    args = parse_args()
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        print(
            "Error: set DEEPSEEK_API_KEY before running the script.",
            file=sys.stderr,
        )
        return 1

    rows = read_rows(args.input, args.limit)
    items = []

    for index, row in enumerate(rows, start=1):
        print(f"Processing row {index}/{len(rows)}: id={row['id']}")
        prompt = build_prompt(row)
        model_result = call_deepseek(api_key, args.model, prompt)
        items.append(normalize_item(row, model_result))
        if index < len(rows):
            time.sleep(args.sleep)

    results = {
        "model": args.model,
        "input_file": args.input,
        "processed_count": len(items),
        "items": items,
    }
    save_results(args.output, results)
    print(f"Saved {len(items)} items to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
