def sanitize(name):
    changed = False
    bits = name.split(".")
    if len(bits) == 3:
        bits[0] = bits[0] + bits[1]
        bits[1] = bits[2]
        del bits[2]
        changed = True
    if len(bits) == 2:
        if bits[1] != "jpg":
            bits[1] = "jpg"
            changed = True
        if "-" in bits[0]:
            parts = bits[0].split("-")
            base = parts[0]
        elif " (" in bits[0]:
            parts = bits[0].split(" (")
            frags = parts[1].split(")")
            bits[0] = parts[0] + "-" + frags[0]
            changed = True
            base = parts[0]
        else:
            base = bits[0]
        i = 0
        for char in base:
            if char.islower():
                ref = base[:i]
                break
            i += 1
        else:
            ref = base
        return ref, changed, bits[0] + "." + bits[1]
    raise ValueError(f"{name} is badly formed")
