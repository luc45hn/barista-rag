# Guía de Equipamiento — Máquinas de Espresso en Cafeterías de Especialidad

## Tipos de caldera y su impacto en la calibración

Antes de hablar de cada máquina, es fundamental entender los tipos de sistema de caldera, porque determinan qué variables puede controlar el barista.

### Single Boiler (Caldera única)
Una sola caldera para extracción y vaporizado. El barista **no puede usar temperatura diferente para distintos cafés** en la misma sesión. La temperatura se ajusta globalmente y afecta tanto al espresso como al vapor.

Variables ajustables: molienda, dosis, ratio, presión de tampe.
Variables NO ajustables: temperatura (fija por el sistema).

### Heat Exchanger (Intercambiador de calor / HX)
Una caldera grande para vapor, con un serpentín interno para el agua de extracción. La temperatura del agua de extracción **no es perfectamente estable** y depende del tiempo de reposo entre shots. Requiere "flushing" (purgar el grupo) antes de cada extracción para estabilizar la temperatura.

Variables ajustables: molienda, dosis, ratio, tiempo de flushing (afecta temperatura indirectamente).
Variables NO ajustables: temperatura de extracción de forma precisa sin PID.

### Dual Boiler (Doble caldera)
Una caldera para extracción y otra para vapor, independientes. Permite **ajuste preciso y estable de temperatura** de extracción sin afectar el vapor. Es el sistema preferido en cafés de especialidad.

Variables ajustables: temperatura de extracción (PID), molienda, dosis, ratio, presión.

### Multi Boiler
Cada grupo tiene su propio boiler independiente. Permite usar temperaturas diferentes por grupo, ideal cuando se sirven distintos perfiles de café simultáneamente.

---

## Máquinas más comunes en cafeterías de especialidad

### Nuova Simonelli Appia II / Appia Life
**Tipo de sistema:** Heat Exchanger (HX)
**Temperatura:** No tiene PID. La temperatura de extracción está determinada por la caldera de vapor (generalmente fija entre 120-125°C) y el serpentín HX. El agua que llega al grupo ronda los 93-96°C según el tiempo de reposo.

**Lo que el barista PUEDE ajustar:**
- Molienda (variable de ajuste principal)
- Dosis (gramos de café en el portafiltro)
- Ratio (gramos de bebida / gramos de café)
- Tiempo de extracción (consecuencia de molienda y dosis)
- Volumetría (si tiene control volumétrico, puede programar el volumen de salida)
- Presión de tampe (influye en la resistencia al flujo)

**Lo que el barista NO PUEDE ajustar:**
- Temperatura de extracción de forma precisa
- Presión de la bomba (fija en 9 bar salvo intervención técnica)

**Estrategia de calibración sin temperatura ajustable:**
1. Flushing consistente antes de cada extracción para estabilizar la temperatura
2. Usar molienda como herramienta principal de ajuste
3. Para cafés más delicados (orígenes claros, procesos naturales), moler más grueso para compensar la temperatura no ajustable
4. Para tuestes más oscuros, moler más fino
5. El ratio puede usarse para ajustar la intensidad: ratio más largo (1:2.5 o 1:3) para suavizar, más corto (1:1.5 o 1:2) para intensificar

**Tip específico para la Appia II:**
Hacer siempre un "cooling flush" (purgar 3-4 segundos de agua) antes de la primera extracción y después de vaporizar leche. La temperatura del HX sube cuando se usa el vapor y baja cuando la máquina está inactiva.

---

### La Marzocco Linea Classic / Linea PB / Linea Mini
**Tipo de sistema:** Dual Boiler con PID
**Temperatura:** Ajustable con precisión de ±0.1°C. El barista tiene control total sobre la temperatura de extracción.

**Lo que el barista PUEDE ajustar:**
- Temperatura de extracción (típicamente entre 88°C y 96°C)
- Molienda
- Dosis
- Ratio
- Pre-infusión (en modelos con esta función)
- Presión (en modelos Strada o con paddle)

**Rango de temperatura por tipo de café:**
- Tuestes claros / orígenes de altura / procesos lavados: 93-96°C
- Tuestes medios / perfiles equilibrados: 91-93°C  
- Tuestes oscuros / blends de bar: 88-91°C
- Cafés de proceso natural o honey con mucha dulzura: 90-92°C

**Estrategia de calibración:**
La temperatura es la primera variable a definir según el perfil del café, antes de ajustar molienda.

---

