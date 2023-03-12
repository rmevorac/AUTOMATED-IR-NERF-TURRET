

with open('zerod_matrix.txt', 'r') as fread:
    with open('new_matrix.txt', 'w') as fwrite:
        while 1:
            line = fread.readline()

            if line == '':
                break

            fwrite.write(line.replace('	', ', '))