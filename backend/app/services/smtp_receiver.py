import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from email.utils import parseaddr

from aiosmtpd.controller import Controller
from sqlalchemy import select

from app.core.config import settings
from app.core.logging.logging import get_logger
from app.db.database import async_session_maker
from app.models.models import EmailAddress, Email, Attachment, Domain
from app.services.email_parser import EmailParser


logger = get_logger(__name__)


class TempMailHandler:
    def __init__(self):
        self.parser = EmailParser()

    async def handle_DATA(self, server, session, envelope) -> str:
        mail_from = envelope.mail_from
        rcpt_tos = envelope.rcpt_tos
        data = envelope.content

        if isinstance(data, str):
            data = data.encode("utf-8")

        parsed = self.parser.parse_email(data)

        try:
            await self._store_email(
                to_addresses=rcpt_tos,
                from_address=parsed.get("from", {}).get("email") or mail_from,
                from_name=parsed.get("from", {}).get("name"),
                subject=parsed.get("subject"),
                text_body=parsed.get("text_body"),
                html_body=parsed.get("html_body"),
                raw_source=data.decode("utf-8", errors="replace"),
                headers=parsed.get("headers"),
                attachments=parsed.get("attachments", []),
            )
        except Exception as e:
            logger.error(f"Failed to store incoming email: {e}")
            return "451 Internal storage error"

        logger.info(f"Received email from {mail_from} to {rcpt_tos}")
        return "250 OK"

    async def _store_email(
        self,
        to_addresses: List[str],
        from_address: str,
        from_name: Optional[str],
        subject: Optional[str],
        text_body: Optional[str],
        html_body: Optional[str],
        raw_source: str,
        headers: Optional[Dict[str, Any]],
        attachments: List[Dict[str, Any]],
    ) -> None:
        async with async_session_maker() as db:
            for to_address in to_addresses:
                to_address = to_address.lower().strip()

                result = await db.execute(
                    select(EmailAddress).where(
                        EmailAddress.email == to_address,
                        EmailAddress.status == "active",
                    )
                )
                email_address = result.scalar_one_or_none()

                if not email_address:
                    logger.warning(f"Received email for unknown address: {to_address}")
                    continue

                if email_address.expires_at is not None and email_address.expires_at < datetime.utcnow():
                    email_address.status = "expired"
                    await db.commit()
                    continue

                email = Email(
                    email_address_id=email_address.id,
                    message_id=(headers or {}).get("Message-ID") or f"gen-{abs(hash(raw_source))}",
                    subject=subject[:500] if subject else None,
                    from_address=(from_address or "")[:255],
                    from_name=(from_name or "")[:255] if from_name else None,
                    text_body=text_body,
                    html_body=html_body,
                    raw_source=raw_source,
                    headers=headers or {},
                    status="received",
                    size_bytes=len(raw_source.encode("utf-8")) if raw_source else 0,
                    received_at=datetime.utcnow(),
                )
                db.add(email)
                await db.flush()

                for att in attachments:
                    db.add(
                        Attachment(
                            email_id=email.id,
                            filename=att.get("filename", "attachment"),
                            content_type=att.get("content_type"),
                            size=att.get("size", 0),
                            content_id=att.get("content_id"),
                            is_inline=att.get("is_inline", False),
                            data=att.get("data"),
                        )
                    )

                email_address.emails_count = (email_address.emails_count or 0) + 1

                domain_result = await db.execute(
                    select(Domain).where(Domain.domain == email_address.domain)
                )
                domain_obj = domain_result.scalar_one_or_none()
                if domain_obj:
                    domain_obj.emails_received = (domain_obj.emails_received or 0) + 1

                await db.commit()

                try:
                    from app.api.v1.endpoints.websocket import notify_new_email
                    await notify_new_email(str(email_address.id), email)
                except Exception:
                    pass


class SMTPReceiver:
    def __init__(self):
        self.controller: Optional[Controller] = None
        self.handler = TempMailHandler()

    def start(self) -> None:
        if self.controller is not None:
            return
        host = settings.SMTP_HOST
        port = settings.SMTP_PORT
        self.controller = Controller(
            self.handler,
            hostname=host,
            port=port,
            decode_data=False,
        )
        try:
            self.controller.start()
            logger.info(f"SMTP receiver started on {host}:{port}")
        except Exception as e:
            logger.error(f"Failed to start SMTP receiver on {host}:{port}: {e}")
            self.controller = None

    def stop(self) -> None:
        if self.controller is not None:
            try:
                self.controller.stop()
            except Exception as e:
                logger.error(f"Error stopping SMTP receiver: {e}")
            finally:
                self.controller = None
                logger.info("SMTP receiver stopped")


receiver = SMTPReceiver()
