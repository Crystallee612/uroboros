def not_hex(d):
    try:
        int(d,16)
        return False
    except:
        return True

def parse(item):
    h1 = item[7:8]
    h2 = item[4:6]
    h3 = item[2:4]
    h4 = item[0:2]
    return "S_0x%X" % int(h1+h2+h3+h4, 16)

def main():
    with open("init_array.info") as f:
        lines = f.readlines()

    start_index = 0
    for i in range(len(lines)):
        l = lines[i]
        if "not found" in l:
            start_index = -1
        elif "Contents of section" in l:
            start_index = i+1

    lines = lines[start_index:]
    ctors = [] # C++ global ctors
    for l in lines:
        items = l.strip().split()
        # addr = items[0]
        for item in items[1:]:
            if len(item) != 8 or not_hex(item):
                break
            else:
                ctors.append(parse(item)+"\n")

    with open("init_array_new.info", 'w') as f:
        f.writelines(ctors)
    return ctors