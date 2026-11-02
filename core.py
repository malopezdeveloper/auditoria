"""Read-only hardware inventory and versioned local audit format."""
import base64
import json
import os
import platform
import subprocess
import uuid
from datetime import datetime, timezone
from pathlib import Path

STATES = ('Pendiente', 'PASS', 'FAIL', 'Dudoso', 'No probado', 'No aplicable')

def now():
    return datetime.now(timezone.utc).isoformat()

def device(category, name, identifier, details=None, os_status='No informado'):
    return dict(id=str(identifier), category=category or 'Sin clasificar', name=name or 'Sin nombre',
                details=details or {}, os_status=os_status or 'No informado', result='Pendiente',
                notes='', reviewer='', reviewed_at='', history=[], photos=[])

def read(path):
    try:
        return Path(path).read_text(errors='replace').strip()
    except OSError:
        return ''

def collect():
    audit = dict(schema=1, audit_id=str(uuid.uuid4()), created_at=now(), technician='', lot='',
                 identity={'hostname': platform.node(), 'os': platform.platform()}, devices=[], errors=[])
    if platform.system() == 'Windows':
        script = Path(__file__).with_name('collector.ps1').read_text(encoding='utf-8')
        encoded = base64.b64encode(script.encode('utf-16le')).decode('ascii')
        run = subprocess.run(['powershell.exe', '-NoProfile', '-NonInteractive', '-EncodedCommand', encoded],
                             capture_output=True, timeout=240, creationflags=0x08000000)
        if run.returncode:
            raise RuntimeError(run.stderr.decode('utf-8', errors='replace'))
        raw = json.loads(run.stdout.decode('utf-8-sig'))
        audit['identity'].update(raw['identity'])
        audit['errors'] = raw['errors']
        for i, d in enumerate(raw['devices']):
            audit['devices'].append(device(d.get('category'), d.get('name'), d.get('id') or f'unknown:{i}', d.get('details'), d.get('os_status')))
    elif platform.system() == 'Linux':
        audit['identity'].update({k: read('/sys/class/dmi/id/'+v) for k,v in
            {'manufacturer':'sys_vendor','model':'product_name','serial':'product_serial'}.items()})
        for category, pattern in [('PCI','/sys/bus/pci/devices/*'), ('USB','/sys/bus/usb/devices/*'),
                                  ('Red','/sys/class/net/*'), ('Audio','/sys/class/sound/card*'),
                                  ('Cámara','/sys/class/video4linux/*'), ('Entrada','/sys/class/input/event*'),
                                  ('Almacenamiento','/sys/block/*'), ('Batería / alimentación','/sys/class/power_supply/*'),
                                  ('Pantalla','/sys/class/drm/card*-*')]:
            import glob
            for item in sorted(glob.glob(pattern)):
                p = Path(item)
                details = {key: read(p/key) for key in ('vendor','device','manufacturer','product','model','serial','uevent','status','capacity','size','type') if (p/key).is_file()}
                if category == 'Entrada': details['name'] = read(p/'device/name')
                name = details.get('product') or details.get('model') or details.get('name') or p.name
                audit['devices'].append(device(category, name, str(p), details))
        audit['devices'].append(device('CPU', platform.processor() or 'Procesador', 'linux:cpu', {'cpuinfo':read('/proc/cpuinfo')}))
        audit['devices'].append(device('RAM', 'Memoria del sistema', 'linux:memory', {'meminfo':read('/proc/meminfo')}))
        audit['errors'].append('Linux: inventario sysfs básico; PCI puede mostrar identificadores numéricos. SN DMI puede requerir permisos. RAM por módulo y SMART no implementados.')
    else:
        raise RuntimeError('Sistema compatible: Windows o Linux.')
    for i,d in enumerate(audit['devices']):
        # Separate inventory rows can share a provider identifier.
        d['row_id'] = str(uuid.uuid4())
    return audit

def record(d, state, technician, notes):
    if state not in STATES: raise ValueError('Estado desconocido')
    if not technician.strip(): raise ValueError('Indica el nombre del técnico.')
    if state in ('FAIL','Dudoso','No aplicable') and not notes.strip():
        raise ValueError('Indica el motivo en observaciones.')
    event = dict(result=state, reviewer=technician.strip(), notes=notes, reviewed_at=now())
    d.update(event)
    d['history'].append(event.copy())

def save(audit, path):
    path=Path(path)
    temp=path.with_suffix(path.suffix+'.tmp')
    with temp.open('w',encoding='utf-8') as f:
        json.dump(audit,f,ensure_ascii=False,indent=2)
        f.flush(); os.fsync(f.fileno())
    os.replace(temp,path)

def load(path):
    data=json.loads(Path(path).read_text(encoding='utf-8'))
    if data.get('schema') != 1 or not isinstance(data.get('devices'),list):
        raise ValueError('Formato de auditoría no compatible')
    required={'id','row_id','category','name','result','history','photos','details','notes','os_status'}
    for d in data['devices']:
        if not isinstance(d,dict) or not required.issubset(d) or d['result'] not in STATES:
            raise ValueError('Dispositivo de auditoría inválido')
    return data