### Victoria Arduino Black Eagle / White Eagle / Eagle One
**Tipo de sistema:** Multi Boiler (T3 en Black Eagle y Eagle One)
**Temperatura:** Control independiente por grupo con PID. El Black Eagle Gravitech incluye control gravimétrico automático del ratio.

**Lo que el barista PUEDE ajustar:**
- Temperatura independiente por grupo
- Molienda, dosis, ratio
- Perfil de presión (en modelos con pressure profiling)
- Pre-infusión

**Diferenciador clave:**
El sistema T3 mantiene temperatura extremadamente estable incluso en alto volumen. Ideal para cafés con mucho movimiento donde la consistencia entre shots es crítica.

---

### Rancilio Classe 5 / Classe 9
**Tipo de sistema:** Heat Exchanger (HX) — Classe 5 / Dual Boiler — Classe 9
**Temperatura:** Sin PID en Classe 5. Con PID en Classe 9.

**Classe 5 (HX):** misma lógica que la Appia II — temperatura no ajustable con precisión, flushing importante.
**Classe 9:** temperatura ajustable, estrategia similar a La Marzocco.

---

### Rocket R9 / Rocket Boxer
**Tipo de sistema:** Dual Boiler con PID
**Temperatura:** Ajustable con precisión. Similar en funcionalidad a La Marzocco.

---

## Principios universales de calibración según el equipo

### Si la máquina NO tiene temperatura ajustable (HX o single boiler):

**El orden de ajuste recomendado es:**
1. Definir la dosis (punto de partida: 18g para portafiltro doble estándar)
2. Ajustar la molienda hasta llegar al tiempo objetivo (27-30 segundos para ratio 1:2)
3. Ajustar el ratio para modificar la intensidad
4. La presión de tampe debe ser consistente (14-20 kg), no variable

**Para cafés con problemas específicos:**
- Espresso muy amargo → moler más grueso + verificar flushing
- Espresso muy ácido → moler más fino + asegurarse de hacer flushing previo
- Espresso muy intenso con leche → aumentar el ratio (más agua, misma dosis)
- Espresso muy débil con leche → reducir el ratio o aumentar la dosis

### Si la máquina SÍ tiene temperatura ajustable (Dual Boiler con PID):

**El orden de ajuste recomendado es:**
1. Definir temperatura según el perfil del café (origen, tueste, proceso)
2. Definir la dosis
3. Ajustar la molienda hasta llegar al tiempo objetivo
4. Ajustar el ratio para la intensidad deseada

---

## Adaptación de parámetros según la bebida final

### Espresso solo
- Ratio objetivo: 1:2 a 1:2.5
- Tiempo: 25-30 segundos
- Se siente el perfil completo del café — todos los defectos son evidentes

### Con leche (latte, cortado, cappuccino)
- La leche suaviza la acidez y amplifica la dulzura y el cuerpo
- Un espresso "muy intenso" con leche suele indicar ratio demasiado corto (muy concentrado)
- Solución: aumentar el ratio a 1:2.5 o 1:3 manteniendo la dosis
- Un espresso "sin sabor" con leche suele indicar espresso muy débil o mala extracción
- La temperatura de vaporizado de la leche afecta el perfil final: 60-65°C preserva más dulzura

### Espresso sobre hielo / bebidas frías
- El frío suprime la acidez y ampifica el amargor
- Aumentar ligeramente el ratio (1:2.5 a 1:3) para compensar
- Temperatura de extracción 1-2°C más baja si es ajustable

---

## Molinos más comunes y su impacto

El molino es tan importante como la máquina. Un buen espresso requiere un molino que pueda ajustarse con precisión.

**Molinos comunes en cafeterías de especialidad:**
- **Mahlkönig EK43 / EK43 S**: molino de referencia para filter y single dose espresso. Alta uniformidad de molienda.
- **Mahlkönig E65S GBW**: molino doble con control gravimétrico. Muy preciso para alto volumen.
- **Eureka Mignon / Atom**: populares en cafés medianos, buena relación precio/precisión.
- **Mythos One / Mythos Two (Victoria Arduino)**: estándar en cafés de alto volumen con fresas cónicas grandes.

**Ajuste de molienda — referencia general:**
- Los números de ajuste varían por molino — no hay un "número universal"
- En un Mahlkönig EK43: el rango de espresso suele estar entre 3 y 6
- En un Eureka Mignon: el rango de espresso suele estar entre 1 y 4
- Siempre calibrar purificando el molino con 5-10g de café antes de medir el resultado de un ajuste nuevo
