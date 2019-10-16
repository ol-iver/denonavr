with open('avr3313.txt', 'r') as f, open('ir_code.py', 'w') as w:
    line = f.readline()
    while line:
        if line[:5] == 'RCKSK':
            name = line[53:-1].replace(' ', '_')
            name = name.replace('-', '_')
            name = name.replace('+', '_')
            name = name.replace('(', '_')
            name = name.replace(')', '_')
            name = name.replace('/', '_')
            name = name.replace(':', '_')
            name = name.replace('__', '_')
            name = name.replace('▼', 'DOWN')
            name = name.replace('▲', 'UP')
            name = name.replace('.', '_')
            if name[-1] == '_':
                name = name[:-1]

            code = line[:12]
            w.write(f'{name} = \'{code}\'\n')
        line = f.readline()
