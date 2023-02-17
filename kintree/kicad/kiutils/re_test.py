import re

test_s = ['Diodes:1F90-86', '34567_90', '1F90-86_1_1', 'Dio-des:GT45-789_0_0', 'Test_diode:TH4567:1', 'Test_diode:TH4567:1_0_0']

result = []
for s in test_s:
    find1 = re.match(r"^(.+?):(.+?)_(\d+?)_(\d+?)$", s)
    if find1:
        lib = find1.group(1)
        symbol = find1.group(2)
        unit_id = find1.group(3)
        style_id = find1.group(4)
        result.append(f'{s} [1]> {lib} | {symbol} | {unit_id} | {style_id}')

    find2 = re.match(r"^(.+?):(.+?)$", s)
    if find2:
        lib = find2.group(1)
        symbol = find2.group(2)
        result.append(f'{s} [2]> {lib} | {symbol}')

    find3 = re.match(r"^(.+?)_(\d+?)_(\d+?)$", s)
    if find3:
        symbol = find3.group(1)
        unit_id = find3.group(2)
        style_id = find3.group(3)
        result.append(f'{s} [3]> {symbol} | {unit_id} | {style_id}')

    if not find1 and not find2 and not find3:
        result.append(f'{s} >> {s}')

for i in result:
    print(i)