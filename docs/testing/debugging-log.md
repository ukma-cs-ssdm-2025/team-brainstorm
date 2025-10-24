# Debugging Log – "Update Book Role Check"

## Симптом
Після зміни коду тест `test_update_book_forbidden_for_non_librarian` почав падати:

```
E       AssertionError: assert 200 == 403
E        +  where 200 = response.status_code
```

API неправильно дозволяло звичайному користувачу (`X-Role: user`) редагувати книгу, хоча це повинно бути дозволено лише бібліотекарю.

---

## Корінна причина
Під час експерименту з налагодження ми **навмисно ввели логічну помилку** в перевірку ролі у функції `update_book()`:

```python
# Помилкова версія
if x_role.lower() != "user":
    raise HTTPException(status_code=403, detail="Only user can edit books")
```

Умову переплутали — замість перевіряти, що **редагувати може лише librarian**, код перевіряв на `"user"`, тим самим повністю міняючи логіку доступу.

---

## Виправлення
Після аналізу падіння тесту ми повернули оригінальну умову:

```python
# Виправлена версія
if x_role.lower() != "librarian":
    raise HTTPException(status_code=403, detail="Only librarian can edit books")
```

Після цього всі тести знову успішно пройшли (`pytest -q` показав `✓ all tests passed`).

---

## Урок
- Маленька зміна логічної умови може повністю змінити бізнес-логіку системи.  
- Автоматичні тести виявляють такі помилки миттєво — навіть якщо код виглядає “нормально”.
- Наступного разу:
  - не комітити експериментальні зміни без тестів;
  - частіше проганяти тести після навіть дрібних правок;
  - використовувати TDD/CI, щоб помилка ловилася відразу.

---

**Файл:** `src/api/routes/books.py`  
**Тест:** `tests/test_reservations.py::test_update_book_forbidden_for_non_librarian` 
