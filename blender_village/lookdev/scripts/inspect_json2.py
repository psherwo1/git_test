import sys, json
j = json.load(open(sys.argv[1], encoding='utf-8'))
for m in j.get('maps', []):
    print({k: v for k, v in m.items() if k not in ('uri',)})
for m in j.get('meta', []): print(m)
print([k for k in j.keys()])
print(j.get('tags'), j.get('categories'))
