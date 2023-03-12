import json
import requests
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Label, Button, Header, Footer, Input, RadioButton, RadioSet, Static


class HTTPApp(App[str]):

    CSS_PATH = "browser.css"
    TITLE = "HTTP Client"
    dark = False

    REQUEST_TEXT = "[b]Request Line[/b]"
    STATUS_TEXT = "[b]Status[/b]"
    HEADERS_TEXT = "[b]Headers[/b]"
    CONTENT_TEXT = "[b]Response Content[/b]"

    def compose(self) -> ComposeResult:
        yield Header()
        with Container():
            with Vertical(id="request-view"):
                with Horizontal():
                    with RadioSet():
                        yield RadioButton("GET", value=True)
                        yield RadioButton("POST")
                    yield Input(placeholder="URL", id="url")
                    yield Button("GO", id="go", variant="primary")
            with Vertical(id="response-view"):
                yield Static(self.REQUEST_TEXT, id="request_line")
                yield Static(self.STATUS_TEXT, id="status")
                with Container(id="response-container"):
                    with Vertical(id="header-view"):
                        yield Static(self.HEADERS_TEXT, id="headers")
                    with Vertical(id="content-view"):
                        yield Static(self.CONTENT_TEXT, id="content", expand=True)

    def on_mount(self) -> None:
        self.method = "GET"
        self.query_one("#url", Input).focus()

    def on_radio_set_changed(self, event: RadioSet.Changed) -> None:
        self.method = f"{event.pressed.label}"

    def update_headers(self, headers):
        header_text = "\n".join(
            f"[b]{header}[/b]: {value}"
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
        try:
            response = requests.request(self.method, url)
        except requests.RequestException as e:
            return self.handle_error(e)
        self.query_one("#request_line", Static).update(f"{self.method} {url}")
        self.update_headers(response.headers)
        self.query_one("#status", Static).update(
            f"{response.status_code} {response.reason}"
        )
        if response.headers.get('Content-Type').startswith('application/json'):
            response_text = json.dumps(response.json(), indent=2)
        else:
            response_text = response.text
        self.query_one("#content", Static).update(response_text)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self.submit()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.submit()


if __name__ == "__main__":
    app = HTTPApp()
    app.run()
