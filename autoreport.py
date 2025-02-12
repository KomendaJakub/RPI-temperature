#!/usr/bin/env python3

import datetime
import sqlite3 
import smtplib
from email.message import EmailMessage
from confidential import EMAIL, PASSWORD, MAIL_SERVER

now = datetime.now()
print(now)


