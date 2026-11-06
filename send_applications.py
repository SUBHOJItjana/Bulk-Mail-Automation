#!/usr/bin/env python3
"""Validate recruiter emails, then send tailored job applications with your CV.

Setup (once):
  pip install dnspython
  Gmail: turn on 2-step verification, create an App Password (Google Account > Security > App passwords).
  export GMAIL_ADDRESS="subhojitdjana@gmail.com"
  export GMAIL_APP_PASSWORD="ukjm nbea idic dgpr"
  Put your CV in this folder as: Subhojit_Jana_Java_Developer_CV.docx

Steps:
  python send_applications.py --validate      # checks syntax + mail server (MX), writes validation_report.csv
  python send_applications.py                 # dry run: prints the emails, sends nothing
  python send_applications.py --send          # really sends (max 25/day, random 60-120 s gaps)
"""
import argparse, csv, os, random, re, smtplib, sys, time
from email.message import EmailMessage

CV = "Subhojit_Jana_Java_Developer_CV.docx"
SUBJECT = "Application for Software/Java Developer Position"
SENT_LOG = "sent_log.csv"
REPORT = "validation_report.csv"
DAILY_LIMIT = 25
PATTERN = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)+$")

BODY = """Dear Hiring Team at {company},

I am writing to express my interest in Software/Java Developer opportunities at {company}. I am a Java Developer with about 1 year 9 months of experience building and supporting enterprise applications, and I would like to contribute to your engineering team. My resume is attached.

I currently work at MasterCom Technology Services as a Java Developer on a project for Tata Telecom Services. My work includes:
- Developing and maintaining Java 17 applications with Spring Boot, Spring MVC, Hibernate/JPA and Spring Security
- Building and integrating RESTful APIs and writing optimized SQL queries and stored procedures (SQL Server, PostgreSQL, MySQL)
- Writing JUnit tests, taking part in code reviews, and working in Agile teams with Git, Maven, Jira and Jenkins/GitLab CI/CD
- Using AI-assisted tools such as GitHub Copilot to speed up coding and debugging

I also have front-end exposure to React.js, Angular, JavaScript and HTML/CSS, and a B.E. in Computer Engineering from the University of Mumbai (2024).

I would be glad to discuss how I can add value at {company}. If you would rather not receive job enquiries at this address, please let me know and I will not write again.

Thank you for your time and consideration.

Warm regards,
Subhojit Jana
Thane, Maharashtra, India
subhojitdjana@gmail.com
linkedin.com/in/jana-subhojitb09a88291
github.com/SUBHOJItjana
"""

def has_mx(domain):
    import dns.resolver
    try:
        return len(dns.resolver.resolve(domain, "MX")) > 0
    except Exception:
        try:  # fall back to A record (some domains receive mail without MX)
            return len(dns.resolver.resolve(domain, "A")) > 0
        except Exception:
            return False

def load_contacts():
    with open("contacts.csv", newline="", encoding="utf8") as f:
        return [{"company": r["company"].strip(), "email": r["email"].strip().lower()} for r in csv.DictReader(f)]

def validate(rows, check_mx=True):
    seen, out = set(), []
    for r in rows:
        status = "ok"
        if not PATTERN.match(r["email"]):
            status = "bad_syntax"
        elif r["email"] in seen:
            status = "duplicate"
        elif check_mx and not has_mx(r["email"].split("@")[1]):
            status = "no_mail_server"
        seen.add(r["email"])
        out.append({**r, "status": status})
    with open(REPORT, "w", newline="", encoding="utf8") as f:
        w = csv.DictWriter(f, fieldnames=["company", "email", "status"])
        w.writeheader(); w.writerows(out)
    return out

def already_sent():
    if not os.path.exists(SENT_LOG):
        return set()
    with open(SENT_LOG, newline="", encoding="utf8") as f:
        return {r["email"] for r in csv.DictReader(f)}

def build(row, sender):
    m = EmailMessage()
    m["From"], m["To"], m["Subject"] = sender, row["email"], SUBJECT
    m.set_content(BODY.format(company=row["company"]))
    with open(CV, "rb") as f:
        m.add_attachment(f.read(), maintype="application",
                         subtype="vnd.openxmlformats-officedocument.wordprocessingml.document", filename=CV)
    return m

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--validate", action="store_true")
    ap.add_argument("--send", action="store_true")
    ap.add_argument("--no-mx", action="store_true", help="skip mail-server check (syntax only)")
    a = ap.parse_args()

    rows = validate(load_contacts(), check_mx=not a.no_mx)
    good = [r for r in rows if r["status"] == "ok"]
    print(f"Validated {len(rows)} addresses: {len(good)} ok, {len(rows)-len(good)} rejected (see {REPORT})")
    for r in rows:
        if r["status"] != "ok":
            print(f"  REJECTED {r['email']}: {r['status']}")
    if a.validate:
        return

    sender = os.environ.get("GMAIL_ADDRESS", "subhojitdjana@gmail.com")
    todo = [r for r in good if r["email"] not in already_sent()][:DAILY_LIMIT]
    if not os.path.exists(CV):
        sys.exit(f"CV not found: put {CV} in this folder.")
    if not a.send:
        print(f"\nDRY RUN: {len(todo)} emails would be sent. Preview of the first one:\n")
        if todo:
            m = build(todo[0], sender)
            print(f"To: {m['To']}\nSubject: {m['Subject']}\n\n{m.get_body().get_content()}")
        return

    pw = os.environ["GMAIL_APP_PASSWORD"]
    new_log = not os.path.exists(SENT_LOG)
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s, open(SENT_LOG, "a", newline="", encoding="utf8") as lf:
        s.login(sender, pw)
        w = csv.writer(lf)
        if new_log:
            w.writerow(["email", "company", "time"])
        for i, r in enumerate(todo, 1):
            try:
                s.send_message(build(r, sender))
                w.writerow([r["email"], r["company"], time.strftime("%Y-%m-%d %H:%M:%S")]); lf.flush()
                print(f"[{i}/{len(todo)}] sent to {r['company']} <{r['email']}>")
            except Exception as e:
                print(f"[{i}/{len(todo)}] FAILED {r['email']}: {e}")
            if i < len(todo):
                time.sleep(random.randint(60, 120))
    print("Done. Check your Gmail inbox for bounce notices and remove those addresses from contacts.csv.")

if __name__ == "__main__":
    main()
