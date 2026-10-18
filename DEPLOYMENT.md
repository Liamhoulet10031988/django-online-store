# Автоматическая проверка и развёртывание проекта

Проект использует GitHub Actions для последовательного выполнения этапов
`tests → linters → build → deploy`. Проверки запускаются при каждом `push` и
для каждого pull request. Публикация Docker-образа и развёртывание выполняются
только после успешных проверок при обновлении ветки `develop`.

## Подготовка удалённого сервера

Подойдёт сервер Ubuntu с открытым SSH-портом и портом `80` для HTTP. Порты
PostgreSQL `5432`, Redis `6379` и Gunicorn `8000` не нужно открывать наружу:
они доступны только сервисам внутри сети Docker Compose.

Установите Docker Engine и плагин Docker Compose по официальной инструкции
Docker. Добавьте пользователя для деплоя в группу `docker`, затем войдите на
сервер повторно:

```bash
sudo usermod -aG docker "$USER"
```

Создайте каталог приложения:

```bash
sudo mkdir -p /opt/django-online-store/nginx
sudo chown -R "$USER":"$USER" /opt/django-online-store
```

Создайте на сервере файл `/opt/django-online-store/.env` по образцу
`.env.template`. Замените все демонстрационные значения. Файл `.env` не
передаётся через GitHub Actions и не хранится в репозитории.

Создайте в Docker Hub репозиторий `django-online-store`. Для этой конфигурации
он должен быть публичным: сервер получает образ без хранения Docker Hub-токена.
Если репозиторий закрытый, сначала отдельно выполните `docker login` на сервере.

Для автоматического запуска Docker после перезагрузки сервера:

```bash
sudo systemctl enable --now docker
```

Все контейнеры в `docker-compose.prod.yml` используют политику
`restart: unless-stopped`, поэтому приложение также запускается повторно после
перезагрузки сервера.

## SSH-ключ для GitHub Actions

Создайте отдельный ключ без парольной фразы на своём компьютере:

```bash
ssh-keygen -t ed25519 -C "github-actions-deploy" -f ./github_actions_deploy
```

Добавьте содержимое `github_actions_deploy.pub` в файл
`~/.ssh/authorized_keys` пользователя сервера. Закрытый ключ из файла
`github_actions_deploy` сохраните только в секрете `SSH_PRIVATE_KEY`.

После добавления ключа локальные файлы ключа следует удалить безопасным для
вашей операционной системы способом. Не добавляйте их в Git.

## Секреты GitHub

В репозитории откройте `Settings → Secrets and variables → Actions` и добавьте:

| Secret | Назначение |
| --- | --- |
| `DOCKERHUB_USERNAME` | имя пользователя Docker Hub |
| `DOCKERHUB_TOKEN` | токен доступа Docker Hub, не пароль |
| `SSH_HOST` | IP-адрес или домен сервера |
| `SSH_USER` | пользователь сервера для деплоя |
| `SSH_PORT` | SSH-порт, обычно `22` |
| `SSH_PRIVATE_KEY` | полный текст закрытого SSH-ключа |
| `DEPLOY_PATH` | каталог проекта, например `/opt/django-online-store` |

Секреты доступны workflow только во время выполнения и не должны находиться в
исходном коде, `.env.template`, сообщениях коммитов или описании pull request.

## Что происходит при запуске workflow

1. Job `test` поднимает PostgreSQL и Redis, проверяет миграции, применяет их и
   запускает весь набор Django-тестов.
2. Job `lint` запускается только после тестов и проверяет Flake8 и сортировку
   импортов.
3. Job `build` запускается только после линтеров. В feature-ветках и pull
   request он проверяет локальную сборку. В `develop` образ дополнительно
   публикуется в Docker Hub с тегами `latest` и SHA коммита.
4. Job `deploy` запускается только для `push` в `develop`: копирует на сервер
   production-конфигурацию, получает новый образ и перезапускает сервисы.

Если тесты, линтеры или сборка завершатся с ошибкой, зависимые jobs не
запустятся и развёртывание не произойдёт.

## Проверка после развёртывания

На сервере выполните:

```bash
cd /opt/django-online-store
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs --tail=100 web
docker compose -f docker-compose.prod.yml logs --tail=100 nginx
curl --fail http://127.0.0.1/
```

Затем откройте в браузере IP-адрес или домен сервера. Если используется домен
и HTTPS, добавьте сертификат и укажите адрес с `https://` в
`CSRF_TRUSTED_ORIGINS` серверного `.env`.
