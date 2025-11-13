
import re

def parse_email(text):
    addresses = re.findall(r"[A-ZÅÄÖa-zåäö]+ \d+, \d+ [A-ZÅÄÖa-zåäö]+", text)
    return addresses
