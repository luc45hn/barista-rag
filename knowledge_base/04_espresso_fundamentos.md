# Espresso — Fundamentos, Parámetros y Resolución de Problemas
**Fuente:** Compilado de estándares SCA, Barista Hustle, Scott Rao — The Coffee Roaster's Companion
**Tipo:** Conocimiento técnico de dominio público / buenas prácticas de la industria

---

## 1. Anatomía de un espresso

Un espresso es una bebida concentrada preparada forzando agua caliente a presión a través de café molido compactado (el "puck").

### Parámetros estándar del espresso (SCA / industria)
| Parámetro | Valor estándar | Rango aceptable |
|---|---|---|
| Dosis (café molido) | 18 g | 14–22 g |
| Rendimiento (bebida) | 36 g | 28–44 g |
| Ratio | 1:2 | 1:1.5 – 1:3 |
| Tiempo de extracción | 27–30 s | 22–35 s |
| Temperatura del agua | 93 °C | 90–96 °C |
| Presión | 9 bar | 8–10 bar |
| Temperatura de servicio | 67–70 °C en taza | — |

### El ratio de espresso
- El ratio más común en specialty es **1:2** (por cada gramo de café, 2 gramos de bebida)
- Ratio más alto (1:3, 1:4) → espresso más largo ("lungo"), más suave, más acidez
- Ratio más bajo (1:1.5, 1:1) → espresso más corto ("ristretto"), más dulce y concentrado

---

## 2. Variables de extracción

### Las 4 variables principales (recuerda: BREW)
1. **B — Brew ratio (ratio):** cuánto café vs cuánta bebida
2. **R — Roast level (tueste):** tostado claro extrae más lento, oscuro extrae más rápido
3. **E — Extraction yield (rendimiento de extracción):** % de sólidos disueltos del café
4. **W — Grind size (molienda):** la variable de ajuste más importante

### Triángulo de la extracción
El sabor del espresso es resultado de la interacción entre:
```
Dosis → determina cuánto café hay
Rendimiento → determina cuánta bebida extraes
Tiempo → consecuencia de molienda + dosis + rendimiento
```

**Si el tiempo es correcto pero el sabor está mal → ajustar dosis o rendimiento**
**Si el sabor está bien pero el tiempo es incorrecto → ajustar molienda**

---

## 3. Dialing in (calibrar el espresso)

"Dialing in" es el proceso de ajustar los parámetros para encontrar la extracción óptima de un café específico.

### Protocolo básico de dialing in
1. **Fijar el ratio:** empezar con 18 g dosis → 36 g bebida (1:2)
2. **Fijar la temperatura:** empezar con 93 °C
3. **Ajustar la molienda** hasta llegar al tiempo objetivo (27–30 s)
4. **Probar el sabor** y ajustar si es necesario:
   - Muy ácido/agrio/subdesarrollado → moler más fino (extrae más)
   - Muy amargo/astringente → moler más grueso (extrae menos)
5. Si el sabor sigue sin funcionar con molienda correcta → ajustar dosis o ratio

### Regla de oro del ajuste
**Una variable a la vez.** Si cambias molienda y temperatura al mismo tiempo, no sabrás qué causó el cambio.

---

## 4. Defectos del espresso y cómo corregirlos

### Subextracción
**Síntomas:** sabor agrio, ácido, delgado, salado, poco dulce, retrogusto corto
**Causas posibles:**
- Molienda muy gruesa
- Temperatura muy baja
- Tiempo de extracción muy corto (< 22 s)
- Dosis muy baja
- Distribución irregular del café en el portafiltro

**Soluciones:**
1. Moler más fino (primera acción)
2. Aumentar temperatura en 1 °C
3. Aumentar dosis levemente
4. Revisar la distribución y el tampeo

### Sobreextracción
**Síntomas:** amargo, astringente, seco, quemado, plano
**Causas posibles:**
- Molienda muy fina
- Temperatura muy alta
- Tiempo de extracción muy largo (> 35 s)
- Dosis muy alta

**Soluciones:**
1. Moler más grueso (primera acción)
2. Bajar temperatura en 1 °C
3. Revisar si hay channeling

### Channeling (canalización)
**¿Qué es?** El agua encuentra un camino de menor resistencia a través del puck y fluye principalmente por ahí, dejando otras zonas sin extraer correctamente.
**Síntomas:** flujo de espresso con "chorros" o irregularidades, sabor ácido Y amargo al mismo tiempo
**Causas:**
- Distribución irregular del café en el portafiltro
- Tampeo inclinado o con presión irregular
- Molienda irregular (burrs desgastados)
- Puck húmedo por purga insuficiente

**Soluciones:**
1. Distribuir el café uniformemente antes de tampear (usar WDT tool o agitar el portafiltro)
2. Tampear recto y con presión pareja (~15–20 kg)
3. Limpiar los burrs regularmente
4. Purgar siempre antes de preparar

