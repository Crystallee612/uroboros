
def main():

    with open('rodata.info') as f:
        lines = f.readlines()
    
    s = []
    for l in (lines):
        items = l.split()
        for item in (items):
            l = len(item)
            for i in range(0,l,2):
                s.append(".byte 0x"+item[i:i+2])
                #  s.append(".byte 0x"+item[6:])
                #  s.append(".byte 0x"+item[4:6])
                #  s.append(".byte 0x"+item[2:4])
                #  s.append(".byte 0x"+item[0:2])
    s = '\n'.join(reversed(s))
    with open('rodata_split.info', 'w') as f:
        f.write(s+'\n')
    
    with open('data.info') as f:
        lines = f.readlines()
    
    s = []
    for l in (lines):
        items = l.split()
        for item in (items):
            l = len(item)
            for i in range(0,l,2):
                s.append(".byte 0x"+item[i:i+2])
                # s.append(".byte 0x"+item[6:])
                # s.append(".byte 0x"+item[4:6])
                # s.append(".byte 0x"+item[2:4])
                # s.append(".byte 0x"+item[0:2])
    s = '\n'.join(reversed(s))
    with open('data_split.info', 'w') as f:
        f.write(s+'\n')
    
    with open('got.info') as f:
        lines = f.readlines()
    
    s = []
    for l in (lines):
        items = l.split()
        for item in (items):
            l = len(item)
            for i in range(0,l,2):
                s.append(".byte 0x"+item[i:i+2])
                # s.append(".byte 0x"+item[6:])
                # s.append(".byte 0x"+item[4:6])
                # s.append(".byte 0x"+item[2:4])
                # s.append(".byte 0x"+item[0:2])
    
    s = '\n'.join(reversed(s))
    with open('got_split.info', 'w') as f:
        f.write(s+'\n')
    
    with open('eh_frame.info') as f:
        lines = f.readlines()
    
    s = []
    for l in (lines):
        items = l.split()
        for item in (items):
            l = len(item)
            for i in range(0,l,2):
                s.append(".byte 0x"+item[i:i+2])
                # s.append(".byte 0x"+item[6:])
                # s.append(".byte 0x"+item[4:6])
                # s.append(".byte 0x"+item[2:4])
                # s.append(".byte 0x"+item[0:2])
    s = '\n'.join(reversed(s))
    with open('eh_frame_split.info', 'w') as f:
        f.write(s+'\n')
    
    
    with open('eh_frame_hdr.info') as f:
        lines = f.readlines()
    
    s = []
    for l in (lines):
        items = l.split()
        for item in (items):
            l = len(item)
            for i in range(0,l,2):
                s.append(".byte 0x"+item[i:i+2])
                # s.append(".byte 0x"+item[6:])
                # s.append(".byte 0x"+item[4:6])
                # s.append(".byte 0x"+item[2:4])
                # s.append(".byte 0x"+item[0:2])
    s = '\n'.join(reversed(s))
    with open('eh_frame_hdr_split.info', 'w') as f:
        f.write(s+'\n')


if __name__ == '__main__':
    main()
