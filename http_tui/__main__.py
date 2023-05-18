import json
from typing import Dict
from urllib import parse

import requests
from rich.markup import escape
from textual import on
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import (
    Button,
    Header,
    Input,
    RadioButton,
    RadioSet,
    Select,
    Static,
)


class HTTPApp(App[str]):
    CSS_PATH = "app.css"
    TITLE = "HTTP Client"
    HTTP_METHODS = ["GET", "POST", "DELETE"]
    dark = False

    REQUEST_TEXT = "[b]Request Line[/b]"
    STATUS_TEXT = "[b]Status[/b]"
    HEADERS_TEXT = "[b]Headers[/b]"
    CONTENT_TEXT = "[b]Response Content[/b]"

    def __init__(self, *args, **kwargs) -> None:
        self.method = "GET"
        self.content_type = ""
        super().__init__(*args, **kwargs)

    def compose(self) -> ComposeResult:
        yield Header()
        with Container():
            with Vertical(id="request-view"):
                with Horizontal():
                    yield Select(
                        [(method, method) for method in self.HTTP_METHODS],
                        value=self.HTTP_METHODS[0],
                        allow_blank=False,
                    )
                    yield Input(placeholder="URL", id="url")
                    yield Button("GO", id="go", variant="primary")
            with Vertical(id="request-body-view", classes="hidden"):
                with Horizontal():
                    with RadioSet(id="content-type"):
                        yield RadioButton(
                            "application/x-www-form-urlencoded",
                            value=True,
                        )
                        yield RadioButton("application/json")
                    yield Input(placeholder="Request Body", id="request-body")
            with Vertical(id="response-view"):
                yield Static(self.REQUEST_TEXT, id="request_line")
                yield Static(self.STATUS_TEXT, id="status")
                with Container(id="response-container"):
                    with Vertical(id="header-view"):
                        yield Static(self.HEADERS_TEXT, id="headers")
                    with Vertical(id="content-view"):
                        yield Static(
                            self.CONTENT_TEXT,
                            id="content",
                            expand=True,
                        )

    def on_mount(self) -> None:
        self.query_one("#url", Input).focus()

    @on(Select.Changed)
    def select_changed(self, event: Select.Changed) -> None:
        self.method = str(event.value)

        body_view = self.query_one("#request-body-view")
        if self.method == "POST":
            body_view.remove_class("hidden")
        else:
            body_view.add_class("hidden")

    def on_radio_set_changed(self, event: RadioSet.Changed) -> None:
        if event.radio_set.id == "content-type":
            self.content_type = f"{event.pressed.label}"

    def update_headers(self, headers):
        header_text = "\n".join(
            f"[b]{header}[/b]: {escape(value)}"
            for header, value in headers.items()
        )
        self.query_one("#headers", Static).update(header_text)

    def handle_error(self, exception):
        self.query_one("#request_line", Static).update(self.REQUEST_TEXT)
        self.query_one("#status", Static).update(self.STATUS_TEXT)
        self.query_one("#headers", Static).update(self.HEADERS_TEXT)
        self.query_one("#content", Static).update(
            f"[bold red]Error[/]\n\n{exception}"
        )

    def submit(self):
        url = self.query_one("#url", Input).value
        headers = {}
        params = {}
        body = self.get_request_body()

        if self.method == "POST":
            if self.content_type:
                headers["content-type"] = self.content_type

            if self.content_type == "application/json":
                params["json"] = body
            else:
                params["data"] = body
        try:
            response = requests.request(
                self.method, url, headers=headers, **params
            )
        except requests.RequestException as e:
            self.handle_error(e)
            return

        self.query_one("#request_line", Static).update(f"{self.method} {url}")
        self.update_headers(response.headers)
        status_line = f"{response.status_code} {response.reason}"
        self.query_one("#status", Static).update(
            ("[green]" if response.ok else "[red]") + f"{status_line}[/]"
        )
        if response.headers.get("Content-Type").startswith("application/json"):
            response_text = json.dumps(response.json(), indent=2)
        else:
            response_text = response.text
        self.query_one("#content", Static).update(escape(response_text))

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self.submit()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.submit()

    def get_request_body(self) -> Dict:
        body = self.query_one("#request-body").value
        if not body:
            return {}
        try:
            return json.loads(body)
        except ValueError:
            return parse.parse_qs(body)


def main():
    app = HTTPApp()
    app.run()


if __name__ == "__main__":
    main()
