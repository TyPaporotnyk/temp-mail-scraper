from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TempMailSelectors:
    email_input: str = "#eposta_adres"
    refresh_button: str = "a.yoket-link"
    cookie_accept_button: str = '[aria-label="Consent"]'

    inbox_container: str = "#epostalar"
    inbox_rows: str = "#epostalar ul.mailler > li.mail"
    empty_inbox: str = "#epostalar .eposta-bekleniyor"

    row_link: str = ":scope > a"
    row_sender: str = ":scope > a > .gonderen"
    row_subject: str = ":scope > a > .baslik"
    row_timestamp: str = ":scope > a > .zaman"

    message_container: str = "#eposta_oku"
    message_sender_container: str = "#eposta_oku .mail-oku-gonderen"
    message_subject: str = "#eposta_oku .mail-oku-gonderen > strong"
    message_timestamp: str = "#eposta_oku .mail-oku-gonderen > .zaman"
    message_iframe: str = "#eposta_oku iframe#iframe"


SELECTORS = TempMailSelectors()
