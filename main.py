from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs


HOST_NAME = "localhost"
SERVER_PORT = 8080


class MyServer(BaseHTTPRequestHandler):
    """Обработчик GET- и POST-запросов учебного веб-приложения."""

    def do_GET(self) -> None:
        """Возвращает страницу контактов на любой GET-запрос."""
        try:
            with open("contacts.html", encoding="utf-8") as file:
                html_content = file.read()
            status_code = 200
        except FileNotFoundError:
            html_content = (
                "<!DOCTYPE html>"
                "<html lang='ru'>"
                "<head><meta charset='UTF-8'><title>Ошибка 500</title></head>"
                "<body><h1>Ошибка 500</h1>"
                "<p>Файл contacts.html не найден.</p></body>"
                "</html>"
            )
            status_code = 500

        self.send_response(status_code)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(html_content.encode("utf-8"))

    def do_POST(self) -> None:
        """Принимает данные формы и выводит их в консоль."""
        content_length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_length).decode("utf-8")
        form_data = parse_qs(post_data)

        print("Получены данные формы:")
        for field_name, field_values in form_data.items():
            print(f"{field_name}: {field_values[0]}")

        self.do_GET()


if __name__ == "__main__":
    web_server = HTTPServer((HOST_NAME, SERVER_PORT), MyServer)
    print(f"Сервер запущен: http://{HOST_NAME}:{SERVER_PORT}")

    try:
        web_server.serve_forever()
    except KeyboardInterrupt:
        pass

    web_server.server_close()
    print("Сервер остановлен")