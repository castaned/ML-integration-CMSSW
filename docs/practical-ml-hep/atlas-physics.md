# La física detrás del Higgs Challenge

**La red no mide una sección eficaz por sí sola.** Ayuda a seleccionar eventos para que una medición o una búsqueda sea más sensible. Aquí conectamos las partículas, las 30 entradas de la red y la interpretación física de sus resultados.

[Volver al laboratorio YAML](atlas-gpu.md) · [Completar la bitácora](atlas-experiments.md)

## De la colisión a lo que ve el detector

La señal del reto es **H → τ⁺τ⁻**. Un tau decae a electrón o muón y neutrinos; el otro produce hadrones y un neutrino. Por eso buscamos **un leptón, un tau hadrónico y momento transversal faltante**, a veces acompañados de jets. El detector registra productos del decaimiento, no una etiqueta que diga «Higgs».

![Producción de Higgs por fusión de gluones y bosones vectoriales](../assets/workshop/higgs_ggf_vbf.png){ width="800" }

*Producción: (a) fusión de gluones; (b) fusión de bosones vectoriales, con quarks salientes que pueden producir jets. Recorte de la figura 1 de la [publicación conjunta ATLAS y CMS, arXiv:1606.02266](https://arxiv.org/abs/1606.02266). Estos diagramas contextualizan la producción; no proceden del artículo del challenge.*

### El estado final que buscamos

![Cadena completa del Higgs a dos taus y sus productos de decaimiento](../assets/workshop/higgs_tautau_final_state.svg)

*Esquema elaborado para el taller. Un tau decae a electrón o muón y dos neutrinos; el otro a hadrones y un neutrino. Se muestra un ejemplo de corriente hadrónica con u y anti-d, que forman hadrones; no observamos quarks libres. Los W son virtuales. También se incluye el proceso con cargas opuestas.*

**Lo visible:** un electrón o muón y un tau hadrónico reconstruido. **Lo invisible:** tres neutrinos, que contribuyen al momento transversal faltante. Por eso usamos variables del leptón, del tau y del MET. El estado completo no se reconstruye con la masa visible solamente.

[Descargar diagrama PNG](../assets/workshop/higgs_tautau_final_state.png) · [SVG para ampliar o presentar](../assets/workshop/higgs_tautau_final_state.svg)

Los fondos imitan esos objetos: **Z → ττ** produce taus reales; los pares de top pueden generar leptones, taus y jets; **W + jets** puede entrar cuando un objeto se identifica incorrectamente. Una misma apariencia final puede tener distintos orígenes.

![La masa visible muestra una señal pequeña sobre fondos abundantes](../assets/workshop/challenge_visible_mass.png){ width="460" }

*Figura 1 extraída del [artículo del Higgs Challenge](https://proceedings.mlr.press/v42/cowa14.pdf), que reproduce el resultado ATLAS-CONF-2013-108. La línea roja de señal está multiplicada por **50**, como indica la leyenda. Esta figura publicada contiene datos y estimaciones de fondo; nuestros entrenamientos usan simulaciones del dataset. No confundir sus cantidades con las de nuestros histogramas normalizados.*

**Pregunta para el salón:** si señal y fondo pueden producir objetos similares, ¿qué combinaciones de masas, direcciones y momentos podrían ayudarnos?

## ¿Ya se observó H → ττ en el LHC?

**Sí. El objetivo actual incluye medir sus propiedades con más precisión.** El challenge de 2014 permite practicar cómo separar una señal difícil; no significa que el canal siga sin observarse.

| Hito | Resultado |
| --- | --- |
| CMS, anunciado en 2017 | Observación de H → ττ por un experimento, 5.9 desviaciones estándar al combinar datos de 7, 8 y 13 TeV |
| ATLAS, 2018 | Observación con 6.4 desviaciones estándar al combinar esas energías |
| ATLAS, publicación de 2022 | Medición de la tasa de producción en este canal con los datos completos de Run 2 |
| ATLAS, publicación de 2025 | Mediciones diferenciales: cómo cambia la producción según las propiedades cinemáticas |

Fuentes: [CMS HIG-16-043](https://cms-results.web.cern.ch/cms-results/public-results/publications/HIG-16-043/index.html), [observación ATLAS](https://atlas.cern/updates/briefing/higgs-couples-heaviest-lepton) y [mediciones diferenciales ATLAS](https://arxiv.org/abs/2407.16320).

Como ejemplo numérico, ATLAS midió en colisiones a **13 TeV**, usando **139 fb⁻¹**, el producto de sección eficaz de producción por probabilidad de decaimiento a ττ, para **|yH| < 2.5**:

**σ × B(H → ττ) = 2.94 ± 0.21 (estadística) +0.37/−0.32 (sistemática) pb.**

La predicción del Modelo Estándar para esa definición es **3.17 ± 0.09 pb**; son compatibles dentro de las incertidumbres. Es una medición publicada, no un número obtenido en nuestro taller ni necesariamente la medición más reciente. [ATLAS, JHEP 08 (2022) 175](https://arxiv.org/abs/2201.08269).

**Para interpretar el ejercicio:** una mejor selección puede ayudar a observar una señal, pero también a medirla mejor una vez observada. Nuestra AMS es un indicador de selección en simulación; no es la significancia observada del experimento ni una sección eficaz.

## Las 30 variables, organizadas por su significado

La tabla corta de la guía solo mostraba ejemplos. **El YAML `features: all_physics` utiliza las 30 variables siguientes.** `PRI_` identifica 17 cantidades primarias y `DER_` las 13 construidas combinando otras cantidades.

### Un pequeño vocabulario

- **pT:** momento perpendicular al haz, en GeV.
- **η:** pseudorrapidez; expresa la dirección respecto al haz. Cerca de cero corresponde a la región transversal.
- **φ:** ángulo alrededor del haz, en radianes.
- **Jet:** conjunto de partículas asociado a un quark o gluón.
- **MET:** desequilibrio transversal observado; puede revelar neutrinos, aunque también depende de la resolución del detector.
- **Masa visible:** usa lo detectado; no recupera automáticamente la energía de los neutrinos.

### Objetos reconstruidos: 17 variables primarias

Definiciones resumidas del [registro oficial de datos](https://opendata.cern.ch/record/328). Los jets se ordenan por pT: «leading» es el primero, «subleading» el segundo.

| Variable | Qué representa |
| --- | --- |
| `PRI_tau_pt` | pT del tau hadrónico reconstruido |
| `PRI_tau_eta` | Su pseudorrapidez |
| `PRI_tau_phi` | Su ángulo azimutal |
| `PRI_lep_pt` | pT del electrón o muón |
| `PRI_lep_eta` | Pseudorrapidez del leptón |
| `PRI_lep_phi` | Ángulo azimutal del leptón |
| `PRI_met` | Magnitud del MET |
| `PRI_met_phi` | Dirección azimutal del MET |
| `PRI_met_sumet` | Energía transversal total registrada |
| `PRI_jet_num` | Número de jets; 3 representa tres o más |
| `PRI_jet_leading_pt` | pT del primer jet |
| `PRI_jet_leading_eta` | Pseudorrapidez del primer jet |
| `PRI_jet_leading_phi` | Ángulo azimutal del primer jet |
| `PRI_jet_subleading_pt` | pT del segundo jet |
| `PRI_jet_subleading_eta` | Pseudorrapidez del segundo jet |
| `PRI_jet_subleading_phi` | Ángulo azimutal del segundo jet |
| `PRI_jet_all_pt` | Suma escalar de pT de todos los jets |

Estas cantidades describen los objetos del evento. No esperamos que cada una discrimine por sí sola: también importan sus relaciones y las condiciones de detección.

### Combinaciones físicas: 13 variables derivadas

Resumen de la [documentación del challenge](https://opendata.cern.ch/record/329), con las definiciones detalladas en su apéndice.

| Variable | Qué combina |
| --- | --- |
| `DER_mass_MMC` | Masa ττ estimada considerando los neutrinos |
| `DER_mass_transverse_met_lep` | Masa transversal leptón–MET |
| `DER_mass_vis` | Masa del tau visible y el leptón |
| `DER_pt_h` | Suma vectorial transversal tau, leptón y MET |
| `DER_deltaeta_jet_jet` | Separación en η entre los dos jets |
| `DER_mass_jet_jet` | Masa del par de jets |
| `DER_prodeta_jet_jet` | Producto de las η de ambos jets |
| `DER_deltar_tau_lep` | Separación angular tau–leptón en η y φ |
| `DER_pt_tot` | Balance transversal: tau, leptón, MET y hasta dos jets |
| `DER_sum_pt` | Suma escalar de pT del tau, leptón y jets |
| `DER_pt_ratio_lep_tau` | Cociente pT del leptón / pT del tau |
| `DER_met_phi_centrality` | Posición angular del MET respecto a tau y leptón |
| `DER_lep_eta_centrality` | Posición del leptón en η respecto a los jets |

**Tres ideas físicas:** las masas ayudan a distinguir hipótesis de origen; el MET informa sobre componentes invisibles; los jets y sus separaciones aportan información sobre la producción. La red puede combinar estas pistas sin que nosotros fijemos todos los cortes.

Si no hay dos jets, algunas variables no están definidas. El valor `-999` lo señala: no es una masa o un momento físico. La preparación automática lo trata antes del entrenamiento. Las columnas de etiqueta, pesos, identificador y partición no cuentan entre las 30 entradas.

## Leer una ROC como físico

La red asigna una puntuación. Al exigir una puntuación mayor que cierto umbral, conservamos una fracción de señal **εs** y una fracción de fondo **εb**.

| Elemento de la ROC del taller | Significado |
| --- | --- |
| Eje horizontal | Fondo que dejamos pasar, εb |
| Eje vertical | Señal que conservamos, εs |
| Un punto | Una elección de umbral |
| Más arriba al mismo εb | Más señal para el mismo fondo aceptado |
| Más a la izquierda al mismo εs | Menos fondo para la misma señal conservada |

**AUC resume toda la curva.** Un análisis puede depender solo de una zona de bajo fondo; por eso una AUC ligeramente mayor no garantiza mejor AMS o mejor límite.

Nuestro gráfico ROC es **sin pesos**. Para traducirlo a rendimientos físicos, se deben sumar los pesos de los eventos seleccionados. Los porcentajes de eventos simulados no siempre son las eficiencias ponderadas que corresponden a tasas esperadas.

### Ejemplo para completar en clase

Este es un ejemplo hipotético de rendimientos esperados, no un resultado del dataset. Antes de la selección de la red tenemos **100 eventos de señal y 10 000 de fondo**. Ambas selecciones conservan 60% de la señal:

| Selección | εs | εb | Señal seleccionada s | Fondo seleccionado b | s / √b, aproximación |
| --- | ---: | ---: | ---: | ---: | ---: |
| A | 0.60 | 0.10 | 60 | 1 000 | 1.90 |
| B | 0.60 | 0.05 | 60 | 500 | 2.68 |

La segunda selección permite ver mejor el mismo exceso de señal sobre el fondo. **No cambia la frecuencia física con la que se produce el Higgs**; cambia cuánto ruido dejamos entrar en la selección. La aproximación s/√b sirve aquí para ilustrar el efecto con fondo dominante y conocido; no reemplaza la AMS del challenge ni un cálculo con incertidumbres sistemáticas.

## Conexión con una sección eficaz

La sección eficaz σ describe la frecuencia de producción de un proceso para una luminosidad dada. En un conteo simplificado, el número esperado de eventos seleccionados se expresa como:

<p><strong>s = L × σ × B × A × εs</strong></p>

L es la luminosidad integrada; B, la probabilidad de la cadena de decaimiento considerada; A, la aceptación y preselección previa; εs, la eficiencia adicional de nuestra red.

Si observamos N eventos y estimamos un fondo b, una estimación elemental sería:

<p><strong>σ estimada = (N − b) / (L × B × A × εs)</strong></p>

Una red útil puede reducir el fondo conservando señal y ayudar a disminuir la incertidumbre de la medición. Pero hay que conocer y calibrar εs y estimar el fondo. Una selección demasiado estricta pierde señal; una red mal modelada puede sesgar el resultado. **Mejor ROC no significa una sección eficaz medida más grande.**

## Conexión con límites y descubrimiento

Si no aparece un exceso claro, un análisis puede establecer un **límite superior**: qué intensidades de señal quedan incompatibles con los datos bajo un procedimiento estadístico definido. Una mejor separación puede mejorar el límite **esperado**, pero no garantiza un cambio concreto del límite observado.

También puede mejorar la sensibilidad esperada a un exceso. El cálculo completo utiliza un modelo estadístico, normalizaciones e incertidumbres de fondo, detector y señal; puede emplear toda la distribución de puntuaciones, no solo un corte. Una ROC no contiene por sí sola toda esa información. Véase la [referencia de Cowan, Cranmer, Gross y Vitells](https://arxiv.org/abs/1007.1727).

En este taller medimos **clasificación y AMS de validación en simulación**. No estamos publicando una sección eficaz, un límite ni una significancia observada de descubrimiento. La AMS conecta la selección con una sensibilidad aproximada, y motiva por qué no basta con acertar muchas etiquetas. El [artículo del challenge, secciones 2 y 4](https://proceedings.mlr.press/v42/cowa14.pdf), desarrolla esa conexión.

!!! question "Para cerrar la discusión"
    ¿Qué preferimos: más AUC global, más señal al mismo fondo, o menos fondo al mismo número de señales? La respuesta depende del objetivo físico y sus incertidumbres. Expliquen qué medirían antes de elegir un modelo.

## Procedencia de las imágenes

- `higgs_ggf_vbf.png`: figura 1 de ATLAS y CMS, [arXiv:1606.02266](https://arxiv.org/abs/1606.02266), recortada para mostrar los diagramas.
- `higgs_tautau_final_state.svg/png`: esquema original del taller de la cadena leptónica–hadrónica de H → ττ; no es una figura extraída del artículo.
- `challenge_visible_mass.png`: figura 1 de Adam-Bourdarios et al., [PMLR 42 (2015)](https://proceedings.mlr.press/v42/cowa14.html), con el crédito original a ATLAS-CONF-2013-108 preservado.

Los diagramas de producción se obtuvieron de la publicación conjunta, porque el artículo y la documentación del challenge no contienen ese tipo de diagramas. La cadena completa H → ττ se elaboró como esquema didáctico para este curso. Ninguna de estas figuras es un resultado de nuestros entrenamientos.
