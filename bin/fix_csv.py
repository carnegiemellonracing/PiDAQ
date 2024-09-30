import sys

fileName = sys.argv[1]

with open(fileName, 'r') as file:
    with open('fixed_' + fileName, 'a') as fixed_file:
        fixed_file.write(file.readline())
        for line in file:
            fixed_file.write(line.replace('[', '"[').replace(']', ']"'))
