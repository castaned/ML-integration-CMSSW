# Bitácora de experimentos

Completar **antes** de cada ejecución qué se cambiará y qué se espera. La mejora de una métrica no basta sin explicación y una comparación consistente.

| Ensayo | Datos/semilla | Cambio único | Métrica de validación | Umbral | Observación | Carpeta |
| --- | --- | --- | --- | --- | --- | --- |
| Higgs referencia | | Regresión logística | AUC | | | |
| Higgs variación | | | AUC | | | |
| CMS referencia | | AE latente 2 | Pérdida SM | | | |
| CMS variación | | | Pérdida SM | | | |

## Entrega de cada equipo

1. Pregunta física y procedencia de la simulación.
2. Configuraciones guardadas y tabla de experimentos.
3. Figura de ROC Higgs, figura de pérdida CMS y referencia a las carpetas de resultados.
4. Una conclusión por práctica: cambio, observación, limitación.

No enviar datos compartidos ni modelos pesados al repositorio. Un informe Markdown con figuras propias es suficiente. No incluir nombres de usuario o rutas personales si el informe será público.

## Preguntas para el cierre

- ¿Qué distingue aprender etiquetas de aprender reconstrucción?
- ¿Qué información se filtraría si usamos el identificador o el peso como entrada?
- ¿Por qué el escalado se ajusta solo con entrenamiento?
- ¿Qué cambia entre AUC, eficiencia a un umbral y significancia física?
- ¿Qué necesitarías para pasar de un ejercicio exploratorio a un resultado científico?
