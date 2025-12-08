[![CI](https://github.com/ukma-cs-ssdm-2025/team-brainstorm/actions/workflows/ci.yml/badge.svg)](https://github.com/ukma-cs-ssdm-2025/team-brainstorm/actions/workflows/ci.yml)

# 📚 Brainstorm Project

> Командний проєкт для управління бібліотекою  
> Розробляється в рамках курсу Software System Design and Modeling (НаУКМА)

---

## 👥 Команда

| Учасник |
---------|
| Федін Володимир |
| Виговський Владислав |
| Зінченко Вероніка |
| Ковтонюк Анастасія |
---

## 📂 Структура проєкту

```
team-brainstorm/
├── docs/                    # Документація
│   ├── api/                 # API специфікації
│   ├── architecture/        # Архітектурні рішення
│   ├── code-quality/        # Звіти про якість коду
│   ├── requirements/        # Вимоги та RTM
│   ├── refactoring/         # Документація рефакторингу
│   ├── reliability/         # Тестування надійності
│   ├── testing/             # Тестова документація
│   └── validation/          # Валідація вимог
├── src/                     # Вихідний код
│   ├── api/                 # API endpoints
│   ├── core/                # Основна бізнес-логіка
│   ├── data/                # Робота з даними
│   └── services/            # Сервіси
├── tests/                   # Тести
├── Labs/                    # Лабораторні роботи (Lab01-Lab10)
├── frontend/                # Frontend код
├── data/                    # Дані та фікстури
└── requirements.txt         # Python залежності
```

---

## 📚 Документація

### 🎯 API
Всі артефакти: [`docs/api/`](docs/api/)
- [API Design](docs/api/api-design.md) - Дизайн REST API
- [OpenAPI Specification](docs/api/openapi-generated.yaml) - Автогенерована специфікація
- [Quality Attributes](docs/api/quality-attributes.md) - Атрибути якості
- [Interactive Docs](docs/api/index.html) - Інтерактивна документація

### 🏗️ Архітектура
Всі артефакти: [`docs/architecture/`](docs/architecture/)
- [High-Level Design](docs/architecture/high-level-design.md) - Загальний дизайн системи
- [Traceability Matrix](docs/architecture/traceability-matrix.md) - Матриця простежуваності
- [UML Diagrams](docs/architecture/) - Діаграми класів, компонентів та послідовностей

### ✅ Якість коду
Всі артефакти: [`docs/code-quality/`](docs/code-quality/)
- [Progress Report](docs/code-quality/progress.md) - Прогрес покращення якості
- [Review Report](docs/code-quality/review-report.md) - Звіти code review
- [Static Analysis](docs/code-quality/static-analysis.md) - Результати статичного аналізу

### 📋 Вимоги
Всі артефакти: [`docs/requirements/`](docs/requirements/)
- [Requirements](docs/requirements/requirements.md) - Функціональні та нефункціональні вимоги
- [Quality Scenarios](docs/requirements/quality-scenarios.md) - Сценарії якості
- [RTM (Requirements Traceability Matrix)](docs/requirements/rtm.md) - Матриця простежуваності вимог

### 🔧 Рефакторинг
Всі артефакти: [`docs/refactoring/`](docs/refactoring/)

### 🧪 Тестування
Всі артефакти: [`docs/testing/`](docs/testing/)

### ✔️ Валідація
Всі артефакти: [`docs/validation/`](docs/validation/)

---

- ## ⚙️ Як запустити
### Передумови
- Python 3.10+
- Git

### Встановлення та запуск

```bash
# 1. Клонувати репозиторій
git clone https://github.com/ukma-cs-ssdm-2025/team-brainstorm.git
cd team-brainstorm

# 2. Створити віртуальне середовище
python -m venv .venv

# 3. Активувати віртуальне середовище
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# 4. Встановити залежності
pip install -r requirements.txt

# 5. Запустити сервер
uvicorn src.api.main:app --reload
```

**API буде доступне за адресою:**  
👉 **http://127.0.0.1:8000**  
📄 **Документація:** http://127.0.0.1:8000/docs

---
## 🧪 Тестування

```bash
# Запустити всі тести
pytest

# Запустити з покриттям
pytest --cov=src --cov-report=html

# Запустити конкретний тест
pytest tests/test_api.py::test_specific_function

# Запустити тести з verbose
pytest -v
```

---

## 📊 CI/CD

Проєкт використовує GitHub Actions для автоматизації:

- ✅ Lint перевірки (flake8, black)
- ✅ Type checking (mypy)
- ✅ Unit тести (pytest)
- ✅ Integration тести
- ✅ Coverage звіти

Цей проєкт розроблено для освітніх цілей в НаУКМА.


## 📝 Політика розробки
- **Форматування**: Black + Flake8  
- **Статичний аналіз**: mypy  
- **Обов’язкові PR-и**: мінімум 1 approve    

Розроблено з ❤️ командою Brainstorm | НаУКМА 2025-2026
