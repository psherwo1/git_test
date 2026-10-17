import sys, zipfile, os
src = sys.argv[1]; dst_root = sys.argv[2]
ALLOWED = ('.jpg','.jpeg','.png','.exr','.tif','.tiff','.json','.txt')
for zn in sorted(os.listdir(src)):
    if not zn.endswith('.zip'): continue
    if len(sys.argv) > 3 and zn != sys.argv[3]: continue
    name = zn[:-4]
    out = os.path.join(dst_root, name)
    os.makedirs(out, exist_ok=True)
    with zipfile.ZipFile(os.path.join(src, zn)) as z:
        for m in z.infolist():
            fn = m.filename
            norm = fn.replace('\\','/')
            if norm.startswith('/') or ':' in norm or '..' in norm.split('/'):
                print('REFUSE', zn, fn); continue
            if m.is_dir(): continue
            ext = os.path.splitext(norm)[1].lower()
            tag = 'EXTRACT' if ext in ALLOWED else 'SKIP'
            print(tag, zn, fn, m.file_size)
            if tag == 'EXTRACT':
                target = os.path.realpath(os.path.join(out, norm))
                if not target.startswith(os.path.realpath(out)+os.sep):
                    print('REFUSE2', fn); continue
                os.makedirs(os.path.dirname(target), exist_ok=True)
                with z.open(m) as fsrc, open(target,'wb') as fdst:
                    fdst.write(fsrc.read())

