def truncate(string, max=60):
    if not string:
        return ""
    if string[:7] == "Chinese":
        string = string[8:9].capitalize() + string[9:]
    else:
        string = string.replace("Chinese famille", "famille")
    if len(string) <= max:
        return string
    # has_date = truncate_at_date(string)
    # if has_date and len(has_date) <= max:
    #     return has_date
    seps = [pos for pos, char in enumerate(string) if char in [",", ";", "."]]
    result = string
    for sep in seps:
        if sep > max:
            break
        result = string[:sep] + "."
    if len(result) < max:
        return result
    # no smart point to truncate at found, so truncate at first symbol after max
    rest = string[max:]
    terminators = [rest.find(" "), rest.find("."), rest.find(","), rest.find(";")]
    min = 9999
    for term in terminators:
        if term >= 0 and term < min:
            min = term
    return string[: max + min]


def truncate_at_date(string):
    # look for date in brackets
    lp = string.find("(")
    if lp > 0:
        rp = string.find(")")
        if rp > lp:
            paren = string[lp + 1 : rp]
            bits = paren.split("-")
            if len(bits) == 2:
                paren = bits[1]
            else:
                # sometimes a different - character is used
                paren = paren[-2:]
            if paren.isdigit():
                return string[: rp + 1]
    # look for date outside brackets
    no_commas = string.replace(",", "")
    colon = no_commas.find(":")
    if colon:
        no_commas = no_commas[:colon]
    nums = [int(s) for s in no_commas.split() if s.isdigit()]
    if nums:
        num = str(nums[0])
        if len(num) > 1:
            pos = string.find(num)
            return string[: pos + len(num)]
    return ""
