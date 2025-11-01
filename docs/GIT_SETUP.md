# 🔐 Настройка Git и GitHub

Решение проблемы аутентификации при push в GitHub.

## ❌ Проблема

```
remote: Invalid username or token.
Password authentication is not supported for Git operations.
fatal: Authentication failed
```

## 💡 Решение

GitHub больше не поддерживает пароли. Есть 2 варианта:

---

## Вариант 1: Personal Access Token (PAT) 🔑

### Шаг 1: Создайте токен на GitHub

1. Зайдите на GitHub → **Settings** (в профиле)
2. Слева внизу: **Developer settings**
3. **Personal access tokens** → **Tokens (classic)**
4. **Generate new token** → **Generate new token (classic)**
5. Настройте токен:
   - **Note**: `recommend-project`
   - **Expiration**: 90 days (или No expiration)
   - **Scopes**: Отметьте `repo` (полный доступ к репозиториям)
6. **Generate token**
7. **СКОПИРУЙТЕ ТОКЕН!** (он больше не покажется)

Пример токена: `ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

### Шаг 2: Используйте токен вместо пароля

```bash
# При push введите:
Username: ваш_github_username
Password: ghp_xxxxxxxxxxxx  # ← ваш токен, не пароль!
```

### Шаг 3: Сохраните токен (опционально)

```bash
# Linux/Mac - сохранить навсегда
git config --global credential.helper store

# Windows - использовать Credential Manager
git config --global credential.helper wincred

# После этого токен сохранится после первого ввода
```

---

## Вариант 2: SSH ключи (рекомендуется) 🔒

### Шаг 1: Генерация SSH ключа

```bash
# Генерация нового SSH ключа
ssh-keygen -t ed25519 -C "your_email@example.com"

# Нажимайте Enter для всех вопросов
# Ключ сохранится в ~/.ssh/id_ed25519
```

### Шаг 2: Копируйте публичный ключ

```bash
# Linux/Mac/WSL
cat ~/.ssh/id_ed25519.pub

# Windows (PowerShell)
type %USERPROFILE%\.ssh\id_ed25519.pub

# Скопируйте весь вывод (начинается с ssh-ed25519...)
```

### Шаг 3: Добавьте ключ на GitHub

1. GitHub → **Settings** → **SSH and GPG keys**
2. **New SSH key**
3. **Title**: `WSL Ubuntu` (или название вашей машины)
4. **Key**: Вставьте скопированный публичный ключ
5. **Add SSH key**

### Шаг 4: Измените remote URL на SSH

```bash
# Проверьте текущий remote
git remote -v

# Если используется HTTPS (начинается с https://):
git remote set-url origin git@github.com:marychev/recommend.git

# Проверьте изменения
git remote -v
# Должно показать: git@github.com:marychev/recommend.git
```

### Шаг 5: Проверьте SSH подключение

```bash
ssh -T git@github.com

# Должно вернуть:
# Hi username! You've successfully authenticated...
```

---

## 🚀 Теперь можно пушить

```bash
git add .
git commit -m "Add recommendation system"
git push origin main
```

---

## 🔄 Быстрое решение для первого push

### Вариант A: С токеном

```bash
# 1. Создайте токен на GitHub (см. выше)

# 2. Push с указанием токена в URL
git push https://ghp_YOUR_TOKEN@github.com/marychev/recommend.git main

# 3. Или введите токен когда попросит пароль
git push
# Username: marychev
# Password: ghp_YOUR_TOKEN
```

### Вариант B: С SSH (рекомендуется)

```bash
# 1. Генерируйте ключ и добавьте на GitHub (см. выше)

# 2. Измените URL
git remote set-url origin git@github.com:marychev/recommend.git

# 3. Push
git push origin main
```

---

## 🐛 Troubleshooting

### Ошибка: "Permission denied (publickey)"

**Причина**: SSH ключ не добавлен в ssh-agent

**Решение**:
```bash
# Запустите ssh-agent
eval "$(ssh-agent -s)"

# Добавьте ключ
ssh-add ~/.ssh/id_ed25519

# Попробуйте снова
git push
```

### Ошибка: "Host key verification failed"

**Решение**:
```bash
# Добавьте GitHub в known_hosts
ssh-keyscan github.com >> ~/.ssh/known_hosts

# Попробуйте снова
git push
```

### Токен не работает

**Проверьте**:
1. Токен скопирован полностью (начинается с `ghp_`)
2. Срок действия не истек
3. Scope `repo` включен

---

## 📝 Git команды для проекта

```bash
# Проверка статуса
git status

# Добавить все файлы
git add .

# Commit (не больше 8 слов - по вашим предпочтениям!)
git commit -m "Add music recommendation system"

# Push в main
git push origin main

# Создать новую ветку
git checkout -b feature/kafka-integration

# Посмотреть историю
git log --oneline

# Посмотреть изменения
git diff
```

---

## 🔒 Безопасность

### ⚠️ ВАЖНО:

1. **НЕ коммитьте** `.env` файлы с секретами
2. **НЕ коммитьте** токены и пароли
3. **Используйте** `.gitignore` (уже настроен ✅)
4. **Токен GitHub** храните в безопасном месте

### Проверка .gitignore:

```bash
# Проверьте что .env в ignore
cat .gitignore | grep .env
# Должно показать: .env

# Проверьте что файл игнорируется
git status
# .env НЕ должен показываться в списке
```

---

## 🎯 Рекомендации

### Для WSL/Ubuntu:

**Лучший вариант - SSH ключи:**
1. Генерируете один раз
2. Добавляете на GitHub
3. Больше никаких паролей!

### Для Windows:

**Git Credential Manager:**
```bash
git config --global credential.helper wincred
```

После первого ввода токена, он сохранится автоматически.

---

## 📚 Дополнительные ресурсы

- [GitHub: Creating a Personal Access Token](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token)
- [GitHub: Connecting with SSH](https://docs.github.com/en/authentication/connecting-to-github-with-ssh)
- [Git Credential Storage](https://git-scm.com/book/en/v2/Git-Tools-Credential-Storage)

---

## ✅ Быстрый чек-лист

Перед первым push:

- [ ] Создал токен на GitHub (или SSH ключ)
- [ ] Проверил `.gitignore` (есть .env, venv, __pycache__)
- [ ] Убрал из репозитория конфиденциальные данные
- [ ] Проверил что все работает (`pytest -v`)
- [ ] Commit message не больше 8 слов
- [ ] Ready to push! 🚀

---

**Выберите один из вариантов и попробуйте снова!** 🔐

