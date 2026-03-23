# SIBO Analyzer — Web

App web para análisis de hidrógeno espirado (SIBO y pruebas de intolerancia).  
Construida con **Streamlit** + **Supabase Auth**.

---

## Requisitos previos

- Python 3.11+
- Cuenta gratuita en [supabase.com](https://supabase.com)

---

## Configuración inicial (una sola vez)

### 1. Clonar e instalar dependencias

```bash
git clone <tu-repo>
cd sibo-web
pip install -r requirements.txt
```

### 2. Crear proyecto en Supabase

1. Entrá a [app.supabase.com](https://app.supabase.com) y creá un nuevo proyecto.
2. Andá a **Project Settings → API**.
3. Copiá la **Project URL** y la **anon public key**.

### 3. Crear usuarios

En Supabase, andá a **Authentication → Users → Invite user** e ingresá el email de cada médico.  
Ellos recibirán un email para establecer su contraseña.  
No se necesita código adicional: Supabase maneja todo el flujo.

### 4. Configurar variables de entorno

```bash
cp .env.example .env
```

Editá `.env` con tus credenciales:

```
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_ANON_KEY=eyJ...
```

---

## Correr localmente

```bash
streamlit run app.py
```

Abrí [http://localhost:8501](http://localhost:8501) en el navegador.

---

## Despliegue en producción (Render)

1. Subí el código a un repositorio en GitHub.
2. En [render.com](https://render.com), creá un nuevo **Web Service**.
3. Seleccioná tu repo. Configurá:
   - **Build command:** `pip install -r requirements.txt`
   - **Start command:** `streamlit run app.py --server.port $PORT --server.address 0.0.0.0`
4. En **Environment Variables**, agregá `SUPABASE_URL` y `SUPABASE_ANON_KEY`.
5. Deploy. En 2 minutos tenés una URL pública tipo `https://sibo-cimeq.onrender.com`.

### Alternativa: Railway

```bash
railway login
railway init
railway up
```
Igual de simple, con variables de entorno desde el dashboard de Railway.

---

## Agregar un logo

Copiá tu archivo `cimeq_logo.png` a la raíz del proyecto.  
El PDF lo incluirá automáticamente.

---

## Estructura del proyecto

```
sibo-web/
├── app.py                  # Entrada principal, login y navegación
├── auth.py                 # Integración con Supabase Auth
├── logic/
│   ├── auc.py              # Cálculo de AUC (sin cambios vs escritorio)
│   ├── interpretacion.py   # Lógica clínica (sin cambios vs escritorio)
│   └── pdf_gen.py          # Generación de PDF en memoria
├── pages/
│   ├── datos.py            # Pestaña Datos y valores
│   ├── efectos.py          # Pestaña Efectos y medicación
│   └── grafico.py          # Pestaña Gráfico y AUC
├── requirements.txt
├── .env.example
└── README.md
```

---

## Notas sobre privacidad

- **No se almacena ningún resultado clínico.** Todo el procesamiento ocurre en memoria del servidor.
- El PDF se genera en memoria y se descarga directamente al navegador; no se guarda en ningún servidor.
- Supabase solo almacena emails y contraseñas de los usuarios (los médicos), no datos de pacientes.
- Para cumplir con la Ley 25.326 (Argentina), se recomienda elegir la región **South America (São Paulo)** al crear el proyecto en Supabase.
