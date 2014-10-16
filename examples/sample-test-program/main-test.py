import re
import test_module.mistune as mistune

SOME_MARKDOWN = """
# pypwd
Dead simple password handling in Python.

The library provides a very simple API to:

 - Hash a password (using PBKDF2)
 - Validate a supplied password vs. hashed data
 - Generate a secure password

# Dependencies
```
 pip install pycrypto
```

# Usage

## Hash the password
```python
from pwd import Password
my_pass = 'VQkA.3Q@p(?x\\aAZ+im%G?B/'

# Create the hash data (salt + encoded hashed password) for storage
hash_data = Password.create(my_pass)
```

## Validate a password
```python
# Retrieve the hash_data from a persistent store
hash_data = retrieve_user_hash_data(user_id)

# Get the password to validate
supplied_password = get_user_password()

if not Password.validate(supplied_password, hash_data):
  raise SecurityException("Password don't match.")
```

## Generate a password
```python
return Password.generate(32)
```
"""


REG_CODE = re.compile(r'<code(.*?)>(.*?)</code>', re.MULTILINE | re.DOTALL)


def extract_code(html):
  code = REG_CODE.findall(html)
  for code_tpl in code:
    print "New snippet:"
    snippet = code_tpl[1].split('\n')
    lno = 0
    for line in snippet:
      lno += 1
      print " #%02d  %s" % (lno, line)


def main():
  features = [
      'table', 'fenced_code', 'footnotes',
      'autolink', 'strikethrough',
  ]
  m = mistune.Markdown(features=features)
  html = m.parse(SOME_MARKDOWN)
  extract_code(html)


if __name__ == "__main__":
    main()
