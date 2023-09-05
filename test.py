from db import mail

mail_to = "granthbagadia2004@gmail.com"

idt = "njcndjcndj"

message = f"""From: From granthbagadia2004@gmail.com
To: To Person {mail_to}
Subject: Order Placed Successfully

This is a confirmation for your order on CampusChic.
Your Order ID is {idt}
"""

mail(mail_to, message)