---

## 5. La leche y sus texturas

### Temperatura de la leche para distintas bebidas
| Bebida | Temperatura ideal |
|---|---|
| Cappuccino | 60–65 °C |
| Latte / Flat white | 60–65 °C |
| Macchiato de leche | 60–65 °C |
| Leche para frío (shakerato) | 4–8 °C |

> **Nunca superar 70 °C:** las proteínas de la leche se desnaturalizan, la leche queda "cocinada" con sabor dulzón/quemado y pierde la microespuma.

### Tipos de textura de leche
- **Microespuma / Silky milk:** leche con burbujas tan pequeñas que no se distinguen, textura aterciopelada — para latte art y flat white
- **Espuma densa:** cappuccino clásico italiano, textura más firme
- **Espuma seca:** para cappuccino "al estilo italiano antiguo", más volumen

### Técnica de vaporizado
1. Purgar el vaporizador antes de usarlo (sacar el agua condensada)
2. Sumergir la lanza apenas debajo de la superficie de la leche
3. **Posición:** lanza levemente inclinada, off-center para crear un remolino
4. **Fase de incorporación de aire (stretching):** bajar la jarra para que la punta quede en la superficie → incorpora aire → máximo en los primeros 3–4 s
5. **Fase de calentamiento (rolling):** subir la jarra para que la lanza quede más profunda → calienta y homogeneiza la espuma → hasta llegar a temperatura
6. Golpear la jarra suavemente sobre la mesa y girar para integrar la espuma
7. Verter inmediatamente

### Errores comunes al vaporizar
- **Demasiadas burbujas grandes:** la lanza estaba muy afuera durante el stretching → resultado: espuma seca, imposible hacer latte art
- **Leche quemada:** se superó la temperatura → tirar y empezar de nuevo
- **Leche sin cuerpo:** no se incorporó suficiente aire → bajar más la jarra al inicio
- **Remolino insuficiente:** la lanza no está en la posición correcta → ajustar ángulo e inclinación

---

## 6. Bebidas a base de espresso — fichas

### Espresso
- 1 shot: 18–20 g café → 32–40 g bebida
- Servir en taza de 60–90 ml precalentada

### Doppio (doble espresso)
- 2 shots: 18–20 g café → 32–40 g bebida (en portafiltro doble)
- No es simplemente "2 espressos juntos"

### Ristretto
- Ratio corto: 1 g café → 1–1.5 g bebida
- Extracción en ~20 s
- Resultado: más dulce, más concentrado, menos amargo

### Lungo
- Ratio largo: 1 g café → 3–4 g bebida
- Extracción en ~40–50 s
- Resultado: más volumen, más acidez, sabores más complejos

### Macchiato espresso
- Espresso + 1–2 cucharadas de espuma densa de leche

### Cappuccino
- 1 shot espresso + leche vaporizada a ~60–65 °C en proporción 1:1:1 (espresso:leche:espuma)
- Volumen total: 150–180 ml
- Cappuccino italiano tradicional: < 150 ml

### Latte / Café con leche (specialty)
- 1–2 shots espresso + leche vaporizada en proporción 1:4 o 1:6
- Volumen total: 220–360 ml
- Microespuma integrada, no espuma separada

### Flat White
- 2 shots (doppio) + leche en proporción 1:2.5 a 1:3
- Volumen total: 150–180 ml
- Microespuma muy fina e integrada — diferencia principal con cappuccino

### Cortado
- 1 shot espresso + leche vaporizada en proporción 1:1 o 1:2
- Volumen total: 50–80 ml
- Reduce la acidez del espresso sin diluir demasiado

---

## 7. Mantenimiento del equipo (básico)

### Diario
- **Retrolavado (backflush):** limpiar el grupo con agua sola después de cada servicio (en máquinas con válvula de 3 vías)
- **Limpiar el portafiltro:** cepillar y enjuagar después de cada extracción
- **Purgar el vaporizador:** antes y después de usar
- **Limpiar la pantalla del grupo:** cepillar al final del día

### Semanal
- **Retrolavado con detergente:** usar pastillas o polvo específico para espresso (Cafiza, Puly Caff)
- **Limpiar los portafiltros en remojo:** sumergir en solución de detergente 20–30 min
- **Limpiar el vaporizador con aguja:** destapar el orificio si está obstruido

### Mensual
- **Cambiar o limpiar filtros de agua:** según indicación del fabricante
- **Calibrar la temperatura de la máquina**
- **Revisar las juntas del grupo**

### Señales de que algo está mal
- **Extracciones inconsistentes sin cambiar nada** → revisar presión o temperatura
- **Espresso sale muy rápido** → burrs desgastados o molienda incorrecta
- **Sabor a jabón** → retrolavado insuficiente o mal enjuagado
- **Máquina tarda en calentar** → calcificación, necesita descalcificación
