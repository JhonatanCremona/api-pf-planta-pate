## Requisitos

A continuación se detallan los requisitos necesarios para ejecutar el proyecto:

- Python 3.8 o superior
- Base de datos como **MySQL** o **PostgreSQL** (configurable)
- PLC compatible con el protocolo **OPC-UA**
- Librerías de Python:
  - **fastapi**: Framework para crear la API REST.
  - **uvicorn**: Servidor ASGI para ejecutar la app FastAPI.
  - **opcua**: Librería para conectarse y leer datos desde el PLC.
  - **sqlalchemy**: ORM para interactuar con la base de datos.

## Instalación

Sigue los siguientes pasos para instalar y ejecutar el proyecto:


2. **Crear y activar un entorno virtual**:
    ```bash
    python3 -m venv venv
    source venv/bin/activate   # En Linux/MacOS
    .\venv\Scripts\activate    # En Windows
    ```
3. **Instalar las dependencias**:
    ```bash
    pip install "fastapi[standard]"
    pip install PyMySQL
    pip install sqlalchemy
    pip install cryptography
    pip install opcua
    pip install python-jose
    pip install pandas openpyxl
    pip install passlib
    pip install bcrypt
    pip install --upgrade pip
    pip install wheel
    pip install Pillow
    ```

4. **Crear nuevo venv/Remover antiguo**:
    ```bash
    deactivate
    rm -r venv
    python -m venv venv
    Reinstalar dependencias
    ```