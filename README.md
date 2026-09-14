# 📄 Document Analysis System

AI-система для автоматического анализа документов закупок: извлечение сущностей,
классификация типов документов и валидация по бизнес-правилам.

![Tests](https://github.com/vbat-data/document-analysis-system/actions/workflows/tests.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.11-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104-009688)
![Coverage](https://img.shields.io/badge/coverage-84%25-brightgreen)
![License](https://img.shields.io/badge/license-MIT-green)

## ✨ Возможности

- 📥 Загрузка документов форматов **PDF / DOCX / XLSX**
- 🔍 Автоматическое извлечение сущностей (NER, RuBERT)
- 🏷 Классификация типа документа (договор / счёт / акт)
- ✅ Валидация по бизнес-правилам
- 💾 Хранение результатов в SQLite
- 📊 REST API с автодокументацией (Swagger UI)
- 🧪 Тесты (pytest, 20 тестов, покрытие ~84%)
- ⚙️ CI на GitHub Actions

## 🏗 Архитектура

```
┌──────────┐   ┌─────────┐   ┌─────────┐   ┌──────────┐   ┌────────┐
│  Upload  │ → │ Parser  │ → │   NER   │ → │ Validator│ → │   DB   │
│ (FastAPI)│   │ PDF/DOCX│   │ RuBERT  │   │  Rules   │   │SQLite  │
└──────────┘   └─────────┘   └─────────┘   └──────────┘   └────────┘
```

## 🚀 Быстрый старт

### Требования
- Python 3.11+

### Установка

```bash
git clone https://github.com/vbat-data/document-analysis-system.git
cd document-analysis-system

python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Запуск

```bash
uvicorn src.main:app --reload
```

Откройте Swagger UI: http://127.0.0.1:8000/docs

## 📡 Примеры API

```bash
# Проверка статуса
curl http://127.0.0.1:8000/health

# Загрузка документа
curl -X POST http://127.0.0.1:8000/documents/upload \
  -F "file=@data/samples/contract.docx"

# Список обработанных документов
curl http://127.0.0.1:8000/documents
```

## 🧪 Тесты

```bash
pytest
```

## 🛠 Стек

| Слой | Технологии |
|------|-----------|
| API | FastAPI, Uvicorn |
| Валидация | Pydantic v2 |
| БД | SQLAlchemy 2.0, SQLite |
| ML / NLP | Transformers, RuBERT, PyTorch |
| Парсинг | pdfplumber, python-docx, pandas |
| Тесты | pytest, pytest-cov, httpx |
| CI | GitHub Actions |

## 📁 Структура проекта

```
document-analysis-system/
├── src/
│   ├── main.py                    # FastAPI entry point
│   ├── config.py                  # Settings
│   ├── schemas.py                 # Pydantic models
│   ├── database.py                # SQLAlchemy
│   ├── ml_models.py               # NER wrapper
│   ├── document_processor.py      # Pipeline
│   ├── validators.py              # Business rules
│   └── api/routes.py              # Endpoints
├── tests/                         # pytest suites
├── requirements.txt
├── pyproject.toml
└── README.md
```

## 🗺 Roadmap

- [x] MVP: FastAPI + NER + валидация + тесты + CI
- [ ] Fine-tuning RuBERT на доменных данных
- [ ] OCR для сканированных PDF
- [ ] Экспорт результатов в Excel
- [ ] Streamlit-дашборд
- [ ] Интеграция с 1С:Документооборот
- [ ] Docker

## 📝 Лицензия

MIT