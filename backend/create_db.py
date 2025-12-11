import MySQLdb

try:
    # Conectar ao MySQL sem selecionar banco de dados
    conn = MySQLdb.connect(
        host='localhost',
        user='root',
        passwd='Tr3vos123'
    )
    cursor = conn.cursor()
    cursor.execute("CREATE DATABASE IF NOT EXISTS reco_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
    conn.commit()
    print("✓ Banco de dados 'reco_db' criado com sucesso!")
    cursor.close()
    conn.close()
except MySQLdb.Error as err:
    print(f"✗ Erro ao criar banco de dados: {err}")
