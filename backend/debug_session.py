import asyncio
import httpx
import smtplib
from email.mime.text import MIMEText
from app.db.database import async_session_maker
from sqlalchemy import text

async def main():
    async with httpx.AsyncClient(base_url="http://127.0.0.1:8000/api/v1") as c:
        r = await c.post("/addresses/generate", json={})
        d = r.json()
        email = d["addresses"][0]["email"]
        eid = d["addresses"][0]["id"]
        token = d["token"]
        print("generated", email)
        msg = MIMEText("Your code is 654321 and link https://verify.example.com/abc")
        msg["From"] = "test@example.com"
        msg["To"] = email
        msg["Subject"] = "Your OTP"
        with smtplib.SMTP("127.0.0.1", 2525) as s:
            s.sendmail("test@example.com", [email], msg.as_string())
        print("smtp sent")
        import asyncio as a
        await a.sleep(1)
        r2 = await c.get(f"/emails/{eid}", headers={"Authorization": f"Bearer {token}"})
        print("detail status", r2.status_code)
        if r2.status_code == 200:
            j = r2.json()
            print("subject", j["subject"])
            print("otp_codes", j["otp_codes"])
            print("verification_links", j["verification_links"])
        else:
            print(r2.text)

asyncio.run(main())
