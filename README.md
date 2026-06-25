# Лабораторная работа 2

## Задача

Скрипт читает публикации Дональда Трампа из CSV-файла, отправляет тексты в LLM через DeepSeek API и сохраняет саммаризацию каждой публикации в JSON.

Для каждой публикации модель возвращает:

- `summary` - краткое содержание одним предложением;
- `key_points` - 1-3 ключевых пункта из текста.

## Используемые данные

Входной файл: `./trump_truths.csv`

Источник датасета: https://www.kaggle.com/datasets/epurevsuren/donald-trump-truths-dataset/data

## Требования

- Python 3.10+
- API-ключ DeepSeek

Скрипт использует только стандартную библиотеку Python, поэтому устанавливать зависимости не нужно.

## Настройка API-ключа

В PowerShell:

```powershell
$env:DEEPSEEK_API_KEY="ваш_api_ключ"
```

## Запуск

```powershell
python lab2.py --input trump_truths.csv --output results.json --limit 20
```

Параметр `--limit` задает количество строк из CSV, которые будут отправлены в LLM. Для демонстрации достаточно 20-50 строк, чтобы не тратить много API-запросов.

## Результат

После запуска появится файл:

```
results.json
```

Файл содержит:

- название модели;
- путь к входному CSV;
- количество обработанных строк;
- список результатов саммаризации.

## Пример структуры результата

```json
{
  "model": "deepseek-chat",
  "input_file": "trump_truths.csv",
  "processed_count": 1,
  "items": [
    {
      "id": "113404826487996526",
      "date": "2024-11-01T00:18:46.050Z",
      "source_length": 269,
      "summary": "The post criticizes Kamala Harris and Joe Biden during the election campaign.",
      "key_points": [
        "Criticism of political opponents",
        "Election campaign message",
        "Call to support voting"
      ]
    }
  ]
}
```
