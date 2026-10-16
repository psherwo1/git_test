import sys, json, os
root = sys.argv[1]
for d in sorted(os.listdir(root)):
    for dp, dn, fns in os.walk(os.path.join(root, d)):
        for f in fns:
            if f.endswith('.json'):
                j = json.load(open(os.path.join(dp, f), encoding='utf-8'))
                def find(o, path=''):
                    if isinstance(o, dict):
                        for k, v in o.items():
                            kl = k.lower()
                            if any(s in kl for s in ('size','scale','meta','name','categor','tags','packing','channel','normal','physical')) and not isinstance(v,(dict,list)):
                                print(d, path + '/' + k, '=', str(v)[:120])
                            find(v, path + '/' + k)
                    elif isinstance(o, list):
                        for i, v in enumerate(o[:40]): find(v, path + '[%d]' % i)
                find(j)
