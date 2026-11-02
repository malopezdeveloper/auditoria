import base64
import json
import queue
import threading
import uuid
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from core import STATES, collect, device, record, save, load, now

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('PULSIA · Auditor de hardware 0.1')
        self.geometry('1250x800'); self.minsize(950,650)
        self.audit=None; self.dirty=False; self.selected=None; self.busy=False
        self.results=queue.Queue()
        style=ttk.Style(self); style.theme_use('clam')
        style.configure('Treeview',rowheight=27)
        top=ttk.Frame(self,padding=12); top.pack(fill='x')
        for title,cmd in [('Nueva detección',self.scan),('Abrir auditoría',self.open),('Guardar',self.save),('Añadir dispositivo',self.manual),('Datos del equipo',self.identity)]:
            ttk.Button(top,text=title,command=cmd).pack(side='left',padx=4)
        ttk.Label(top,text='Técnico:').pack(side='left',padx=(20,4))
        self.tech=tk.StringVar(); ttk.Entry(top,textvariable=self.tech,width=23).pack(side='left')
        ttk.Label(top,text='Lote:').pack(side='left',padx=4)
        self.lot=tk.StringVar(); ttk.Entry(top,textvariable=self.lot,width=15).pack(side='left')
        self.tech.trace_add('write',self.changed); self.lot.trace_add('write',self.changed)
        self.summary=tk.StringVar(value='Comienza con Nueva detección. Todos los resultados requieren revisión manual.')
        ttk.Label(self,textvariable=self.summary,padding=10).pack(fill='x')
        self.query=tk.StringVar(); self.query.trace_add('write',lambda *_:self.refresh())
        bar=ttk.Frame(self,padding=8);bar.pack(fill='x')
        ttk.Label(bar,text='Buscar por categoría, nombre, identificador o resultado:').pack(side='left')
        ttk.Entry(bar,textvariable=self.query,width=45).pack(side='left',padx=8)
        pane=ttk.Panedwindow(self,orient='vertical');pane.pack(fill='both',expand=True,padx=12)
        listing=ttk.Frame(pane);pane.add(listing,weight=3)
        cols=('category','name','os_status','result')
        self.tree=ttk.Treeview(listing,columns=cols,show='headings',selectmode='browse')
        for c,label,w in zip(cols,('Categoría','Dispositivo','Estado del SO','Resultado auditor'),(170,520,140,160)):
            self.tree.heading(c,text=label);self.tree.column(c,width=w)
        scroll=ttk.Scrollbar(listing,command=self.tree.yview);self.tree.configure(yscrollcommand=scroll.set)
        scroll.pack(side='right',fill='y');self.tree.pack(fill='both',expand=True)
        for tag,color in [('PASS','#ddf3e4'),('FAIL','#ffb3b3'),('Dudoso','#fff0bd')]: self.tree.tag_configure(tag,background=color)
        self.tree.bind('<<TreeviewSelect>>',self.select)
        detail=ttk.Frame(pane,padding=8);pane.add(detail,weight=2)
        self.details=tk.Text(detail,height=8,wrap='word',state='disabled');self.details.pack(fill='both',expand=True)
        ttk.Label(detail,text='Observaciones (pulsa Registrar para conservarlas):').pack(anchor='w')
        self.notes=tk.Text(detail,height=3,wrap='word');self.notes.pack(fill='x')
        row=ttk.Frame(detail);row.pack(fill='x',pady=8)
        self.state=tk.StringVar(value='Pendiente')
        ttk.Combobox(row,textvariable=self.state,values=STATES,state='readonly',width=20).pack(side='left')
        ttk.Button(row,text='Registrar resultado',command=self.confirm).pack(side='left',padx=8)
        ttk.Button(row,text='Adjuntar fotografías',command=self.photos).pack(side='left')
        self.status=tk.StringVar(value='Detección ≠ confirmación funcional. Revisa también dispositivos desconocidos y componentes ausentes.')
        ttk.Label(self,textvariable=self.status,padding=10).pack(fill='x')
        self.protocol('WM_DELETE_WINDOW',self.close); self.after(150,self.poll)

    def identity(self):
        if not self.audit:return
        win=tk.Toplevel(self);win.title('Identificación y avisos de detección');win.geometry('800x600')
        text=tk.Text(win,wrap='word');text.pack(fill='both',expand=True)
        text.insert('1.0',json.dumps({'identity':self.audit['identity'],'avisos':self.audit['errors']},ensure_ascii=False,indent=2));text.configure(state='disabled')
    def changed(self,*_):
        if self.audit: self.dirty=True
    def safe(self):
        if self.busy:
            messagebox.showinfo('Detección','Espera a que termine la detección.');return False
        return not self.dirty or messagebox.askyesno('Cambios sin guardar','¿Descartar los cambios sin guardar?')
    def scan(self):
        if not self.safe():return
        self.busy=True; self.status.set('Detectando hardware; puede tardar varios minutos…')
        def work():
            try:self.results.put((True,collect()))
            except Exception as exc:self.results.put((False,str(exc)))
        threading.Thread(target=work,daemon=True).start()
    def poll(self):
        try:
            ok,data=self.results.get_nowait();self.busy=False
            if ok:
                self.audit=data;self.audit['technician']=self.tech.get();self.audit['lot']=self.lot.get()
                self.selected=None;self.dirty=True;self.refresh()
                self.status.set('Detección terminada. '+('Avisos: '+ ' | '.join(data['errors']) if data['errors'] else 'Inventario listo para revisión.'))
            else:messagebox.showerror('Detección fallida',data);self.status.set('No se pudo completar la detección.')
        except queue.Empty:pass
        self.after(150,self.poll)
    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        if not self.audit:return
        q=self.query.get().casefold()
        for d in self.audit['devices']:
            if q and q not in ' '.join(str(d.get(k,'')) for k in ('category','name','id','result')).casefold():continue
            self.tree.insert('', 'end',iid=d['row_id'],values=tuple(d[k] for k in ('category','name','os_status','result')),tags=(d['result'],))
        ds=self.audit['devices']; pending=sum(d['result']=='Pendiente' for d in ds)
        self.summary.set(f"{len(ds)} registros · {pending} pendientes · {sum(d['result']=='FAIL' for d in ds)} FAIL · Auditoría {self.audit['audit_id']}")
    def current(self):
        return next((d for d in self.audit['devices'] if d['row_id']==self.selected),None) if self.audit else None
    def select(self,*_):
        selection=self.tree.selection()
        if not selection:return
        self.selected=selection[0];d=self.current()
        self.state.set(d['result']);self.notes.delete('1.0','end');self.notes.insert('1.0',d['notes'])
        self.details.configure(state='normal');self.details.delete('1.0','end')
        info={k:v for k,v in d.items() if k!='photos'}
        info['fotografías']=[p['name'] for p in d['photos']]
        self.details.insert('1.0',json.dumps(info,ensure_ascii=False,indent=2));self.details.configure(state='disabled')
    def confirm(self):
        d=self.current()
        if not d:return
        try:record(d,self.state.get(),self.tech.get(),self.notes.get('1.0','end-1c'))
        except ValueError as exc:messagebox.showwarning('Revisión',str(exc));return
        self.dirty=True;self.refresh();self.status.set('Resultado registrado. Guarda la auditoría para conservarlo en disco.')
    def manual(self):
        if not self.audit or self.busy:return
        name=simpledialog.askstring('Alta manual','Nombre del dispositivo o prueba (por ejemplo USB lateral izquierdo):')
        if not name or not name.strip():return
        category=simpledialog.askstring('Categoría','Categoría:',initialvalue='Manual')
        if not category:return
        d=device(category,name,'manual:'+str(uuid.uuid4()),{'origin':'Alta manual del auditor'},'No detectado automáticamente')
        d['row_id']=str(uuid.uuid4());self.audit['devices'].append(d);self.dirty=True;self.refresh()
    def photos(self):
        d=self.current()
        if not d:return
        paths=filedialog.askopenfilenames(title='Fotografías',filetypes=[('Imágenes','*.jpg *.jpeg *.png *.webp *.bmp')])
        for p in paths:
            try:
                b=Path(p).read_bytes()
                d['photos'].append({'name':Path(p).name,'added_at':now(),'base64':base64.b64encode(b).decode('ascii')})
                self.dirty=True
            except OSError as exc:messagebox.showerror('Fotografía',str(exc))
        self.select()
    def save(self):
        if not self.audit or self.busy:return
        path=filedialog.asksaveasfilename(defaultextension='.json',initialfile='auditoria_'+self.audit['audit_id']+'.json',filetypes=[('Auditoría JSON','*.json')])
        if not path:return
        try:
            self.audit.update(technician=self.tech.get(),lot=self.lot.get(),saved_at=now());save(self.audit,path)
            self.dirty=False;self.status.set('Guardado: '+path)
        except Exception as exc:messagebox.showerror('No se pudo guardar',str(exc))
    def open(self):
        if not self.safe():return
        p=filedialog.askopenfilename(filetypes=[('Auditoría JSON','*.json')])
        if not p:return
        try:
            data=load(p);self.audit=data;self.selected=None
            self.tech.set(data.get('technician',''));self.lot.set(data.get('lot',''));self.dirty=False;self.refresh()
            self.status.set('Auditoría abierta: '+p)
        except Exception as exc:messagebox.showerror('No se pudo abrir',str(exc))
    def close(self):
        if self.safe():self.destroy()

if __name__=='__main__':App().mainloop()
