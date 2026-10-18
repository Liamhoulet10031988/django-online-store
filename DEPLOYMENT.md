# Проверка и развёртывание приложения

Приложение: https://orangepi5b.taila2acdb.ts.net/

Документация API: https://orangepi5b.taila2acdb.ts.net/api/docs/

GitHub Actions выполняет `tests → linters → build → deploy`. Проверки идут
на каждом push и Pull Request. Публикация и deploy идут при push в
`feature/ci-cd` и `develop`, поэтому полный результат можно проверить до Merge.

## Сервер и изоляция

Production-конфигурация рассчитана на Linux ARM64, в том числе Orange Pi.
Сборка использует `ubuntu-24.04-arm`, а не x86 runner. Нужны Docker Engine,
Compose v2 или новее и доступ по SSH.

Compose-проект `django-online-store` имеет отдельные сеть и тома. Он не
использует ресурсы других приложений. Не выполняйте общие `docker system prune`,
`docker volume prune` или `docker image prune` на сервере с другими проектами.

Создайте отдельный каталог пользователя деплоя и серверный `.env` по
`.env.template`. Все демонстрационные значения замените:

```bash
mkdir -p ~/django-online-store/nginx
chmod 700 ~/django-online-store
chmod 600 ~/django-online-store/.env
```

Тома PostgreSQL, Redis, static и media получают префикс `django-online-store_`.
Не подключайте существующую базу или том другого приложения.

Контейнеры ограничены по памяти; логи ротируются. Политика перезапуска —
`unless-stopped`. Проверьте `systemctl is-enabled docker`; перезагружать
сервер ради проверки не нужно.

## Доступ через домашнюю сеть

По умолчанию приложение слушает `127.0.0.1:8088`.
`HTTP_BIND_ADDRESS` и `HTTP_PORT` в `.env` задают адрес и порт Nginx.
Для доступа из LAN задайте адрес интерфейса или `0.0.0.0`. Порты PostgreSQL,
Redis и Gunicorn на хосте не публикуются.

GitHub-hosted runner не видит адреса `192.168.x.x`. Workflow подключает его
к существующей сети Tailscale, затем выполняет обычный SSH. Публично открывать
SSH домашнего устройства не нужно.

В админке Tailscale создайте тег `tag:django-deploy` и разрешите ему только
TCP 22 нужного сервера. Сохраните существующие правила. Создайте auth key
с этим тегом, параметрами Reusable и Ephemeral; если требуется подтверждение
устройств — также Pre-approved. Сохраните его в `TAILSCALE_AUTHKEY`.

Для публичной ссылки можно отдельно настроить Tailscale Funnel: он открывает
только выбранный HTTP-сервис через HTTPS. Потребуется доступ к админке сети.
LAN-адрес сам по себе недоступен преподавателю из интернета.

## SSH

Создайте отдельный ключ вне репозитория:

```powershell
ssh-keygen -t ed25519 -C "django-store-deploy" -f "$env:USERPROFILE\.ssh\django_store_deploy"
```

Публичную часть добавьте в `~/.ssh/authorized_keys` сервера. Закрытая часть
хранится только локально и в `SSH_PRIVATE_KEY`.

Через уже проверенное SSH-подключение узнайте публичный ключ сервера:

```bash
cat /etc/ssh/ssh_host_ed25519_key.pub
```

В `SSH_KNOWN_HOSTS` сохраните строку:

```text
TAILSCALE_SERVER_IP ssh-ed25519 PUBLIC_SERVER_KEY
```

Это публичный host key сервера, а не пользовательский закрытый ключ.

## Docker Hub и GitHub Secrets

Создайте публичный Docker Hub-репозиторий `django-online-store` и токен с
правом публикации. Публичный образ сервер получает без пароля Docker Hub.
Для закрытого образа отдельно выполните `docker login` на сервере.

В GitHub откройте `Settings → Secrets and variables → Actions`:

| Secret | Значение |
| --- | --- |
| `DOCKERHUB_USERNAME` | логин Docker Hub |
| `DOCKERHUB_TOKEN` | токен Docker Hub с правом публикации |
| `TAILSCALE_AUTHKEY` | tagged reusable ephemeral auth key |
| `SSH_HOST` | Tailscale IP сервера |
| `SSH_USER` | пользователь Linux |
| `SSH_PORT` | обычно `22` |
| `SSH_PRIVATE_KEY` | полный отдельный закрытый ключ |
| `SSH_KNOWN_HOSTS` | IP и публичный host key сервера |
| `DEPLOY_PATH` | абсолютный путь к каталогу приложения |

Настройте все Secrets до push. Сервер должен быть online в Tailscale.
Токены, пароли и содержимое `.env` не добавляются в Git.

## Этапы развёртывания

1. Тесты выполняются с отдельными PostgreSQL и Redis на runner.
2. Flake8 и isort выполняются после тестов.
3. ARM64 runner собирает образ и публикует SHA коммита и `latest`.
4. Deploy подключается к Tailscale и проверяет SSH host key.
5. На сервер копируются только Compose и конфигурация Nginx.
6. Deploy-runner скачивает из Docker Hub образ точного SHA и передаёт его
   через `docker save | ssh ... docker load`. Серверу не нужен прямой доступ
   к Docker Hub; настройки общего Docker daemon не меняются. Базовые образы
   PostgreSQL, Redis и Nginx должны быть подготовлены на сервере заранее.
7. `DOCKER_IMAGE` серверного `.env` получает новый SHA; Compose использует
   `--pull never` и ждёт готовности web. Остальные значения `.env` сохраняются.
8. Worker и beat стартуют после готовности Django и завершения миграций.
9. Nginx перечитывает upstream, а HTTP-проверка подтверждает ответ приложения.

Ошибки тестов, линтеров, сборки, запуска или HTTP завершают pipeline
неуспешно. Общая очистка Docker-ресурсов не выполняется.

## Проверка результата

В каталоге приложения:

```bash
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml exec -T nginx nginx -t
curl --fail http://127.0.0.1:8088/
curl --fail http://127.0.0.1:8088/api/docs/
docker compose -f docker-compose.prod.yml logs --tail=80 web nginx celery_worker celery_beat
```

Перед повторной сдачей проверьте успешный **push-запуск** со всеми четырьмя
jobs и публичную ссылку приложения. В PR-запуске публикация и deploy
пропускаются: сервер обновляется только на push в разрешённую ветку.
