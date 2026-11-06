# Bulk-Mail-Automation
IN this need to have list of emails in the csv format, then run the py file after that it will find the validate mail ids , then run the py file it will automatically send the mails.
The excel should containt the hr or hiring manager mail in this format:- company,email

Setup (once):
  pip install dnspython
  Gmail: turn on 2-step verification, create an App Password (Google Account > Security > App passwords).
  export GMAIL_ADDRESS="Mail Id"
  export GMAIL_APP_PASSWORD="App Password"
  Put your CV in this folder as: CV.docx

Steps:
  python send_applications.py --validate      # checks syntax + mail server (MX), writes validation_report.csv
  python send_applications.py                 # dry run: prints the emails, sends nothing
  python send_applications.py --send          # really sends (max 25/day, random 60-120 s gaps)
