# PULSIA Auditor 0.1 — inventario y revisión manual

Primera base del auditor local. Código Python sin dependencias de pip.
Windows 10/11: Python 3.12 o superior con Tcl/Tk y Windows PowerShell.
Linux: Python 3.12 o superior con tkinter (en Debian/Ubuntu, paquete python3-tk).

## Inicio

Extrae todo el ZIP en una carpeta escribible, también puede estar en un USB.
Windows: doble clic en Iniciar.cmd. Linux: `sh iniciar.sh`.
No requiere instalar módulos Python. No incluye Python ni un ejecutable compilado.

## Flujo

1. Introduce técnico y lote y pulsa Nueva detección. Se crea una auditoría nueva;
   volver a detectar no mezcla resultados con auditorías anteriores.
2. Consulta Datos del equipo para identidad, BIOS, SN disponible y avisos.
3. Filtra el inventario. Selecciona una fila y consulta detalles e identificadores.
4. Comprueba físicamente el componente y elige resultado. Introduce observaciones
   y pulsa Registrar resultado. FAIL, Dudoso y No aplicable requieren motivo.
5. Añade manualmente componentes o pruebas que no aparezcan. Por ejemplo, cada
   puerto USB físico, micrófono, lector de tarjetas, teclado o touchpad.
6. Adjunta fotografías si procede. No hay límite prefijado de cantidad; las fotos
   se incorporan al JSON en base64 y consumen memoria/tamaño de archivo.
7. Guarda el JSON. Abrir auditoría permite continuar con fotos e historial.

Las observaciones solo se incorporan al pulsar Registrar resultado. Guarda con
frecuencia: los cambios están en memoria hasta pulsar Guardar y elegir destino.
Cerrar o abrir otra auditoría avisa sobre resultados registrados sin guardar.
El historial permite consultar cambios, pero es un JSON editable, no una firma
ni un comprobante inalterable. No se debe certificar una unidad usando únicamente
el estado OK de Windows.

## Qué detecta

Windows: inventario PnP de dispositivos presentes (incluidos lógicos/controladores),
CPU, módulos RAM, discos, batería, identidad y BIOS mediante CIM. Cada proveedor
puede generar avisos sin impedir que se consulten los demás. Datos de discos y PnP
pueden representar el mismo componente desde perspectivas distintas: todavía no
hay consolidación por dispositivo físico. La categoría PnP se mantiene original.

Linux: inventario básico sysfs de PCI, USB, red, audio, vídeo, entrada, discos,
alimentación y conectores de pantalla; CPU y memoria desde procfs. No tiene aún
el mismo detalle de Windows. Algunas categorías representan interfaces o nodos,
no componentes físicos distintos. No asigna ausencia por falta de detección.

## Comprobaciones manuales sugeridas

- USB/lector: conectar una unidad conocida, leer un archivo y verificar cada puerto.
- Audio/micrófono: reproducir sonido y grabar/reproducir voz.
- Cámara: abrir la app de cámara y comprobar imagen.
- Pantalla: fondos sólidos, brillo y revisión de píxeles y parpadeos.
- Teclado/touchpad: comprobar teclas, botones y gestos.
- Red/Bluetooth: comprobar conexión y transferencia o emparejamiento.
- Batería: comprobar carga y funcionamiento desconectado del cargador.
- CPU/RAM/disco: pendiente de integrar herramientas de diagnóstico específicas;
  presencia e información técnica no sustituyen pruebas de estabilidad o SMART.

La aplicación registra las conclusiones; todavía no ejecuta esas pruebas.
No incluye borrado de discos, estrés, SMART, prueba de superficie, lectura de claves,
servidor, PXE ni envío de datos. Ningún resultado pasa automáticamente a PASS.
Un dispositivo sin controlador, oculto al SO, averiado o no enumerado puede no verse.
Un puerto vacío no equivale a un puerto funcional. El inventario incluye adaptadores
virtuales y dispositivos del sistema si los enumera el SO.

## Validación de esta entrega

Tres pruebas automatizadas: estados/historial y guardado-reapertura, proveedor
Windows simulado con aviso parcial, y detección real en el entorno Linux de desarrollo.
Compilación sintáctica de los módulos. Interfaz y PowerShell pendientes de probar
sobre Windows real: esta versión es un prototipo, no una auditoría industrial validada.
Para pruebas: `python -m unittest -v` desde esta carpeta.

Referencia técnica de detección Windows:
https://learn.microsoft.com/en-us/powershell/module/pnpdevice/get-pnpdevice
