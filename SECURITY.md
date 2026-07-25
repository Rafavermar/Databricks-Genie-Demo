# Seguridad

## Alcance

Este repositorio es una demostración con datos exclusivamente sintéticos. No
debe utilizarse para almacenar información de clientes, credenciales ni datos
operativos reales.

## Información que no debe publicarse

- tokens, secretos OAuth, cookies o cabeceras de autorización;
- archivos `.databrickscfg`, `.env` o variables exportadas;
- hosts privados, correos o identificadores internos innecesarios;
- capturas con información personal o recursos ajenos al demo;
- evidencias remotas sin pasar por los mecanismos de saneamiento del proyecto.

La automatización Enterprise usa un GitHub Environment denominado
`databricks-demo`. Guarde `DATABRICKS_CLIENT_SECRET` como **secret** del
environment y el resto de parámetros no sensibles como **variables**.

## Reportar un problema

No publique una vulnerabilidad ni un secreto en una issue. Utilice la opción
privada **Report a vulnerability** de GitHub si está habilitada o contacte al
propietario del repositorio por un canal privado.

Si un secreto aparece accidentalmente en un commit:

1. revoque o rote el secreto inmediatamente;
2. revise los logs y accesos asociados;
3. elimine el dato del historial antes de volver a publicar;
4. documente el incidente sin incluir el valor comprometido.

## Responsabilidad de despliegue

Antes de usar el target `enterprise`, el equipo receptor debe revisar permisos,
identidad desplegadora, catálogo, schema, SQL warehouse, políticas corporativas
y proceso de retirada. El target no aprovisiona infraestructura de cuenta.
