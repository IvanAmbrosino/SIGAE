def get_noradIDs(self) -> list[dict]:
        print("testsa")
        """Consulta la base de datos y retorna los satélites cuyo get_from_api es True"""
        conn = psycopg2.connect(
            host="localhost",      # Cambia si tu contenedor tiene otro hostname
            port=5432,
            dbname="sigae",        # Cambia por el nombre real de tu base
            user="postgres",       # Cambia por tu usuario real
            password="postgres"    # Cambia por tu contraseña real
        )
        with conn.cursor() as cur:
            cur.execute("SELECT noradID, get_from_api FROM satelites WHERE get_from_api = TRUE;")
            columns = [desc[0] for desc in cur.description]
            results = [dict(zip(columns, row)) for row in cur.fetchall()]
        conn.close()
        return results