"""csvlite - minimal CSV line parser for internal exports. DO NOT MODIFY.

Rules:
  - fields separated by `,`
  - a field may be wrapped in double quotes; inside, `""` is a literal quote
  - quoted fields may contain commas
  - whitespace is significant (no trimming)
  - empty string -> [""]  (one empty field, like csv module)
"""


def parse_line(line):
    fields, buf, in_q, i = [], [], False, 0
    while i < len(line):
        ch = line[i]
        if in_q:
            if ch == '"':
                if i + 1 < len(line) and line[i + 1] == '"':
                    buf.append('"')
                    i += 1
                else:
                    in_q = False
            else:
                buf.append(ch)
        else:
            if ch == '"':
                in_q = True
            elif ch == ",":
                fields.append("".join(buf))
                buf = []
            else:
                buf.append(ch)
        i += 1
    fields.append("".join(buf))
    return fields
