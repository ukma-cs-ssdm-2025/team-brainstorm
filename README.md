[![CI](https://github.com/ukma-cs-ssdm-2025/team-brainstorm/actions/workflows/ci.yml/badge.svg)](https://github.com/ukma-cs-ssdm-2025/team-brainstorm/actions/workflows/ci.yml)

# 📚 Brainstorm Project

Командний проєкт для управління бібліотекою.  
Розробляється в рамках курсу (НаУКМА).


Супроводжувач репозиторію (Repo Maintainer) - Федін Володимир

Супроводжувач CI (CI Maintainer) - Виговський Владислав 

Керівник документації (Documentation Lead) - Зінченко Вероніка

Керівник трекера завдань (Issue Tracker Lead) - Ковтонюк Анастасія

Керівник вимогг (Requirements Lead) - Ковтонюк Анастасія

Керівник якості (Quality Lead) - Федін Володимир

Керівник простежуваності (Traceability Lead) - Виговський Владислав 

Керівник документації (Documentation Lead) - Зінченко Вероніка


## 📂Артефакти

Усі артефакти зберігаються в каталозі [`docs/api/`](docs/api/):
- [api-design](docs/api/api-design.md)
- [index](docs/api/index.html)
- [openapi-generated](docs/api/openapi-generated.yaml)
- [quality-attributes](docs/api/quality-attributes.md)

## Architecture

Усі артефакти зберігаються в каталозі [`docs/architecture/`](docs/architecture/):
- [high-level-design](docs/architecture/high-level-design.md)
- [traceability-matrix](docs/architecture/traceability-matrix.md)
- [uml1](docs/architecture/uml1)
- [uml2](docs/architecture/uml2)
- [uml3](docs/architecture/uml3)

## Code-quality

Усі артефакти зберігаються в каталозі [`docs/code-quality/`](docs/code-quality/):
- [progress](docs/code-quality/progress.md)
- [review-report](docs/code-quality/review-report.md)
- [static-analysis](docs/code-quality/static-analysis.md)

## Requirements

Усі артефакти зберігаються в каталозі [`docs/requirements/`](docs/requirements/):
- [quality-scenarios](docs/requirements/quality-scenarios.md)
- [requirements](docs/requirements/requirements.md)
- [rtm](docs/requirements/rtm.md)

- ## ⚙️ Як запустити
```bash
# Клонувати репозиторій
git clone https://github.com/ukma-cs-ssdm-2025/team-brainstorm.git
cd team-brainstorm

# Створити віртуальне середовище
python -m venv venv
source venv/bin/activate   # або venv\Scripts\activate на Windows

# Встановити залежності
pip install -r requirements.txt

# Запустити локально
uvicorn src.api.main:app --reload
```

API буде доступне за адресою:  
👉 http://127.0.0.1:8000/docs


## 📝 Політика розробки
- **Форматування**: Black + Flake8  
- **Статичний аналіз**: mypy  
- **Обов’язкові PR-и**: мінімум 1 approve    

## 👥 Команда
- Зінченко Вероніка
- Федін Володимир   
- Ковтонюк Анастасія
- Виговський Владислав 
